import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from release_checks import validate_declared_schema, validate_register_evidence

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/register_discover.py'
NEUTRAL = 'The account describes causes and outcomes in a careful sequence. '
MARKED = 'Perhaps you must check this result and explain it? '


class RegisterDiscoveryTests(unittest.TestCase):
    def discover(self, texts):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = root / 'corpus'; corpus.mkdir()
            for i, text in enumerate(texts):
                (corpus / f'u{i}.txt').write_text(text)
            output = root / 'registers.json'
            run = subprocess.run([sys.executable, str(SCRIPT), str(corpus), '--json', str(output)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            raw = output.read_text()
            self.assertNotIn('Infinity', raw)
            self.assertNotIn('NaN', raw)
            data = json.loads(raw)
            validate_declared_schema(data, 'registers')
            return data

    def test_one_added_sentence_cannot_force_register_split(self):
        data = self.discover([NEUTRAL * 100, NEUTRAL * 100 + 'Perhaps you must check?'])
        self.assertEqual(data['verdict'], 'SINGLE_REGISTER')
        self.assertEqual(data['forced_splits'], [])
        validate_register_evidence(data)

    def test_supported_persistent_difference_is_retained_and_json_is_finite(self):
        data = self.discover([NEUTRAL * 150, MARKED * 150])
        self.assertEqual(data['verdict'], 'MULTI_REGISTER')
        self.assertTrue(data['stability']['stable'])
        self.assertTrue(any(v is None for pair in data['forced_splits'] for v in pair['ratios'].values()))
        validate_register_evidence(data)

    def test_thin_corpus_reports_insufficient_evidence(self):
        data = self.discover([NEUTRAL, MARKED])
        self.assertEqual(data['verdict'], 'INSUFFICIENT_EVIDENCE')
        with self.assertRaisesRegex(ValueError, 'sufficient'):
            validate_register_evidence(data)

    def test_localized_difference_is_not_a_stable_family(self):
        data = self.discover([NEUTRAL * 150, MARKED * 50 + NEUTRAL * 100])
        self.assertEqual(data['verdict'], 'INSUFFICIENT_EVIDENCE')
        self.assertFalse(data['stability']['stable'])


if __name__ == '__main__':
    unittest.main()
