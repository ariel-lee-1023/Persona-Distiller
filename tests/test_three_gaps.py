import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
import test_recognition as fixtures
import recognition_runner as rr
from migrate_identity import migrate, resolve_record
from workflow import Workflow, file_hash


class ThreeGapTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.RunnerTests('test_full_first_adoption_eight_calls_blinding_caps_and_resume')
        self.f.setUp(); self.addCleanup(self.f.doCleanups)

    def test_migrated_audit_executes_and_original_is_preserved(self):
        root = Path(self.f.tmp.name) / 'legacy'; old = root / 'fidelity-ledger'; old.mkdir(parents=True)
        (old / 'source-manifest.json').write_text('{"sources": 1}')
        code = b"from pathlib import Path\nimport json\nprint(json.loads(Path('fidelity-ledger/source-manifest.json').read_text())['sources'])\n"
        (old / 'check_runtime.py').write_bytes(code)
        historical = old / 'runs/old'; historical.mkdir(parents=True)
        (historical / 'check_runtime.py').write_bytes(code)
        result = migrate(root)
        proc = subprocess.run([sys.executable, str(root / 'transworld-identity/check_runtime.py')], cwd=root, text=True, capture_output=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), '1')
        self.assertEqual((root / 'transworld-identity/runs/old/check_runtime.py').read_bytes(), code)
        change = result['operational_updates'][0]
        self.assertEqual((root / change['original']).read_bytes(), code)
        self.assertFalse(old.exists())
        self.assertEqual(resolve_record(root, 'fidelity-ledger/check_runtime.py').read_bytes(), code)
        self.assertEqual(migrate(root)['status'], 'already_canonical')

    def test_explicit_retry_replaces_overlong_completed_answer_with_remaining_budget(self):
        first = True
        def client(request, timeout):
            nonlocal first
            if first:
                first = False
                return {'text': 'word ' * 251}
            return self.f.client(request, timeout)
        rr.execute(self.f.run, self.f.wf.path, client=client)
        path = self.f.run / '0-persona.json'; original = path.read_bytes()
        self.assertEqual(self.f.wf.status()['consumed'], 6)
        self.assertEqual(self.f.wf.status()['remaining'], 2)
        self.f.execute(retry=True)
        self.assertLessEqual(rr.words(json.loads(path.read_text())['response']['text']), 250)
        self.assertEqual(self.f.wf.status()['consumed'], 8)
        self.assertTrue(any(p.read_bytes() == original for p in (self.f.run / 'attempts').rglob('*.json')))
        self.assertEqual(self.f.completion()['delivery_status'], 'candidate')

    def test_explicit_retry_replaces_malformed_judge_json(self):
        save = rr.save
        def interrupted_save(path, value):
            save(path, value)
            if Path(path).name == 'judge-1.json': raise KeyboardInterrupt()
        def client(request, timeout):
            if request['model'] == 'mock-judge': return {'text': '{invalid JSON'}
            return self.f.client(request, timeout)
        with patch.object(rr, 'save', side_effect=interrupted_save):
            with self.assertRaises(KeyboardInterrupt): rr.execute(self.f.run, self.f.wf.path, client=client)
        self.assertEqual(self.f.wf.status()['consumed'], 7)
        path = self.f.run / 'judge-1.json'; original = path.read_bytes()
        self.f.execute(retry=True)
        self.assertIn('cases', json.loads(json.loads(path.read_text())['response']['text']))
        self.assertEqual(self.f.wf.status()['consumed'], 8)
        self.assertTrue(any(p.read_bytes() == original for p in (self.f.run / 'attempts').rglob('*.json')))

    def test_identical_presented_answers_cannot_be_standard_accepted(self):
        def client(request, timeout):
            if request['model'] == 'mock': return {'text': 'Inspect the evidence before agreeing.'}
            return self.f.client(request, timeout)
        result = rr.execute(self.f.run, self.f.wf.path, client=client)
        self.assertEqual(result['recognition']['outcome'], 'failed')
        self.assertEqual([j['persona_wins'] for j in result['recognition']['judges']], [0, 0])
        self.assertEqual(self.f.completion()['delivery_status'], 'candidate')

    def test_invalid_answer_has_no_implicit_retry(self):
        def client(request, timeout):
            if request['model'] == 'mock': return {'text': 'word ' * 251}
            return self.f.client(request, timeout)
        rr.execute(self.f.run, self.f.wf.path, client=client)
        self.f.execute()
        self.assertEqual(self.f.wf.status()['consumed'], 6)
        self.assertTrue(all(c['output_usable'] is False for c in self.f.wf.status()['calls']))
        self.assertEqual(self.f.completion()['delivery_status'], 'candidate')

    def test_unusable_import_can_be_replaced_without_mutating_original_ledger(self):
        donor = Workflow.create(Path(self.f.tmp.name) / 'donor.sqlite', self.f.root, 'prior generation', ['SKILL.md'])
        request = rr.request_for(self.f.frozen, self.f.plan['cases'][0], 'persona')
        call, _ = donor.reserve('recognition/0-persona', 'candidate', request, '0')
        donor.finish(call, response={'text': 'word ' * 251})
        before = file_hash(donor.path)
        self.f.wf.import_calls(donor.path)
        self.f.execute()
        self.assertEqual(self.f.wf.status()['consumed'], 5)
        result = self.f.execute(retry=True)
        self.assertEqual(self.f.wf.status()['consumed'], 8)
        self.assertEqual(result['recognition']['outcome'], 'passed')
        self.assertEqual(file_hash(donor.path), before)

    def test_shape_invalid_judge_replaced_but_failed_acceptance_is_not_retried(self):
        save = rr.save
        def interrupted_save(path, value):
            save(path, value)
            if Path(path).name == 'judge-1.json': raise KeyboardInterrupt()
        def client(request, timeout):
            if request['model'] == 'mock-judge': return {'text': '{"cases": []}'}
            return self.f.client(request, timeout)
        with patch.object(rr, 'save', side_effect=interrupted_save):
            with self.assertRaises(KeyboardInterrupt): rr.execute(self.f.run, self.f.wf.path, client=client)
        self.f.execute(retry=True)
        record = json.loads((self.f.run / 'judge-1.json').read_text())
        self.assertEqual(len(json.loads(record['response']['text'])['cases']), 3)
        self.assertEqual(self.f.wf.status()['consumed'], 8)
        self.f.execute(retry=True)
        self.assertEqual(self.f.wf.status()['consumed'], 8)

    def test_identity_masking_can_create_forced_ties(self):
        frozen = self.f.plan
        frozen['identity_labels'] = ['Identity One', 'Identity Two']
        self.f.run = self.f.root / 'transworld-identity/runs/masked'
        rr.freeze(self.f.root, frozen, self.f.run, self.f.wf.path)
        def client(request, timeout):
            if request['model'] == 'mock':
                name = 'Identity One' if 'Runtime perspective:' in request['messages'][0]['content'] else 'Identity Two'
                return {'text': name + ': inspect the evidence.'}
            return self.f.client(request, timeout)
        result = rr.execute(self.f.run, self.f.wf.path, client=client)
        self.assertEqual(result['recognition']['outcome'], 'failed')
        for judge in result['recognition']['judges']:
            self.assertTrue(all(c['effective'] == 'tie' and c['identical_presented_answers'] for c in judge['comparisons'].values()))
        self.f.execute(retry=True)
        self.assertEqual(self.f.wf.status()['consumed'], 8)

    def test_prior_directory_migration_can_repair_operational_scripts(self):
        root = Path(self.f.tmp.name) / 'already-moved'; new = root / 'transworld-identity'; new.mkdir(parents=True)
        (new / 'source.json').write_text('{}')
        original = b"from pathlib import Path\nassert Path('fidelity-ledger/source.json').is_file()\n"
        (new / 'check_runtime.py').write_bytes(original)
        result = migrate(root)
        self.assertEqual(result['status'], 'updated_operational')
        self.assertEqual((root / result['operational_updates'][0]['original']).read_bytes(), original)
        proc = subprocess.run([sys.executable, str(new / 'check_runtime.py')], cwd=root, capture_output=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(migrate(root)['status'], 'already_canonical')

    def test_read_only_import_updates_only_destination_audit(self):
        root = Path(self.f.tmp.name) / 'source'; old = root / 'fidelity-ledger'; old.mkdir(parents=True)
        (old / 'source.json').write_text('{}')
        code = b"from pathlib import Path\nassert Path('fidelity-ledger/source.json').is_file()\n"
        (old / 'audit.py').write_bytes(code)
        dest = Path(self.f.tmp.name) / 'imported'; dest.mkdir()
        result = migrate(dest, root)
        self.assertEqual((old / 'audit.py').read_bytes(), code)
        self.assertEqual((dest / result['operational_updates'][0]['original']).read_bytes(), code)
        proc = subprocess.run([sys.executable, str(dest / 'transworld-identity/audit.py')], cwd=dest, capture_output=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == '__main__': unittest.main()
