"""Regression tests for the generated persona project layout."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VALIDATOR = REPO / "scripts" / "validate_package.py"


class TestGeneratedProjectLayout(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "demo-perspective"
        self.addCleanup(self._tmp.cleanup)

    def write_valid_project(self, *, declared_name: str = "demo-perspective") -> None:
        skill = self.root / ".agents" / "skills" / "demo-perspective"
        clusters = skill / "references" / "clusters"
        clusters.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\n"
            f"name: {declared_name}\n"
            "description: Embodies Demo's public reasoning and writing for analytical questions.\n"
            "---\n\n"
            "# Demo perspective\n\n"
            "## Loading depth\n"
            "Open references/clusters/c01-topic.md when the topic applies.\n",
            encoding="utf-8",
        )
        (skill / "references" / "frameworks.md").write_text("# Frameworks\n", encoding="utf-8")
        (skill / "references" / "voice.md").write_text("# Voice\n", encoding="utf-8")
        (clusters / "c01-topic.md").write_text("# Topic\n\nuid: c01\n", encoding="utf-8")
        ledger = self.root / "fidelity-ledger"
        ledger.mkdir()
        (ledger / "provenance.md").write_text(
            "# Audit\n\n## Weights and evidence\n\nRecorded evidence.\n", encoding="utf-8"
        )

    def run_validator(self) -> tuple[subprocess.CompletedProcess[str], dict]:
        report = self.root.parent / "validation.json"
        proc = subprocess.run(
            [sys.executable, str(VALIDATOR), str(self.root), "--json", str(report)],
            text=True,
            capture_output=True,
            check=False,
        )
        return proc, json.loads(report.read_text(encoding="utf-8"))

    def test_accepts_agents_skill_layout(self) -> None:
        self.write_valid_project()
        proc, report = self.run_validator()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(report["verdict"], "PASS")
        self.assertTrue(report["skill_root"].endswith(".agents/skills/demo-perspective"))

    def test_rejects_legacy_root_skill_layout(self) -> None:
        self.root.mkdir()
        (self.root / "SKILL.md").write_text(
            "---\nname: demo-perspective\ndescription: A sufficiently descriptive legacy skill.\n---\n",
            encoding="utf-8",
        )
        proc, report = self.run_validator()
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(report["verdict"], "FAIL")
        self.assertTrue(any(".agents/skills" in item["detail"] for item in report["checks"]))

    def test_requires_directory_and_frontmatter_names_to_match(self) -> None:
        self.write_valid_project(declared_name="other-perspective")
        proc, report = self.run_validator()
        self.assertNotEqual(proc.returncode, 0)
        mismatch = next(item for item in report["checks"] if item["check"] == "C1b")
        self.assertFalse(mismatch["ok"])

    def test_missing_descriptive_links_are_rejected(self):
        self.write_valid_project()
        skill = self.root / '.agents/skills/demo-perspective/SKILL.md'
        with skill.open('a') as out:
            out.write('\nRead [missing](references/clusters/unwritten-judgment.md).\n')
        proc, report = self.run_validator()
        self.assertNotEqual(proc.returncode, 0)
        self.assertTrue(any(c['check'] == 'C5' and not c['ok'] for c in report['checks']))

    def test_missing_reference_definition_link_is_rejected(self):
        self.write_valid_project()
        voice = self.root / '.agents/skills/demo-perspective/references/voice.md'
        voice.write_text('[deep voice][details]\n\n[details]: <missing%20voice.md>\n')
        proc, report = self.run_validator()
        self.assertNotEqual(proc.returncode, 0)

    def test_compact_reference_names_and_published_symlink_layout(self):
        self.write_valid_project()
        skill = self.root / '.agents/skills/demo-perspective'
        with (skill / 'SKILL.md').open('a') as out:
            out.write('\nRead `voice.md` and `frameworks.md` when needed.\n')
        (skill / 'SKILL.md').rename(self.root / 'SKILL.md')
        (skill / 'references').rename(self.root / 'references')
        skill.rmdir()
        skill.symlink_to('../..', target_is_directory=True)
        proc, report = self.run_validator()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_release_does_not_accept_structure_without_fidelity(self):
        self.write_valid_project()
        proc = subprocess.run([sys.executable, str(VALIDATOR), str(self.root), '--release'], capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('R0', proc.stdout)


if __name__ == "__main__":
    unittest.main()
