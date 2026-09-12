import copy
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from workflow import Workflow, digest, file_hash, DispatchStopped
from recognition import DIMENSIONS, assess
import recognition_runner as rr
from completion_report import report, validate_package


def plan_fixture():
    evidence = {'id': 'E1', 'source': 'Fictional public hearing', 'locator': 'hearing:turns-12-18',
                'attribution': 'subject', 'group_id': 'hearing-event', 'situation': 'Unexamined report',
                'audience': 'colleagues', 'available_information': 'No underlying observations yet',
                'constraints': 'Pressure for endorsement', 'observation': 'Inspect observations before endorsing; revise after evidence.',
                'claim_type': 'observed_event', 'conditions': ['Evidence not inspected'], 'exceptions': ['Persuasive evidence supplied'],
                'conflicts': [], 'runtime_support': ['SKILL.md#method'], 'curation': {'decision': 'contextualize', 'reason': 'Refusal depends on available evidence.'}}
    patterns = []
    for name in ('Inspect before endorsing', 'Revise with observations', 'Challenge the premise respectfully'):
        patterns.append({'pattern': name, 'evidence_ids': ['E1'], 'circumstances': 'Pressure with changing evidence',
                         'observable_behavior': name, 'acceptable_variation': 'Accept once verified', 'mismatch': 'Always refuse regardless of evidence',
                         'diagnostic_reason': 'Concrete order of examination under pressure, beyond generic honesty.',
                         'scoring_anchors': {str(i): 'Specific example at level ' + str(i) for i in range(5)}})
    return {'structure_revision': 2, 'contract': {'subject': 'Fictional examiner', 'intended_use': 'Assess reports', 'period_domains': 'Public hearings',
                         'supplied_sources': ['hearing'], 'output_location': 'persona/', 'delivery_target': 'local draft',
                         'source_boundary': {'priority_materials': 'hearing turns 12-18', 'reading_units': 1, 'ocr_pages': 0}},
            'cases': [{'id': str(i), 'kind': kind, 'task': task, 'fixed_background': 'The examiner has no memory beyond the documented hearing.',
                       'stipulated_changes': change, 'references': ['references/topic.md'] if i < 2 else ['references/voice.md']}
                      for i, (kind, task, change) in enumerate([
                          ('characteristic', 'Should the report be endorsed?', 'Only conclusions are available'),
                          ('changed_condition', 'Should the report now be endorsed?', 'Independent observations now verify its conclusions'),
                          ('interpersonal', 'A colleague demands agreement. Respond.', 'Colleague is under deadline pressure')])],
            'evidence': [evidence], 'profile': patterns, 'identity_labels': ['Fictional Examiner'],
            'generation': {'endpoint': 'https://example.invalid/chat/completions', 'model': 'mock', 'judge_models': ['mock-judge', 'mock-judge'],
                           'temperature': 0, 'answer_max_tokens': 700, 'judge_max_tokens': 8192, 'input_token_limit': 64000,
                           'timeout_seconds': 10, 'deadline': time.time() + 600, 'max_words': 250}}


