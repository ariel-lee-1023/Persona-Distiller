"""Scope placement, reviewed migration, and actual request applicability regressions."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import test_recognition as standard
import recognition_runner as rr
from completion_report import validate_package
from workflow import Workflow, digest, file_hash
from migrate_identity import migrate_scope
from output_structure import structure_issues
import test_evaluation_runner as research
import test_fidelity as release


def inventory(root):
    return {p.relative_to(root).as_posix(): file_hash(p) for p in root.rglob('*') if p.is_file() and not p.is_symlink()}


class OutputStructureTests(unittest.TestCase):
    def fixture(self):
        f = standard.RunnerTests('test_full_first_adoption_eight_calls_blinding_caps_and_resume')
        f.setUp()
        self.addCleanup(f.doCleanups)
        return f

    def test_new_package_and_exact_reference_selection(self):
        f = self.fixture()
        self.assertFalse((f.root / 'references/scope.md').exists())
        self.assertEqual(validate_package(f.root)['verdict'], 'PASS')
        case = {**f.plan['cases'][0], 'references': []}
        request = rr.request_for(f.frozen, case, 'persona')
        self.assertEqual(set(request['dependencies']), {'SKILL.md'})
        self.assertNotIn('Examine the premise before judgment.', request['messages'][0]['content'])
        case['references'] = ['references/topic.md']
        self.assertEqual(set(rr.request_for(f.frozen, case, 'persona')['dependencies']), {'SKILL.md', 'references/topic.md'})

    def test_new_plans_reject_missing_references_and_legacy_scope_route(self):
        f = self.fixture()
        plan = copy.deepcopy(f.plan)
        del plan['cases'][0]['references']
        with self.assertRaisesRegex(ValueError, 'explicit references'): rr.validate_plan(plan)
        plan = {**f.plan, 'runtime_routes': {'scope': 'references/scope.md'}}
        with self.assertRaisesRegex(ValueError, 'redistribute'): rr.validate_plan(plan)
        plan = copy.deepcopy(f.plan); del plan['structure_revision']
        with self.assertRaisesRegex(ValueError, 'legacy plan'): rr.freeze(f.root, plan, f.run, f.wf.path)

    def test_scope_sentinel_is_judge_only_and_hashed(self):
        f = self.fixture()
        scope = f.root / 'transworld-identity/scope.md'
        scope.write_text('RECONSTRUCTION_SENTINEL: inherited translated passages, no journals.')
        f.plan['assessment_scope'] = 'transworld-identity/scope.md'
        f.run = f.run.with_name('judge-scope')
        frozen = rr.freeze(f.root, f.plan, f.run, f.wf.path)
        f.execute()
        for request in f.calls[:6]: self.assertNotIn('RECONSTRUCTION_SENTINEL', json.dumps(request))
        for request in f.calls[6:]: self.assertIn('RECONSTRUCTION_SENTINEL', json.dumps(request))
        self.assertEqual(frozen['hashes']['assessment_scope'], file_hash(scope))
        self.assertEqual(f.completion()['delivery_status'], 'standard_accepted')
        scope.write_text('Changed judge evidence')
        self.assertEqual(f.completion()['delivery_status'], 'candidate')
        prior = f.wf
        f.wf = Workflow.create(Path(f.tmp.name) / 'judge-update.sqlite', f.root, 'Judge evidence correction', ['SKILL.md'])
        f.wf.import_calls(prior.path)
        f.run = f.run.with_name('judge-update')
        rr.freeze(f.root, f.plan, f.run, f.wf.path)
        f.execute()
        self.assertEqual(f.wf.status()['consumed'], 2)

    def test_unused_maintainer_and_readme_edits_keep_hashes_and_calls(self):
        f = self.fixture(); f.execute()
        hashes = copy.deepcopy(f.frozen['hashes'])
        (f.root / 'transworld-identity/scope.md').write_text('Maintainer-only clarification')
        (f.root / 'README.md').write_text('Bring an unexamined report. [Scope](transworld-identity/scope.md).')
        f.execute()
        self.assertEqual(len(f.calls), 8)
        self.assertEqual(f.completion()['hashes'], hashes)
        self.assertEqual(f.completion()['delivery_status'], 'standard_accepted')

    def test_optional_operational_scope_basename_is_allowed(self):
        f = self.fixture()
        (f.root / 'references/scope.md').write_text('When comparing two reports, keep their premises separate.')
        f.plan['cases'][0]['references'] = ['references/scope.md']
        frozen = rr.freeze(f.root, f.plan, f.run.with_name('optional'), f.wf.path)
        self.assertIn('keep their premises separate', rr.request_for(frozen, f.plan['cases'][0], 'persona')['messages'][0]['content'])
        self.assertNotIn('keep their premises separate', rr.request_for(frozen, f.plan['cases'][1], 'persona')['messages'][0]['content'])
        self.assertEqual(validate_package(f.root)['verdict'], 'PASS')

    def test_host_and_symlink_routes_are_checked(self):
        f = self.fixture()
        host = f.root / 'AGENTS.md'
        host.write_text('Before answering load [scope](transworld-identity/scope.md).')
        self.assertEqual(validate_package(f.root)['verdict'], 'FAIL')
        with self.assertRaises(ValueError): rr.runtime_snapshot(f.root)
        host.write_text('For maintenance read [scope](transworld-identity/scope.md).')
        self.assertEqual(validate_package(f.root)['verdict'], 'PASS')
        host.write_text('Read [host rules](host-rules.md).')
        (f.root / 'host-rules.md').symlink_to('transworld-identity/scope.md')
        self.assertEqual(validate_package(f.root)['verdict'], 'FAIL')
        host.unlink()
        (f.root / 'references/alias.md').symlink_to('../transworld-identity/scope.md')
        self.assertEqual(validate_package(f.root)['verdict'], 'FAIL')

    def legacy_fixture(self):
        f = self.fixture()
        original_core = (f.root / 'SKILL.md').read_text()
        (f.root / 'SKILL.md').write_text(original_core + '\nAlways load references/scope.md.\n')
        (f.root / 'references/scope.md').write_text('English translations only; journals were unavailable.\nKeep pseudonymous speakers distinct from the author.\nFaith must be interpreted in its conceptual context.\n')
        (f.root / 'README.md').write_text('# An encounter\nBring the question that keeps returning.\n[Scope](references/scope.md)\n')
        (f.root / 'AGENTS.md').write_text('Always load references/scope.md with SKILL.md.\n')
        legacy_plan = copy.deepcopy(f.plan); del legacy_plan['structure_revision']
        legacy_plan['runtime_routes'] = {'scope': 'references/scope.md'}
        f.run = f.run.with_name('legacy')
        rr.freeze(f.root, legacy_plan, f.run, f.wf.path, legacy_replay=True)
        rr.execute(f.run, f.wf.path, client=f.client, legacy_replay=True)
        changes = {
            'SKILL.md': original_core + '\nKeep pseudonymous speakers distinct from the author.\n',
            'references/frameworks.md': 'Examine observations, then revise. Faith must be interpreted in its conceptual context.\n',
            'references/scope.md': None,
            'transworld-identity/scope.md': 'English translations only; journals were unavailable. Existing fictional hearing coverage retained.\n',
            'README.md': (f.root / 'README.md').read_text().replace('(references/scope.md)', '(transworld-identity/scope.md)'),
            'AGENTS.md': 'Load SKILL.md and task-relevant references. For maintenance read transworld-identity/scope.md.\n',
            'transworld-identity/standard-plan.json': json.dumps(f.plan)
        }
        plan = {'structure_revision': 2, 'reviewer': 'Fixture editorial review', 'legacy_scope': 'references/scope.md',
            'changes': [{'path': path, 'before_hash': file_hash(f.root / path) if (f.root / path).exists() else None,
                         'content': content, 'reconciliation_reason': 'Retain existing fictional coverage and inherited source limitation.'} for path, content in changes.items()],
            'passages': [{'start_line': i, 'end_line': i, 'destinations': [dest], 'reason': reason} for i, dest, reason in [
                (1, 'transworld-identity/scope.md', 'Reconstruction evidence'), (2, 'SKILL.md', 'Attribution across methods'),
                (3, 'references/frameworks.md', 'Situated conceptual condition')]], 'recognition_plan': f.plan}
        return f, plan

    def test_reviewed_migration_preserves_bytes_behavior_links_and_history(self):
        f, plan = self.legacy_fixture()
        before = inventory(f.root)
        preview = migrate_scope(f.root, plan)
        self.assertEqual(before, inventory(f.root))
        result = migrate_scope(f.root, plan, apply=True)
        self.assertEqual(result['status'], 'applied')
        self.assertFalse((f.root / 'references/scope.md').exists())
        self.assertIn('journals were unavailable', (f.root / 'transworld-identity/scope.md').read_text())
        self.assertIn('pseudonymous speakers', (f.root / 'SKILL.md').read_text())
        self.assertIn('conceptual context', (f.root / 'references/frameworks.md').read_text())
        self.assertEqual((f.root / 'README.md').read_text().splitlines()[:2], ['# An encounter', 'Bring the question that keeps returning.'])
        self.assertEqual(validate_package(f.root)['verdict'], 'PASS')
        for path, hash_value in before.items():
            if path.startswith('transworld-identity/runs/') or path in ('references/voice.md', 'transworld-identity/evidence.json', 'transworld-identity/provenance.md'):
                self.assertEqual(inventory(f.root)[path], hash_value)
        backup = next((f.root / 'transworld-identity/migrations').glob('scope-*/originals'))
        for change in plan['changes']:
            if change['before_hash']:
                self.assertEqual(file_hash(backup / change['path']), change['before_hash'])
        self.assertEqual(migrate_scope(f.root, plan, apply=True)['status'], 'already_applied')
        rows = preview['assessment_applicability']
        legacy_rows = [r for r in rows if '/legacy/' in r['record']]
        self.assertTrue(all(r['outcome'] == ('superseded' if r['condition'] == 'persona' else 'reusable_if_valid') for r in legacy_rows))
        self.assertEqual(f.completion()['delivery_status'], 'candidate')
        prior = f.wf
        f.wf = Workflow.create(Path(f.tmp.name) / 'migrated.sqlite', f.root, 'Migrated runtime', ['SKILL.md'])
        f.wf.import_calls(prior.path)
        f.run = f.run.with_name('migrated')
        rr.freeze(f.root, f.plan, f.run, f.wf.path)
        f.execute()
        # All candidate requests changed; all controls remain exact matches.
        self.assertEqual(sum(c['role'] == 'candidate' for c in f.wf.status()['calls']), 3)
        self.assertEqual(sum(c['role'] == 'control' for c in f.wf.status()['calls']), 0)

    def test_migration_conflicts_and_unmapped_passages_do_not_mutate(self):
        f, plan = self.legacy_fixture()
        before = inventory(f.root)
        del next(c for c in plan['changes'] if c['path'] == 'transworld-identity/scope.md')['reconciliation_reason']
        with self.assertRaisesRegex(ValueError, 'reconciliation_reason'): migrate_scope(f.root, plan, True)
        self.assertEqual(inventory(f.root), before)
        next(c for c in plan['changes'] if c['path'] == 'transworld-identity/scope.md')['reconciliation_reason'] = 'Retain both accounts.'
        plan['passages'].pop()
        with self.assertRaisesRegex(ValueError, 'every material'): migrate_scope(f.root, plan, True)
        self.assertEqual(inventory(f.root), before)

    def test_research_declared_context_and_explicit_legacy_replay(self):
        f = research.RunnerTests('test_prediction_isolation_retrieval_capture_and_sealed_grade_export')
        f.setUp(); self.addCleanup(f.doCleanups)
        (f.skill / 'transworld-identity').mkdir()
        (f.skill / 'transworld-identity/scope.md').write_text('ASSESSMENT_SENTINEL')
        (f.skill / 'references/scope.md').write_text('OPTIONAL_RUNTIME_SENTINEL')
        calls = []
        def client(endpoint, model, messages, temperature):
            calls.append(copy.deepcopy(messages))
            return {'text': json.dumps({'action': 'answer', 'text': 'An answer'})}
        def predict(legacy=False, kind='persona'):
            return research.runner.predict(f.skill, f.suite_path, f.root / 'new-runs', 'https://example.invalid', 'mock',
                workflow=f.workflow, client=client, legacy_replay=legacy, kind=kind)
        new = predict()
        self.assertTrue(all('ASSESSMENT_SENTINEL' not in json.dumps(c) and 'OPTIONAL_RUNTIME_SENTINEL' not in json.dumps(c) for c in calls))
        self.assertEqual(json.loads((new / 'config.json').read_text())['structure_revision'], 2)
        calls.clear(); old = predict(True)
        self.assertTrue(any('Host scope contract:\nOPTIONAL_RUNTIME_SENTINEL' in c[0]['content'] for c in calls))
        self.assertEqual(json.loads((old / 'config.json').read_text())['context_protocol'], 'legacy-host-scope')
        calls.clear(); predict(kind='books'); first = copy.deepcopy(calls)
        # Separate database avoids cache hits while comparing the unchanged Books contexts.
        f.workflow = Workflow.create(f.root / 'books-other.sqlite', f.skill, 'Mock books comparison', ['SKILL.md'], mode='research', budget=100, authorization='Mock comparison')
        calls.clear(); predict(True, kind='books')
        self.assertEqual(first, calls)

    def test_new_release_scope_gate_preserves_behavioral_requirement_and_old_reports(self):
        f = release.ReleaseTests('test_passes_complete_evidence_and_fails_changed_runtime')
        f.setUp(); self.addCleanup(f.doCleanups)
        self.assertTrue(all(c['ok'] for c in f.check()))
        original = (f.root / 'fidelity.json').read_bytes()
        (f.skill / 'references/scope.md').unlink()
        (f.skill / 'SKILL.md').write_text('Keep historical claims in their attested context.')
        (f.skill / 'transworld-identity').mkdir()
        (f.skill / 'transworld-identity/scope.md').write_text('Ethics, 1910 to 1920, inherited evidence.')
        updated = json.loads(json.dumps(f.f).replace(f.digest, release.runtime_hash(f.skill)))
        updated['structure_revision'] = 2
        path = f.root / 'new-fidelity.json'; path.write_text(json.dumps(updated))
        checks = release.release_checks(f.skill, path)
        self.assertTrue(all(c['ok'] for c in checks), checks)
        updated['behavioral']['scope'][1]['criteria']['period'] = False
        path.write_text(json.dumps(updated))
        checks = release.release_checks(f.skill, path)
        self.assertTrue(any(c['check'] == 'R9.scope' and not c['ok'] for c in checks))
        self.assertEqual((f.root / 'fidelity.json').read_bytes(), original)


if __name__ == '__main__': unittest.main()
