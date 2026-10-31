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
        ledger = self.root / "transworld-identity"
        ledger.mkdir()
        (ledger / "provenance.md").write_text(
            "# Audit\n\n## Weights and evidence\n\nRecorded evidence.\n", encoding="utf-8"
        )

    def run_validator(self, *extra_args: str) -> tuple[subprocess.CompletedProcess[str], dict]:
        report = self.root.parent / "validation.json"
        proc = subprocess.run(
            [sys.executable, str(VALIDATOR), str(self.root), "--structure-revision", "1", "--json", str(report), *extra_args],
            text=True,
            capture_output=True,
            check=False,
        )
        return proc, json.loads(report.read_text(encoding="utf-8"))

    def write_root_project(self, *, declared_name: str = "demo-perspective") -> None:
        self.write_valid_project(declared_name=declared_name)
        skill = self.root / '.agents/skills/demo-perspective'
        (skill / 'SKILL.md').rename(self.root / 'SKILL.md')
        (skill / 'references').rename(self.root / 'references')
        skill.rmdir()
        skill.parent.rmdir()
        skill.parent.parent.rmdir()
        (self.root / 'transworld-identity/scope.md').write_text('Existing source and reconstruction scope.\n')

    def test_explicit_root_layout_accepts_different_repository_name(self):
        self.write_root_project(declared_name='another-perspective')
        proc, report = self.run_validator('--layout', 'root', '--structure-revision', '2')
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(report['layout'], 'root')
        self.assertEqual(report['skill_root'], str(self.root))

    def test_root_layout_still_checks_frontmatter(self):
        self.write_root_project()
        core = self.root / 'SKILL.md'
        core.write_text(core.read_text().replace("description: Embodies Demo's public reasoning and writing for analytical questions.", 'description:'))
        proc, report = self.run_validator('--layout', 'root', '--structure-revision', '2')
        self.assertNotEqual(proc.returncode, 0)
        failures = {c['check'] for c in report['checks'] if not c['ok']}
        self.assertTrue({'C1', 'C2'}.issubset(failures))

    def test_root_layout_still_checks_missing_core_and_references(self):
        self.write_root_project()
        (self.root / 'SKILL.md').unlink()
        (self.root / 'references/voice.md').unlink()
        proc, report = self.run_validator('--layout', 'root', '--structure-revision', '2')
        self.assertNotEqual(proc.returncode, 0)
        failures = {c['check'] for c in report['checks'] if not c['ok']}
        self.assertTrue({'S1', 'S2', 'S3'}.issubset(failures))

    def test_root_layout_rejects_a_second_skill_copy(self):
        self.write_root_project()
        other = self.root / '.agents/skills/other-perspective'
        other.mkdir(parents=True)
        (other / 'SKILL.md').write_text((self.root / 'SKILL.md').read_text())
        proc, report = self.run_validator('--layout', 'root', '--structure-revision', '2')
        self.assertNotEqual(proc.returncode, 0)
        self.assertTrue(any(c['check'] == 'S1' and not c['ok'] for c in report['checks']))

    def test_root_layout_checks_discovery_alias_name(self):
        self.write_root_project()
        alias = self.root / '.agents/skills/wrong-name'
        alias.parent.mkdir(parents=True)
        alias.symlink_to('../..', target_is_directory=True)
        proc, report = self.run_validator('--layout', 'root', '--structure-revision', '2')
        self.assertNotEqual(proc.returncode, 0)
        self.assertTrue(any(c['check'] == 'C1b' and not c['ok'] for c in report['checks']))
        alias.rename(alias.with_name('demo-perspective'))
        proc, report = self.run_validator('--layout', 'root', '--structure-revision', '2')
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_root_layout_rejects_dangling_discovery_alias(self):
        self.write_root_project()
        alias = self.root / '.agents/skills/demo-perspective'
        alias.parent.mkdir(parents=True)
        alias.symlink_to('missing', target_is_directory=True)
        proc, report = self.run_validator('--layout', 'root', '--structure-revision', '2')
        self.assertNotEqual(proc.returncode, 0)
        self.assertTrue(any(c['check'] == 'S1' and not c['ok'] for c in report['checks']))

    def test_root_layout_still_rejects_broken_reference_links(self):
        self.write_root_project()
        (self.root / 'references/voice.md').write_text('Read `missing.md`.\n')
        proc, report = self.run_validator('--layout', 'root', '--structure-revision', '2')
        self.assertNotEqual(proc.returncode, 0)
        self.assertTrue(any(c['check'] == 'C5' and not c['ok'] for c in report['checks']))

    def test_historical_cluster_citations_do_not_require_runtime_modules(self):
        self.write_valid_project()
        (self.root / 'transworld-identity/provenance.md').write_text('Retired modules c09 and c12.\n')
        (self.root / 'README.md').write_text('Historical coverage included c10.\n')
        proc, report = self.run_validator()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue(next(c for c in report['checks'] if c['check'] == 'C6')['ok'])

    def test_dead_runtime_cluster_citation_still_fails(self):
        self.write_root_project()
        voice = self.root / 'references/voice.md'
        voice.write_text('Read c09 when needed.\n')
        proc, report = self.run_validator('--layout', 'root', '--structure-revision', '2')
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('c09', next(c for c in report['checks'] if c['check'] == 'C6')['detail'])

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