def judge_fixture(shown, index, scores=None, wins=3):
    rows = []
    for i, case in enumerate(shown):
        row = {'id': case['id'], 'preference': ('A' if index == 0 else 'B') if i < wins else 'tie',
               'reason': 'Orders examination before judgment, adapting when observations arrive.', 'evidence_ids': ['E1']}
        for slot in ('A', 'B'):
            row[slot] = {dim: {'score': (scores or [4, 3, 3, 3, 3])[j], 'passage': case['answers'][slot], 'evidence_ids': ['E1'],
                               'reason': 'Applies the documented pattern to changed facts.', 'pair_reason': 'First inspects, then accepts when observations verify the claim.'}
                         for j, dim in enumerate(DIMENSIONS)}
        rows.append(row)
    return {'material_issues': [], 'cases': rows}


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.cases = [{'id': str(i), 'answers': {'A': 'Examine first; accept once verified.', 'B': 'Offer a helpful analysis.'}} for i in range(3)]
        self.judges = [judge_fixture(self.cases, 0), judge_fixture([
            {**c, 'answers': {'A': c['answers']['B'], 'B': c['answers']['A']}} for c in self.cases], 1)]

    def result(self):
        return assess(self.judges, self.cases, {'E1'})

    def test_exact_eighty_threshold_and_evidence_sensitive_adaptation_pass(self):
        result = self.result()
        self.assertEqual(result['outcome'], 'passed')
        self.assertEqual([j['recognition_score'] for j in result['judges']], [80, 80])

    def test_generic_fluent_answers_fail_specificity_even_with_high_other_scores(self):
        for i, j in enumerate(self.judges):
            for c in j['cases']:
                slot = c['A' if i == 0 else 'B']
                for d in DIMENSIONS: slot[d]['score'] = 4
                slot['specificity']['score'] = 1
        self.assertEqual(self.result()['outcome'], 'failed')

    def test_each_dimension_floor_and_each_case_floor(self):
        for dim in DIMENSIONS:
            with self.subTest(dim=dim):
                judges = copy.deepcopy(self.judges)
                for i, j in enumerate(judges):
                    for row in j['cases']:
                        for d in DIMENSIONS: row['A' if i == 0 else 'B'][d]['score'] = 4
                    j['cases'][0]['A' if i == 0 else 'B'][dim]['score'] = 1 if dim == 'interaction' else 2
                self.assertEqual(assess(judges, self.cases, {'E1'})['outcome'], 'failed')
        for i, j in enumerate(self.judges):
            for row in j['cases']:
                for d in DIMENSIONS: row['A' if i == 0 else 'B'][d]['score'] = 4
            for d in DIMENSIONS: j['cases'][0]['A' if i == 0 else 'B'][d]['score'] = 3
            j['cases'][0]['A' if i == 0 else 'B']['interaction']['score'] = 2
        self.assertEqual(self.result()['outcome'], 'failed')

    def test_ties_do_not_count_and_judge_disagreement_is_inconclusive(self):
        for row in self.judges[0]['cases'][1:]: row['preference'] = 'tie'
        self.assertEqual(self.result()['outcome'], 'inconclusive')
        for row in self.judges[1]['cases'][1:]: row['preference'] = 'tie'
        self.assertEqual(self.result()['outcome'], 'failed')

    def test_missing_dimensions_unassessed_and_malformed_values_do_not_pass(self):
        record = self.judges[0]['cases'][0]['A']['reasoning']
        for value in (True, 4.1, None, -1, 5):
            record['score'] = value
            with self.assertRaises(ValueError): self.result()
        record['score'] = 'unassessed'
        self.assertEqual(self.result()['outcome'], 'inconclusive')
        del self.judges[0]['cases'][0]['A']['reasoning']
        with self.assertRaises(ValueError): self.result()

    def test_fabricated_citation_or_answer_passage_rejected(self):
        self.judges[0]['cases'][0]['A']['reasoning']['evidence_ids'] = ['missing']
        with self.assertRaises(ValueError): self.result()
        self.judges[0]['cases'][0]['A']['reasoning']['evidence_ids'] = ['E1']
        self.judges[0]['cases'][0]['A']['reasoning']['passage'] = 'invented'
        with self.assertRaises(ValueError): self.result()

    def test_verified_defect_and_judge_reported_material_issue(self):
        self.assertEqual(assess([], self.cases, {'E1'}, True)['outcome'], 'failed')
        self.judges[0]['material_issues'] = ['Unresolved contradiction of fixed history']
        self.assertEqual(self.result()['outcome'], 'inconclusive')


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'persona'; self.root.mkdir()
        (self.root / 'references').mkdir()
        (self.root / 'SKILL.md').write_text('---\nname: fictional-perspective\ndescription: Assess reports using a documented perspective.\n---\n# Method\nInspect observations before endorsing.\nPreserve historical facts; do not fabricate historical quotations. Read references/frameworks.md. Use references/topic.md for reports and references/voice.md for conversation.\n')
        for name, text in [('frameworks', 'Examine observations, then revise.'), ('topic', 'Examine the premise before judgment.'),
                           ('voice', 'Challenge the premise respectfully.')]:
            (self.root / 'references' / (name + '.md')).write_text(text)
        (self.root / '.agents/skills').mkdir(parents=True)
        (self.root / '.agents/skills/fictional-perspective').symlink_to('../..')
        (self.root / 'transworld-identity').mkdir()
        (self.root / 'transworld-identity/scope.md').write_text('Fictional hearing coverage. No journals supplied. Contemporary applications extrapolate the observed methods.')
        (self.root / 'transworld-identity/provenance.md').write_text('# Build contract\n\nFictional test record, not a real persona assessment.\n')
        self.wf = Workflow.create(Path(self.tmp.name) / 'workflow.sqlite', self.root, 'Build fixture', ['SKILL.md'], operation='new')
        self.plan = plan_fixture()
        self.run = self.root / 'transworld-identity/runs/first'
        self.calls = []
        self.frozen = rr.freeze(self.root, self.plan, self.run, self.wf.path)

    def client(self, request, timeout):
        self.calls.append(copy.deepcopy(request))
        if request['model'] == 'mock':
            facts = json.loads(request['messages'][1]['content'])
            text = ('Accept, because the observations now verify it.' if 'now verify' in facts['stipulated_changes'] else
                    'Examine the observations before endorsing; ask the colleague for the underlying evidence.')
            if 'Runtime perspective:' not in request['messages'][0]['content']:
                text = 'Review the report for accuracy, request supporting information as needed, and communicate the decision clearly.'
        else:
            packet = json.loads(request['messages'][1]['content'])
            index = sum(r['model'] != 'mock' for r in self.calls) - 1
            # Imported or resumed judge calls keep their reverse-order position by inspecting the persisted reservation.
            state = self.wf.status()
            last = state['calls'][-1]['item']
            index = 0 if last.endswith('judge-1') else 1
            text = json.dumps(judge_fixture(packet['cases'], index))
        return {'text': text, 'usage': {'total_tokens': 40}, 'model': request['model']}

    def execute(self, **kwargs):
        return rr.execute(self.run, self.wf.path, client=self.client, **kwargs)

    def review(self):
        content = rr.runtime_snapshot(self.root)
        return {'summary': 'Source and condition checked', 'reviewer': 'Machine-assisted editorial review',
                'reviewed_all_core_claims': True, 'limitations': [],
                'source_checks': [{'claim': 'Inspect before endorsing', 'outcome': 'passed', 'assessment': 'Matches the observed order.',
                                   'condition_or_exception': 'Accept after verification', 'evidence_ids': ['E1'],
                                   'dependencies': {p: digest(t) for p, t in content.items()}}]}

    def completion(self):
        review_path = Path(self.tmp.name) / 'review.json'; review_path.write_text(json.dumps(self.review()))
        return report(self.root, self.wf, review_path, self.run)

    def test_full_first_adoption_eight_calls_blinding_caps_and_resume(self):
        result = self.execute()
        self.assertEqual(result['recognition']['outcome'], 'passed', result)
        self.assertEqual(len(self.calls), 8)
        self.assertEqual(self.wf.status()['consumed'], 8)
        for request in self.calls[:6]:
            self.assertNotIn('scoring_anchors', json.dumps(request))
            self.assertNotIn('source_packet', json.dumps(request))
            self.assertEqual(request['max_tokens'], 700)
        for i in (1, 3, 5):
            self.assertNotIn('Runtime perspective:', self.calls[i]['messages'][0]['content'])
            self.assertEqual(self.calls[i]['messages'][1], self.calls[i-1]['messages'][1])
        first = json.loads(self.calls[6]['messages'][1]['content'])
        second = json.loads(self.calls[7]['messages'][1]['content'])
        self.assertEqual(first['cases'][0]['answers']['A'], second['cases'][0]['answers']['B'])
        self.assertTrue(all(c['answers']['A'] != c['answers']['B'] for c in first['cases']))
        self.execute(); self.assertEqual(len(self.calls), 8)
        completion = self.completion()
        self.assertEqual(completion['delivery_status'], 'standard_accepted', completion)
        self.assertEqual(len(self.calls), 8)
        self.assertNotIn(str(self.root), json.dumps(completion))

    def assert_readme_edit_preserves_assessment(self, expected_status):
        readme = self.root / 'README.md'
        readme.write_text('# Examiner\nAdministrative capability inventory.\n')
        before = self.completion()
        calls_before = copy.deepcopy(self.calls)
        consumed_before = self.wf.status()['consumed']
        readme.write_text(
            '# Examiner\nBring a report whose conclusions you have been asked to endorse.\n'
            'Suggested prompt: Which observations would justify signing this?\n'
            '**Status: ' + expected_status + '.** See '
            '[scope](transworld-identity/scope.md).\n')
        after = self.completion()
        for key in ('runtime_hash', 'module_hashes', 'hashes', 'gates',
                    'recognition', 'assessment_records', 'budget'):
            self.assertEqual(after[key], before[key], key)
        self.assertEqual(before['delivery_status'], expected_status)
        self.assertEqual(after['delivery_status'], expected_status)
        self.assertEqual(self.wf.status()['consumed'], consumed_before)
        self.assertEqual(self.calls, calls_before)
        self.assertIn('Bring a report', readme.read_text())

    def test_readme_only_edit_keeps_candidate_without_recognition_calls(self):
        self.assert_readme_edit_preserves_assessment('candidate')
        self.assertEqual(self.calls, [])

    def test_readme_only_edit_preserves_accepted_inputs_and_saved_results(self):
        self.execute()
        self.assert_readme_edit_preserves_assessment('standard_accepted')
        self.execute()
        self.assertEqual(len(self.calls), 8)

    def test_partial_resume_consumes_only_missing_calls(self):
        original = self.client
        count = 0
        def interrupt(request, timeout):
            nonlocal count
            count += 1
            if count == 4: raise KeyboardInterrupt()
            return original(request, timeout)
        with self.assertRaises(KeyboardInterrupt): rr.execute(self.run, self.wf.path, client=interrupt)
        self.assertEqual(self.wf.status()['consumed'], 4)
        self.assertTrue((self.run / '1-persona.json').exists())
        # Interrupted reservation stays charged; a retry fits only part of the remaining protocol.
        result = self.execute(retry=True)
        self.assertEqual(self.wf.status()['consumed'], 8)
        self.assertEqual(result['recognition']['outcome'], 'inconclusive')
        self.assertEqual(len([r for r in self.calls if r['model'] == 'mock']), 6)

    def test_lost_mirror_is_recovered_from_persistent_success_without_dispatch(self):
        self.execute()
        (self.run / '0-persona.json').unlink()
        self.execute()
        self.assertEqual(len(self.calls), 8)
        self.assertTrue((self.run / '0-persona.json').exists())

    def test_profile_change_reuses_answers_but_not_judges_with_new_scoped_budget(self):
        self.execute()
        prior = self.wf
        self.wf = Workflow.create(Path(self.tmp.name) / 'later.sqlite', self.root, 'Later profile correction', ['SKILL.md'])
        self.wf.import_calls(prior.path)
        self.plan['profile'][0]['mismatch'] = 'Approves before observations are inspected'
        self.run = self.root / 'transworld-identity/runs/later'
        rr.freeze(self.root, self.plan, self.run, self.wf.path)
        result = self.execute()
        self.assertEqual(self.wf.status()['consumed'], 2)
        self.assertEqual(len(self.calls), 10)
        self.assertEqual(result['recognition']['outcome'], 'passed')

    def test_runtime_change_invalidates_only_affected_answers(self):
        self.execute()
        prior = self.wf
        (self.root / 'references/topic.md').write_text('Inspect raw observations and compare alternatives.')
        self.wf = Workflow.create(Path(self.tmp.name) / 'later.sqlite', self.root, 'Later topic correction', ['references/topic.md'])
        self.wf.import_calls(prior.path)
        self.run = self.root / 'transworld-identity/runs/later'
        rr.freeze(self.root, self.plan, self.run, self.wf.path)
        self.execute()
        # Two topic answers changed; three controls and the interpersonal answer are reused.
        # If the deterministic mock returns identical text, prior judge inputs are identical and reusable.
        self.assertEqual(self.wf.status()['consumed'], 2)
        self.assertEqual(len(self.calls), 10)

    def test_changed_runtime_cannot_borrow_a_current_pass(self):
        self.execute()
        (self.root / 'references/topic.md').write_text('Always refuse reports.')
        self.assertEqual(self.completion()['delivery_status'], 'candidate')
        self.assertEqual(len(self.calls), 8)

    def test_exhausted_repair_does_not_grant_more_calls(self):
        self.execute(); self.wf.repair()
        (self.root / 'SKILL.md').write_text((self.root / 'SKILL.md').read_text() + '\nNew condition.\n')
        self.run = self.root / 'transworld-identity/runs/repair'
        rr.freeze(self.root, self.plan, self.run, self.wf.path)
        result = self.execute()
        self.assertEqual(self.wf.status()['consumed'], 8)
        self.assertEqual(result['recognition']['outcome'], 'inconclusive')
        with self.assertRaises(DispatchStopped): self.wf.repair()

    def test_expired_deadline_and_input_cap_prevent_new_dispatch(self):
        with self.wf.transaction() as db:
            db.execute("UPDATE config SET value='1' WHERE key='deadline'")
        result = self.execute()
        self.assertEqual(self.wf.status()['consumed'], 0)
        self.assertEqual(result['recognition']['outcome'], 'inconclusive')
        self.assertFalse(self.calls)

    def test_hidden_assessment_cannot_enter_runtime_via_text_or_symlink(self):
        path = self.root / 'references/leak.md'
        path.write_text('Read ../transworld-identity/recognition-profile.md')
        with self.assertRaisesRegex(ValueError, 'hidden'): rr.runtime_snapshot(self.root)
        self.assertEqual(validate_package(self.root)['verdict'], 'FAIL')
        path.unlink(); path.symlink_to('../transworld-identity/recognition-profile.md')
        with self.assertRaises(ValueError): rr.runtime_snapshot(self.root)
        self.assertEqual(validate_package(self.root)['verdict'], 'FAIL')

    def test_tampered_frozen_inputs_or_saved_answers_cannot_pass(self):
        self.execute()
        path = self.run / '0-persona.json'; record = json.loads(path.read_text()); record['response']['text'] = 'Tampered answer.'
        path.write_text(json.dumps(record))
        self.assertEqual(self.execute()['recognition']['outcome'], 'inconclusive')
        frozen = self.run / 'frozen.json'; frozen.write_text(frozen.read_text() + ' ')
        with self.assertRaisesRegex(ValueError, 'frozen'): self.execute()

    def test_structure_and_no_evaluation_remains_candidate_without_human_requirement(self):
        result = self.completion()
        self.assertEqual(result['gates']['package'], 'passed', result)
        self.assertEqual(result['gates']['source'], 'passed', result)
        self.assertEqual(result['delivery_status'], 'candidate')
        self.assertEqual(self.wf.status()['consumed'], 0)


if __name__ == '__main__':
    unittest.main()
