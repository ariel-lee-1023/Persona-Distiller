"""Regression coverage for independent splits, family labels and executable gates."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import builtins

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from holdout_split import split_items
from discrimination_test import family_mapping
from release_checks import file_hash, runtime_hash, release_checks

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'


def valid_behavior(content_hash):
    data = {'content_hash': content_hash}
    for kind, keys in [('reasoning', ('method', 'conditions')), ('commitment', ('costly_choice', 'resisted_pressure')), ('scope', ('period', 'conditions', 'attribution'))]:
        labels = ['attested_period', 'earlier_period', 'changed_conditions'] if kind == 'scope' else ['new1', 'new2']
        data[kind] = [{'id': kind + label, 'prompt': 'New situation ' + label, 'answer': 'Recorded characteristic response.',
                       'criteria': {k: True for k in keys}, 'rationale': 'Supported by source and conditions.', 'disputed': False,
                       'scope_case': label, 'method': 'Check assumptions then apply rule', 'attested_choice': 'Costly choice',
                       'convenient_alternative': 'Easy choice', 'pressure': 'Incentive to conform'} for label in labels]
    candidates = ['Target', 'Neighbor A', 'Neighbor B']
    data['identity'] = {'candidates': candidates, 'cases': [
        {'id': 'shared-task', 'prompt': 'The same task and facts.', 'answer': 'Characteristic answer for ' + actor, 'truth': actor,
         'judgments': [{'reviewer': judge, 'choice': actor, 'blinded': True, 'disputed': False, 'rationale': 'Distinctive reasoning.'} for judge in ('judge1', 'judge2')]}
        for actor in candidates]}
    return data


class SplitTests(unittest.TestCase):
    def test_related_passages_never_cross_partitions_and_order_is_stable(self):
        items = [{'id': f'p{i}', 'group': f'work{i // 3}', 'domain': 'ethics'} for i in range(30)]
        result = split_items(items, stratify=True)
        self.assertEqual(result, split_items(list(reversed(items)), stratify=True))
        for group in result['group_assignments']:
            parts = {part for part, ids in result['partitions'].items() for pid in ids if result['passage_groups'][pid] == group}
            self.assertEqual(len(parts), 1)
        self.assertEqual(sum(map(len, result['partitions'].values())), 30)

    def test_rejects_ungrouped_duplicate_and_impossible_splits(self):
        cases = [[{'id': 'p'}], [{'id': 'p', 'group': 'a'}] * 3]
        for items in cases:
            with self.assertRaises(ValueError):
                split_items(items)
        with self.assertRaises(ValueError):
            split_items([{'id': str(i), 'group': str(i)} for i in range(4)], frac=.8, dev_frac=.3)


class FamilyTests(unittest.TestCase):
    def mapping(self):
        return {'units': [{'unit_id': 'u1', 'clusters': ['c01', 'c02']}, {'unit_id': 'u2', 'clusters': ['c03']}],
                'families': [{'family_id': 'R1', 'members': ['u1']}, {'family_id': 'R2', 'members': ['u2']}]}

    def test_two_works_in_one_family_are_not_distinct_answers(self):
        registers = self.mapping()
        self.assertEqual(family_mapping(registers)['c01'], family_mapping(registers)['c02'])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clusters = root / 'clusters'
            clusters.mkdir()
            for cid in ('c01', 'c02', 'c03'):
                (clusters / (cid + '.txt')).write_text('Some useful source words. ' * 100)
            reg = root / 'registers.json'
            reg.write_text(json.dumps(registers))
            key = root / 'key.json'
            sample = subprocess.run([sys.executable, str(SCRIPTS / 'discrimination_test.py'), 'sample', str(clusters), '--registers', str(reg), '--key', str(key), '--mask-names'], capture_output=True, text=True)
            self.assertEqual(sample.returncode, 0, sample.stderr)
            data = json.loads(key.read_text())
            self.assertEqual(set(data['labels'].values()), {'R1', 'R2'})
            answers = root / 'answers.json'
            answers.write_text(json.dumps(data['labels']))
            score = subprocess.run([sys.executable, str(SCRIPTS / 'discrimination_test.py'), 'score', str(key), '--answers-file', str(answers), '--json', str(root / 'score.json')], capture_output=True, text=True)
            self.assertEqual(score.returncode, 0, score.stderr)
            self.assertEqual(json.loads((root / 'score.json').read_text())['score'], 1)

    def test_rejects_ambiguous_cluster(self):
        registers = self.mapping()
        registers['units'][1]['clusters'].append('c01')
        with self.assertRaisesRegex(ValueError, 'mixed-family'):
            family_mapping(registers)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.skill = self.root / 'skill'
        refs = self.skill / 'references'
        refs.mkdir(parents=True)
        (self.skill / 'SKILL.md').write_text('Load references/scope.md before answering.')
        (refs / 'scope.md').write_text('Supported domains: ethics. Period: 1910 to 1920. Standing judgments depend on original conditions. Mark changed circumstances as extrapolation.')
        self.digest = runtime_hash(self.skill)
        self.split = split_items([{'id': 'p' + str(i), 'group': 'g' + str(i)} for i in range(10)])
        (self.root / 'split.json').write_text(json.dumps(self.split))
        self.registers = {
            'verdict': 'SINGLE_REGISTER', 'n_registers': 1, 'n_units': 2,
            'thresholds': {'ratio': 3, 'dims': 3},
            'stability': {'adequate': True, 'stable': True, 'subsamples': 3, 'tokens_per_subsample': 200,
                          'minimum_agreement': .8, 'family_agreement': 1, 'pairs': [{'indices': [0, 1], 'split': False, 'agreement': 1}]},
            'units': [{'unit_id': 'u1', 'features': {'sentence_length': 10}, 'family': 'R1'},
                      {'unit_id': 'u2', 'features': {'sentence_length': 11}, 'family': 'R1'}],
            'families': [{'family_id': 'R1', 'members': ['u1', 'u2']}],
            'distance_matrix': {'units': ['u1', 'u2'], 'z_distance': [[0, .1], [.1, 0]],
                                'ratio_exceedances': [[0, 0], [0, 0]]}}
        (self.root / 'registers.json').write_text(json.dumps(self.registers))
        def result(part):
            return {'content_hash': self.digest, 'overall': 1, 'baseline': .5, 'hit_2': 1, 'hit_1': 0,
                    'passed': True, 'fresh_context': True, 'model': 'test-model', 'settings': 'temperature 0', 'baseline_prompt': 'Think like Demo.',
                    'items': [{'id': pid, 'prompt': 'What follows?', 'answer': 'Characteristic reasoning.', 'baseline_answer': 'Generic direction.', 'rationale': 'Matches the mechanism.', 'score': 2, 'baseline_score': 1} for pid in self.split['partitions'][part]]}
        self.f = {'content_hash': self.digest, 'split_hash': file_hash(self.root / 'split.json'), 'registers_hash': file_hash(self.root / 'registers.json'),
                  'stale': [], 'isolation': {'split_before_extraction': True, 'test_exposures': 1, 'construction_partitions': ['train']},
                  'register_families': ['R1'], 'projection': {'gate': result('development'), 'final': result('test')},
                  'cost': {'content_hash': self.digest, 'total_divergences': 1, 'slated_for_core': 1, 'in_core_final': 1, 'logged_out': 0, 'missing_unlogged': 0, 'presence_assertion': 'pass'},
                  'style': {'content_hash': self.digest, 'modulation_reproduced': True, 'avoid_list_violations': 0},
                  'behavioral': valid_behavior(self.digest)}

    def check(self, data=None):
        path = self.root / 'fidelity.json'
        path.write_text(json.dumps(self.f if data is None else data))
        return release_checks(self.skill, path)

    def test_passes_complete_evidence_and_fails_changed_runtime(self):
        self.assertTrue(all(c['ok'] for c in self.check()))
        (self.skill / 'references' / 'new-module.md').write_text('New judgments.')
        self.assertTrue(any(not c['ok'] and c['check'] == 'R1' for c in self.check()))

    def test_each_missing_or_failed_gate_blocks_release(self):
        mutations = [lambda f: f.pop('projection'), lambda f: f['cost'].update(missing_unlogged=1),
                     lambda f: f['projection']['final'].update(overall=.4),
                     lambda f: f['projection']['gate'].update(content_hash='stale'),
                     lambda f: f['isolation'].update(test_exposures=2),
                     lambda f: f['style'].update(avoid_list_violations=1),
                     lambda f: f['projection']['final']['items'][0].update(id='train-item'),
                     lambda f: f.update(stale=['cost'])]
        for mutate in mutations:
            f = copy.deepcopy(self.f)
            mutate(f)
            self.assertTrue(any(not c['ok'] for c in self.check(f)), f)

    def test_stale_style_requires_explicit_note_but_never_excuses_stale_cost(self):
        self.f['stale'] = ['style']
        self.f['style']['content_hash'] = 'sha256:' + '0' * 64
        self.assertTrue(any(not c['ok'] for c in self.check()))
        self.f['style_staleness_note'] = 'Core changed; previous style results are not current.'
        self.assertTrue(all(c['ok'] for c in self.check()))
        self.f['stale'].append('cost')
        self.assertTrue(any(not c['ok'] for c in self.check()))

    def test_single_family_merge_requires_matrix_review(self):
        self.f['merge_triggered'] = True
        self.assertTrue(any(not c['ok'] for c in self.check()))
        self.f['merge_review'] = 'Recomputed distance matrix still supports one family.'
        self.assertTrue(all(c['ok'] for c in self.check()))

    def check_registers(self, data):
        path = self.root / 'registers.json'
        path.write_text(json.dumps(data))
        # A matching hash must not make malformed evidence valid.
        self.f['registers_hash'] = file_hash(path)
        return self.check()

    def test_declared_register_schema_is_required(self):
        cases = [
            ('no units', lambda r: r.pop('units')),
            ('no membership', lambda r: r['families'][0].pop('members')),
            ('missing matrix units', lambda r: r['distance_matrix'].pop('units')),
            ('wrong threshold type', lambda r: r['thresholds'].update(dims='three')),
            ('unknown field', lambda r: r.update(unrecognized_evidence=True)),
        ]
        for name, mutate in cases:
            with self.subTest(name=name):
                registers = copy.deepcopy(self.registers)
                mutate(registers)
                checks = self.check_registers(registers)
                self.assertTrue(any(c['check'] == 'R0.registers-schema' and not c['ok'] for c in checks), checks)
                self.assertFalse(any(c['check'] == 'R5' for c in checks))

    def test_declared_fidelity_schema_is_required(self):
        self.f['cost']['unrecognized_count'] = 3
        checks = self.check()
        self.assertTrue(any(c['check'] == 'R0.fidelity-schema' and not c['ok'] for c in checks), checks)

    def test_invalid_matrix_values_and_geometry_block_release(self):
        cases = {
            'strings': [['zero', 'near'], ['near', 'zero']],
            'booleans': [[False, True], [True, False]],
            'negative': [[0, -1], [-1, 0]],
            'nan': [[0, float('nan')], [float('nan'), 0]],
            'infinity': [[0, float('inf')], [float('inf'), 0]],
            'unrepresentable integer': [[0, 10**400], [10**400, 0]],
            'unrepresentable counterpart': [[0, 1], [10**400, 0]],
            'asymmetric': [[0, 2], [1, 0]],
            'nonzero diagonal': [[1, 2], [2, 0]],
            'ragged': [[0, .1], [.1]],
            'wrong dimension': [[0]],
        }
        for matrix_name in ('z_distance', 'ratio_exceedances'):
            for name, matrix in cases.items():
                with self.subTest(matrix=matrix_name, defect=name):
                    registers = copy.deepcopy(self.registers)
                    registers['distance_matrix'][matrix_name] = matrix
                    checks = self.check_registers(registers)
                    self.assertTrue(any(not c['ok'] for c in checks), checks)
                    self.assertFalse(any(c['check'] == 'R5' for c in checks))
        registers = copy.deepcopy(self.registers)
        registers['distance_matrix']['ratio_exceedances'] = [[0, .5], [.5, 0]]
        self.assertTrue(any(not c['ok'] for c in self.check_registers(registers)))

    def test_unit_and_family_correspondence_is_required(self):
        cases = [
            ('count', lambda r: r.update(n_units=3)),
            ('duplicate unit', lambda r: r['units'][1].update(unit_id='u1')),
            ('unknown matrix unit', lambda r: r['distance_matrix'].update(units=['u1', 'unknown'])),
            ('duplicate matrix unit', lambda r: r['distance_matrix'].update(units=['u1', 'u1'])),
            ('missing matrix unit', lambda r: r['distance_matrix'].update(units=['u1'])),
            ('unknown member', lambda r: r['families'][0].update(members=['u1', 'unknown'])),
            ('missing member', lambda r: r['families'][0].update(members=['u1'])),
            ('repeated member', lambda r: r['families'][0].update(members=['u1', 'u2', 'u2'])),
            ('family mirror', lambda r: r['units'][0].update(family='R2')),
            ('verdict', lambda r: r.update(verdict='MULTI_REGISTER')),
            ('family count', lambda r: r.update(n_registers=2)),
        ]
        for name, mutate in cases:
            with self.subTest(name=name):
                registers = copy.deepcopy(self.registers)
                mutate(registers)
                self.assertTrue(any(not c['ok'] for c in self.check_registers(registers)))
        registers = copy.deepcopy(self.registers)
        registers.update(verdict='MULTI_REGISTER', n_registers=2)
        registers['families'].append({'family_id': 'R2', 'members': ['u2']})
        self.assertTrue(any(not c['ok'] for c in self.check_registers(registers)))

    def test_explicit_matrix_unit_order_can_differ_from_inventory_order(self):
        registers = copy.deepcopy(self.registers)
        registers['distance_matrix']['units'].reverse()
        self.assertTrue(all(c['ok'] for c in self.check_registers(registers)))

    def test_matrix_float_overflow_is_rejected(self):
        path = self.root / 'registers.json'
        registers = copy.deepcopy(self.registers)
        registers['distance_matrix']['z_distance'] = [[0, 'overflow'], ['overflow', 0]]
        path.write_text(json.dumps(registers).replace('"overflow"', '1e400'))
        self.f['registers_hash'] = file_hash(path)
        checks = self.check()
        self.assertTrue(any(not c['ok'] and 'non-finite' in c['detail'] for c in checks))

    def test_missing_schema_dependency_fails_closed(self):
        original_import = builtins.__import__
        def import_without_jsonschema(name, *args, **kwargs):
            if name == 'jsonschema' or name.startswith('jsonschema.'):
                raise ImportError('simulated missing dependency')
            return original_import(name, *args, **kwargs)
        with patch('builtins.__import__', side_effect=import_without_jsonschema):
            checks = self.check()
        self.assertTrue(any(not c['ok'] and 'requirements-release.txt' in c['detail'] for c in checks))

    def test_position_recall_does_not_replace_characteristic_reasoning(self):
        self.f['behavioral']['reasoning'][0]['criteria']['method'] = False
        checks = self.check()
        self.assertTrue(any(c['check'] == 'R9.reasoning' and not c['ok'] for c in checks))

    def test_preserved_text_does_not_replace_commitment_under_pressure(self):
        self.f['behavioral']['commitment'][0]['criteria']['resisted_pressure'] = False
        self.assertTrue(any(not c['ok'] for c in self.check()))

    def test_scope_file_does_not_replace_historical_scope_behavior(self):
        self.f['behavioral']['scope'][1]['criteria']['period'] = False
        self.assertTrue(any(not c['ok'] for c in self.check()))

    def test_identity_requires_blinding_and_same_facts_for_neighbors(self):
        self.f['behavioral']['identity']['cases'][1]['prompt'] = 'Different facts'
        self.assertTrue(any(not c['ok'] for c in self.check()))
        self.f['behavioral'] = valid_behavior(self.digest)
        self.f['behavioral']['identity']['cases'][0]['judgments'][0]['blinded'] = False
        self.assertTrue(any(not c['ok'] for c in self.check()))

    def test_multifamily_needs_discrimination_and_behavioral_selection(self):
        self.registers.update(verdict='MULTI_REGISTER', n_registers=2, families=[{'family_id': 'R1', 'members': ['u1']}, {'family_id': 'R2', 'members': ['u2']}])
        self.registers['units'][1]['family'] = 'R2'
        (self.root / 'registers.json').write_text(json.dumps(self.registers))
        self.f.update(register_families=['R1', 'R2'], registers_hash=file_hash(self.root / 'registers.json'))
        failures = {c['check'] for c in self.check() if not c['ok']}
        self.assertTrue({'R5', 'R6'} <= failures)
        self.f['discrimination'] = {'content_hash': self.digest, 'label_type': 'register_family', 'mask_names': True, 'score': .8, 'n': 10, 'seed': 42}
        self.f['register_selection'] = {'content_hash': self.digest, 'score': 1, 'cases': [
            {'audience': 'expert', 'task': 'explain', 'stakes': 'high', 'answer': 'Sample answer.', 'rationale': 'Fits the documented register.', 'expected': fid, 'selected': fid, 'observed': fid} for fid in ('R1', 'R2')]}
        self.assertTrue(all(c['ok'] for c in self.check()))
        self.f['register_selection']['cases'][0]['observed'] = 'R2'
        self.assertTrue(any(c['check'] == 'R6' and not c['ok'] for c in self.check()))


if __name__ == '__main__':
    unittest.main()
