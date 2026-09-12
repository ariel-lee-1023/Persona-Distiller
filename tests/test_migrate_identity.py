import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from migrate_identity import migrate, resolve_record, inventory
from workflow import runtime_files


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'persona'; self.root.mkdir()
        self.old = self.root / 'fidelity-ledger'; (self.old / 'runs/old').mkdir(parents=True)
        self.raw = b'{"historical_hash":"unchanged","path":"fidelity-ledger/runs/old/answer.txt"}\r\n'
        (self.old / 'runs/old/manifest.json').write_bytes(self.raw)
        (self.old / 'runs/old/answer.txt').write_bytes(b'Old output\r\n\x00')
        (self.old / 'source.json').write_text('{"old_field":"preserved without invented scores"}')
        (self.old / 'empty').mkdir()
        (self.root / 'README.md').write_text('Read fidelity-ledger/source.json.\nUnrelated user text.\n')
        self.before = inventory(self.old)

    def test_exact_byte_rename_and_historical_path_resolution_without_answers(self):
        result = migrate(self.root)
        self.assertEqual(result['model_calls'], 0)
        self.assertFalse(self.old.exists())
        new = self.root / 'transworld-identity'
        for p, h in self.before.items(): self.assertEqual(inventory(new)[p], h)
        self.assertEqual((new / 'runs/old/manifest.json').read_bytes(), self.raw)
        self.assertEqual(resolve_record(self.root, 'fidelity-ledger/runs/old/manifest.json').read_bytes(), self.raw)
        self.assertEqual((self.root / 'README.md').read_text(), 'Read transworld-identity/source.json.\nUnrelated user text.\n')
        self.assertEqual(migrate(self.root)['status'], 'already_canonical')

    def test_readme_relink_preserves_introduction_examples_bytes_and_candidate(self):
        introduction = '\ufeff# 一个审慎的观察者\r\n\r\n先把你看到的事说清楚。  \r\n'
        example = '\r\nSuggested prompt: What observation would change this verdict?\r\n'
        status = '\r\n**Status: Candidate.** See [assessment](fidelity-ledger/validation.json).\r\n'
        original = (introduction + example + status).encode('utf-8')
        readme = self.root / 'README.md'
        readme.write_bytes(original)
        validation = b'{"delivery_status":"candidate","recognition":{"outcome":"not_run"}}\r\n'
        (self.old / 'validation.json').write_bytes(validation)
        (self.root / 'SKILL.md').write_text('Inspect the observations before endorsing.')
        before_runtime = runtime_files(self.root)

        result = migrate(self.root)

        self.assertEqual(readme.read_bytes(), original.replace(
            b'fidelity-ledger/validation.json', b'transworld-identity/validation.json'))
        link = readme.read_text().split('[assessment](', 1)[1].split(')', 1)[0]
        self.assertEqual((self.root / link).read_bytes(), validation)
        self.assertEqual(json.loads((self.root / link).read_bytes())['delivery_status'], 'candidate')
        self.assertEqual(runtime_files(self.root), before_runtime)
        self.assertEqual(result['model_calls'], 0)
        migrate(self.root)
        self.assertEqual(readme.read_bytes(), original.replace(
            b'fidelity-ledger/validation.json', b'transworld-identity/validation.json'))

    def test_conflicting_destination_stops_before_any_changes(self):
        new = self.root / 'transworld-identity'; new.mkdir(); (new / 'source.json').write_text('conflict')
        with self.assertRaisesRegex(ValueError, 'nothing changed'): migrate(self.root)
        self.assertEqual(inventory(self.old), self.before)
        self.assertEqual((new / 'source.json').read_text(), 'conflict')
        self.assertIn('fidelity-ledger/', (self.root / 'README.md').read_text())
        with self.assertRaisesRegex(ValueError, 'conflicting'): resolve_record(self.root, 'fidelity-ledger/source.json')

    def test_identical_destination_reconciles_without_duplicate_tree(self):
        new = self.root / 'transworld-identity'; new.mkdir()
        (new / 'source.json').write_bytes((self.old / 'source.json').read_bytes())
        (new / 'unrelated.json').write_text('preserve')
        migrate(self.root)
        self.assertFalse(self.old.exists())
        self.assertEqual((new / 'unrelated.json').read_text(), 'preserve')

    def test_directory_file_collision_is_preflighted(self):
        new = self.root / 'transworld-identity'; new.mkdir(); (new / 'runs').write_text('file')
        with self.assertRaises(ValueError): migrate(self.root)
        self.assertEqual(inventory(self.old), self.before)

    def test_read_only_import_does_not_mutate_source(self):
        dest = Path(self.tmp.name) / 'destination'; dest.mkdir()
        self.assertEqual(resolve_record(self.root, 'transworld-identity/source.json').read_bytes(), (self.old / 'source.json').read_bytes())
        result = migrate(dest, self.root)
        self.assertEqual(result['status'], 'imported')
        self.assertEqual(inventory(self.old), self.before)
        self.assertEqual((dest / 'transworld-identity/runs/old/manifest.json').read_bytes(), self.raw)
        self.assertIn('fidelity-ledger/', (self.root / 'README.md').read_text())


if __name__ == '__main__': unittest.main()
