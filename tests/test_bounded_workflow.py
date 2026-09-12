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

    def test_default_standard_has_only_target_and_one_batched_review(self):
        pred = self.predict()
        config = json.loads((pred / 'config.json').read_text())
        self.assertEqual(config['mode'], 'standard'); self.assertEqual(config['conditions'], ['persona'])
        self.assertNotIn('unaffected topic', json.dumps(self.calls).lower())
        rubric = self.root / 'rubric.json'; rubric.write_text('{"case1":{"evidence":"PRIVATE SOURCE"}}')
        grade = runner.grade(pred, self.suite, rubric, self.root / 'runs', 'https://example.invalid', 'judge', 'reviewer', client=self.client)
        self.assertEqual(self.wf.status()['consumed'], 2)
        self.assertNotIn('PRIVATE SOURCE', json.dumps(self.calls[0]))
        self.assertTrue(runner.verify(grade))
        with self.assertRaisesRegex(ValueError, 'research fidelity'):
            runner.export_persona(pred, [grade], self.suite)

    def test_resume_reuses_completed_answers_and_ignores_unrelated_module_change(self):
        self.predict()
        (self.skill / 'references/other.md').write_text('Updated unrelated material.')
        self.wf = Workflow(self.wf.path)
        self.predict()
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.wf.status()['consumed'], 1)
        (self.skill / 'references/topic.md').write_text('The relevant condition has changed.')
        with self.assertRaisesRegex(DispatchStopped, 'repair'):
            self.predict()
        self.wf.repair(); self.predict()
        self.assertEqual(len(self.calls), 2)
        with self.assertRaises(DispatchStopped): self.wf.repair()

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
        for i in range(2):
            self.wf.reserve(str(i), 'candidate', {'prompt': str(i)}, candidate=str(i))
        with self.assertRaisesRegex(DispatchStopped, 'candidate response limit'):
            self.wf.reserve('third', 'candidate', {}, candidate='third')
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
            try: wf.reserve(str(i), 'delegated', {'item': i}); return True
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
        with self.assertRaises(DispatchStopped): self.predict()
        wf = Workflow.create(self.root / 'format.sqlite', self.skill, 'Fix formatting', ['SKILL.md'], change_type='formatting')
        with self.assertRaisesRegex(DispatchStopped, 'formatting'):
            wf.dispatch('sample', 'candidate', 'https://example.invalid', 'mock', [], 0, self.client, candidate='sample')
        self.assertEqual(wf.status()['consumed'], 0)


class CompletionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = packages.TestGeneratedProjectLayout('test_accepts_agents_skill_layout')
        self.fixture.setUp(); self.fixture.write_valid_project(); self.addCleanup(self.fixture.doCleanups)
        self.package = self.fixture.root
        self.skill = self.package / '.agents/skills/demo-perspective'
        self.wf = Workflow.create(self.package / 'fidelity-ledger/workflow.sqlite', self.skill, 'Update topic condition', ['references/clusters/c01-topic.md'])
        (self.skill / 'references/clusters/c01-topic.md').write_text('# Topic\n\nuid: c01\nUse B only after A; stop for C.\n')
        deps = {'references/clusters/c01-topic.md': file_hash(self.skill / 'references/clusters/c01-topic.md')}
        saved = self.package / 'answer.json'; saved.write_text(json.dumps({'prompt': 'When may I use B?', 'answer': 'After A, except C.', 'dependencies': deps}))
        self.review = {'summary': 'Restored condition A and exception C.', 'reviewer': 'Human source reviewer', 'usable': True,
                       'limitations': ['Independent identity evaluation has not passed.'],
                       'source_checks': [{'claim': 'B requires A', 'locator': 'Work, chapter 2, page 10', 'source_excerpt': 'A before B, except C.',
                            'condition_or_exception': 'Do not apply B when C holds.', 'assessment': 'Condition restored faithfully.', 'passed': True, 'dependencies': deps}],
                       'responses': [{'record': 'answer.json', 'record_hash': file_hash(saved), 'assessment': 'Applies the exception.',
                                      'checks': {'supported_claims': True, 'qualifications': True, 'method': True}}]}
        self.review_path = self.package / 'review.json'

    def result(self, **kwargs):
        self.review_path.write_text(json.dumps(self.review))
        return completion_report.report(self.package, self.wf, self.review_path, **kwargs)

    def test_usable_working_delivery_can_have_failed_research_gate(self):
        fidelity = self.package / 'fidelity-ledger/fidelity.json'; fidelity.write_text('{}')
        result = self.result()
        self.assertEqual(result['delivery_status'], 'usable_working_version')
        self.assertEqual(result['evaluation_status'], 'research_evaluation_incomplete')
        self.assertEqual(result['research_validation']['verdict'], 'FAIL')
        self.assertEqual(self.wf.status()['consumed'], 0)

    def test_structure_only_does_not_establish_lightweight_content_or_fidelity(self):
        self.review['source_checks'] = []; self.review['responses'] = []
        result = self.result()
        self.assertEqual(result['structure']['verdict'], 'PASS')
        self.assertEqual(result['delivery_status'], 'incomplete_draft')
        self.assertFalse(result['lightweight_checks_completed'])

    def test_stale_source_review_does_not_pass_and_unrelated_evidence_survives(self):
        other = {'id': 'voice review', 'dependencies': {'references/voice.md': file_hash(self.skill / 'references/voice.md')}}
        self.review['existing_evidence'] = [other]
        (self.skill / 'references/clusters/c01-topic.md').write_text('# Topic\nuid: c01\nChanged again.')
        result = self.result()
        self.assertEqual(result['delivery_status'], 'incomplete_draft')
        self.assertTrue(result['existing_evidence'][0]['current'])
        self.assertFalse(result['source_checks'][0]['current_and_complete'])

    def test_formatting_completion_needs_no_new_model_answers(self):
        wf = Workflow.create(self.package / 'format.sqlite', self.skill, 'Reformat', ['SKILL.md'], change_type='formatting')
        (self.skill / 'SKILL.md').write_text((self.skill / 'SKILL.md').read_text() + '\n')
        self.review.update(source_checks=[], responses=[], formatting_only_rationale='Only trailing whitespace changed; runtime content retained.')
        self.wf = wf
        result = self.result()
        self.assertEqual(result['delivery_status'], 'usable_working_version')
        self.assertEqual(result['evaluation_status'], 'lightweight_checks_completed')


if __name__ == '__main__':
    unittest.main()
