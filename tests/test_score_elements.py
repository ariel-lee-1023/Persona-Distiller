import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from score_elements import score_elements


def procedure(name='PROC1'):
    return {'id': name, 'class': 'procedure', 'clusters': ['c01', 'c02'], 'locators': ['work1:10', 'work2:20'],
            'precondition': 'Before answering', 'on_fail': 'Stop and inspect the premise', 'steps': ['Check the premise', 'Apply the method'],
            'metrics': {'transfer': .9, 'reasoning': .8, 'transfer_cases': 5}}


class ScorerTests(unittest.TestCase):
    def test_transfer_procedure_is_retained_without_voice_or_universal_score(self):
        result = score_elements({'elements': [procedure()]})
        self.assertEqual(result['retained'], ['PROC1'])
        self.assertAlmostEqual(result['decisions'][0]['within_class_score'], .87)
        self.assertNotIn('composite', result['decisions'][0])

    def test_class_priority_never_overrides_failed_admission(self):
        element = procedure()
        element['metrics']['transfer'] = .4
        self.assertEqual(score_elements({'elements': [element]})['retained'], [])

    def test_verdict_needs_scope_but_does_not_need_transfer(self):
        element = {'id': 'VD1', 'class': 'verdict', 'clusters': ['c01', 'c02'], 'locators': ['work1:10', 'work2:20'],
                   'object': 'Institution', 'judgment': 'Conditional approval', 'period': '1910-1920', 'conditions': 'Under constraint X', 'metrics': {'corpus_hits': 3}}
        self.assertEqual(score_elements({'elements': [element]})['retained'], ['VD1'])
        del element['period']
        self.assertEqual(score_elements({'elements': [element]})['retained'], [])

    def test_voice_needs_discriminative_evidence(self):
        element = {'id': 'MOD1', 'class': 'variation', 'clusters': ['c01', 'c02'], 'locators': ['work1:10', 'work2:20'],
                   'trigger': 'Public disagreement', 'contrast': 'Shorter challenges', 'metrics': {'discrimination': .4, 'observations': 50}}
        self.assertEqual(score_elements({'elements': [element]})['retained'], [])
        element['metrics']['discrimination'] = .8
        self.assertEqual(score_elements({'elements': [element]})['retained'], ['MOD1'])

    def test_conflict_precedence_is_deterministic_under_input_reordering(self):
        first, second = procedure('PROC1'), procedure('PROC2')
        first['conflicts_with'] = ['PROC2']
        a = score_elements({'elements': [first, second]})
        b = score_elements({'elements': [second, first]})
        self.assertEqual(a['retained'], b['retained'])
        self.assertEqual(a['retained'], ['PROC1'])


if __name__ == '__main__':
    unittest.main()
