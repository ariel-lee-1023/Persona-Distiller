import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from workflow import Workflow, DispatchStopped, runtime_files, file_hash
import evaluation_runner as runner
import completion_report
import test_validate_package as packages


class BoundedWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.skill = self.root / 'skill'
        (self.skill / 'references').mkdir(parents=True)
        (self.skill / 'SKILL.md').write_text('Apply the ordered method with its original condition.')
        (self.skill / 'references/topic.md').write_text('Method: check A before B. Exception: C.')
        (self.skill / 'references/other.md').write_text('An unaffected topic.')
        self.wf = Workflow.create(self.root / 'workflow.sqlite', self.skill, 'Improve one topic',
                                  ['references/topic.md'])
        self.suite = self.root / 'suite.json'
        self.suite.write_text(json.dumps({'tasks': [{'id': 'case1', 'prompt': 'Apply the method to a new case.',
            'references': ['references/topic.md'], 'criteria': {'method': 'Use method', 'condition': 'Respect condition'}}]}))
        self.calls = []

    def client(self, endpoint, model, messages, temperature):
        self.calls.append(copy.deepcopy(messages))
        if messages[0]['content'].startswith('Review these'):
            value = {'items': [{'id': row['id'], 'criteria': {key: True for key in row['criteria']},
                     'score': 2, 'rationale': 'Method and condition preserved.', 'disputed': False}
                    for row in json.loads(messages[1]['content'])]}
        else:
            value = {'action': 'answer', 'text': 'Check A before B; exception C prevents application.'}
        return {'text': json.dumps(value), 'usage': {'total_tokens': 40}}

    def predict(self):
        return runner.predict(self.skill, self.suite, self.root / 'runs', 'https://example.invalid',
                              'mock', workflow=self.wf, client=self.client)

    def test_legacy_research_runner_cannot_substitute_for_standard_recognition(self):
        with self.assertRaisesRegex(ValueError, 'recognition_runner'):
            self.predict()
        self.assertEqual(self.wf.status()['consumed'], 0)

    def test_exact_request_reuse_survives_restart(self):
        call, _ = self.wf.reserve('case1', 'candidate', {'prompt': 'fixed'}, candidate='case1')
        self.wf.finish(call, response={'text': 'saved'})
        _, saved = Workflow(self.wf.path).reserve('case1', 'candidate', {'prompt': 'fixed'}, candidate='case1')
        self.assertEqual(saved, {'text': 'saved'})
        self.assertEqual(self.wf.status()['consumed'], 1)

    def test_global_budget_stops_before_dispatch_and_persists_across_resume(self):
        for i in range(8):
            self.wf.dispatch(str(i), 'candidate', 'https://example.invalid', 'mock', [], 0,
                             lambda *a: {'text': str(i)}, candidate='one-response')
        wf = Workflow(self.wf.path)
        with self.assertRaisesRegex(DispatchStopped, 'exhausted'):
            wf.dispatch('ninth', 'grader', 'https://example.invalid', 'mock', [], 0, self.client)
        self.assertEqual(wf.status()['remaining'], 0); self.assertFalse(self.calls)
        with self.assertRaises(FileExistsError):
            Workflow.create(wf.path, self.skill, 'reset', ['SKILL.md'])
        wf.authorize_more(1, 'User explicitly authorized one additional review')
        wf.dispatch('ninth', 'grader', 'https://example.invalid', 'mock', [], 0, lambda *a: {'text': 'review'})
        self.assertEqual(wf.status()['consumed'], 9)

    def test_partial_answers_survive_exhaustion_and_research_resumes_exact_experiment(self):
        (self.skill / 'transworld-identity').mkdir()
        (self.skill / 'transworld-identity/scope.md').write_text('Fictional research coverage.')
        self.wf = Workflow.create(self.root / 'research.sqlite', self.skill, 'Explicit final test', ['SKILL.md'],
                                  mode='research', budget=1, authorization='One final prediction call initially')
        suite = {'version': 2, 'defined_before_extraction': True, 'baseline_prompt': 'Target role',
                 'tasks': [{'id': 'final1', 'partition': 'final', 'group': 'final-work', 'kind': 'projection',
                            'prompt': 'New case', 'criteria': {'method': 'Use the method'}}]}
        self.suite.write_text(json.dumps(suite))
        def predict():
            return runner.predict(self.skill, self.suite, self.root / 'runs', 'https://example.invalid', 'mock',
                                  phase='final', workflow=self.wf, client=self.client)
        with self.assertRaises(DispatchStopped): predict()
        partial = next((self.root / 'runs').glob('predict-*'))
        self.assertTrue(runner.verify(partial))
        self.assertEqual(len(json.loads((partial / 'predictions.json').read_text())), 1)
        self.wf = Workflow(self.wf.path)
        self.wf.authorize_more(1, 'User authorized the one remaining candidate call')
        completed = predict()
        self.assertEqual(len(json.loads((completed / 'predictions.json').read_text())), 2)
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(self.wf.status()['consumed'], 2)

    def test_checkpoints_keep_runtime_bytes_and_unfinished_items(self):
        original = (self.skill / 'references/topic.md').read_bytes()
        self.wf.checkpoint(['one targeted review'], {'ocr_pages': 2})
        old_hash = file_hash(self.skill / 'references/topic.md')
        (self.skill / 'references/topic.md').write_text('Later edit')
        with self.wf.transaction() as db:
            self.assertEqual(db.execute('SELECT content FROM runtime_blobs WHERE hash=?', (old_hash,)).fetchone()[0], original)
        checkpoint = self.wf.status()['events'][-1]['value']
        self.assertEqual(checkpoint['remaining_items'], ['one targeted review'])
        self.assertEqual(checkpoint['remaining_calls'], 8)

    def test_candidate_caps_and_no_default_comparisons(self):
        for i in range(3):
            self.wf.reserve(str(i), 'candidate', {'prompt': str(i)}, candidate=str(i))
        with self.assertRaisesRegex(DispatchStopped, 'candidate response limit'):
            self.wf.reserve('fourth', 'candidate', {}, candidate='fourth')
        for role in ('baseline', 'neighbor'):
            with self.assertRaises(DispatchStopped): self.wf.reserve(role, role, {})

    def test_interrupted_and_failed_calls_remain_charged_without_automatic_retry(self):
        self.wf.reserve('interrupted', 'candidate', {'prompt': 'p'}, candidate='a')
        with self.assertRaises(DispatchStopped):
            Workflow(self.wf.path).reserve('interrupted', 'candidate', {'prompt': 'p'}, candidate='a')
        call, _ = self.wf.reserve('interrupted', 'candidate', {'prompt': 'p'}, candidate='a', retry=True)
        self.wf.finish(call, error='TimeoutError')
        self.assertEqual(self.wf.status()['consumed'], 2)
        self.assertEqual([r['state'] for r in self.wf.status()['calls']], ['reserved', 'failed'])

    def test_concurrent_reservations_cannot_exceed_budget(self):
        wf = Workflow.create(self.root / 'one.sqlite', self.skill, 'One call', ['SKILL.md'], budget=1)
        def reserve(i):
            try: wf.reserve(str(i), 'candidate', {'item': i}, candidate=str(i)); return True
            except DispatchStopped: return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sum(pool.map(reserve, [1, 2])), 1)
        self.assertEqual(wf.status()['consumed'], 1)

    def test_research_requires_authorization_and_fixed_budget(self):
        for kwargs in ({}, {'budget': 30}, {'authorization': 'Explicit comprehensive evaluation'}):
            with self.assertRaisesRegex(ValueError, 'authorization'):
                Workflow.create(self.root / 'research.sqlite', self.skill, 'research', ['SKILL.md'], mode='research', **kwargs)
        wf = Workflow.create(self.root / 'research.sqlite', self.skill, 'research', ['SKILL.md'], mode='research',
                             budget=30, authorization='Explicit comprehensive evaluation')
        self.assertEqual(wf.status()['budget'], 30)

    def test_stop_and_formatting_do_not_dispatch(self):
        self.wf.stop()
        with self.assertRaises(DispatchStopped): self.wf.reserve('stopped', 'judge', {})
        wf = Workflow.create(self.root / 'format.sqlite', self.skill, 'Fix formatting', ['SKILL.md'], change_type='formatting')
        with self.assertRaisesRegex(DispatchStopped, 'formatting'):
            wf.dispatch('sample', 'candidate', 'https://example.invalid', 'mock', [], 0, self.client, candidate='sample')
        self.assertEqual(wf.status()['consumed'], 0)


if __name__ == '__main__':
    unittest.main()
