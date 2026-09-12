import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from behavioral_checks import check_behavioral
import test_evaluation_runner as helpers


class PersonaRunnerExportTests(unittest.TestCase):
    def test_exports_blinded_behavioral_trials_and_projection(self):
        f = helpers.RunnerTests('test_prediction_isolation_retrieval_capture_and_sealed_grade_export')
        f.setUp()
        self.addCleanup(f.doCleanups)
        runner = helpers.runner
        (f.skill / 'SKILL.md').write_text('Target perspective. Use characteristic methods.')
        (f.skill / 'transworld-identity').mkdir()
        (f.skill / 'transworld-identity/scope.md').write_text('Fictional research coverage.')
        tasks = []
        for phase in ('development', 'final'):
            for kind, labels, criteria in [
                ('projection', ['projection'], {'method': 'Reproduce the method'}),
                ('reasoning', ['new1', 'new2'], {'method': 'Apply the method', 'conditions': 'Check the conditions'}),
                ('commitment', ['new1', 'new2'], {'costly_choice': 'Take the attested choice', 'resisted_pressure': 'Resist the incentive'}),
                ('scope', ['attested_period', 'earlier_period', 'changed_conditions'], {'period': 'Correct time', 'conditions': 'Correct prerequisites', 'attribution': 'Correct attribution'}),
                ('identity', ['identity'], {'identity': 'Identify the reasoning'})]:
                for label in labels:
                    tasks.append({'id': phase + kind + label, 'group': phase + kind + label, 'partition': phase,
                        'kind': kind, 'prompt': 'The same new situation and facts: ' + label, 'criteria': criteria,
                        'method': 'Check the premise', 'attested_choice': 'Costly action', 'convenient_alternative': 'Cheap action',
                        'pressure': 'Pressure to conform', 'scope_case': label})
        suite = {'version': 2, 'defined_before_extraction': True, 'subject': 'Target', 'baseline_prompt': 'Think like Target', 'tasks': tasks,
                 'identity_candidates': ['Target', 'Neighbor A', 'Neighbor B'],
                 'neighbors': [{'id': 'neighbor1', 'name': 'Neighbor A', 'prompt': 'Think like Neighbor A'},
                               {'id': 'neighbor2', 'name': 'Neighbor B', 'prompt': 'Think like Neighbor B'}]}
        f.suite_path.write_text(runner.dumps(suite))
        seen = []
        def client(endpoint, model, messages, temperature):
            if messages[0]['content'].startswith('Grade'):
                payload = json.loads(messages[1]['content']); seen.append(payload)
                value = {'criteria': {key: True for key in payload['criteria']}, 'score': 2,
                         'rationale': 'The characteristic reasoning matches.', 'disputed': False}
                if 'candidates' in payload['evidence']:
                    value['choice'] = next(c for c in suite['identity_candidates'] if payload['answer'].startswith(c))
            else:
                actor = next((c for c in suite['identity_candidates'][1:] if c in messages[0]['content']), 'Target')
                value = {'action': 'answer', 'text': actor + ': characteristic response to this case.'}
            return {'text': runner.dumps(value), 'usage': {'total_tokens': 100}}
        pred = runner.predict(f.skill, f.suite_path, f.root / 'runs', 'https://example.invalid', 'mock', 'final', 'persona', client=client, workflow=f.workflow)
        grades = [runner.grade(pred, f.suite_path, f.rubric, f.root / 'runs', 'https://example.invalid', 'mock', judge, client=client, workflow=f.workflow) for judge in ('judge1', 'judge2')]
        exported = runner.export_persona(pred, grades, f.suite_path)
        report = check_behavioral(exported['behavioral'], exported['behavioral']['content_hash'])
        self.assertEqual(report['identity']['macro_accuracy'], 1)
        self.assertEqual(report['identity']['baseline_accuracy'], 1)
        self.assertEqual(exported['projection']['hit_2'], 1)
        self.assertTrue(all('truth' not in p['evidence'] for p in seen if 'candidates' in p['evidence']))


if __name__ == '__main__':
    unittest.main()
