# Persona Distiller

[Persona Distiller](SKILL.md) builds or incrementally upgrades a reusable perspective
skill from one person's supplied public record. It preserves characteristic reasoning,
conditional judgments, costly commitments, interaction and expressive range, with
source locators and a compact operational core.

Ordinary production uses a bounded **standard** workflow. Set a finite reading/OCR
boundary, construct the source-grounded package, and run three recognition cases:
six answers (persona and competent generic control) plus two fresh-context judges.
Eight evaluation calls total includes retries and repair retests. At most one targeted
repair is allowed, without a new budget. Inconclusive evidence narrows the claim and
ends the run with an accurate status.

## What is delivered

```text
persona-repository/
  SKILL.md
  AGENTS.md                       # where the host requires it
  README.md
  LICENSE
  references/
    frameworks.md
    voice.md
    <topic-or-source-modules>.md
  transworld-identity/
    scope.md
    provenance.md
    evidence.json
    recognition-profile.md
    validation.json
    runs/<run-id>/
    migrations/<migration-id>/
  .agents/skills/<persona-slug> -> ../..
```

Equivalent existing modules can keep their names. Runtime references contain useful
attribution and context but never load hidden assessment rubrics or answers. Raw books,
recovered full text and scratch stay outside the published repository.
Reconstruction coverage and evidence limits live in `transworld-identity/scope.md`.
Every produced skill includes an activation entry immediately after its title. Before
the first substantive response, including short answers, it requires the full core,
`references/voice.md` and `references/frameworks.md`. Voice supplies the expressive
system; frameworks supplies concepts, reasoning procedures and supported conditional
judgments. Already retained files need not be reread; files lost after compaction must
be reloaded. Additional topic/source modules load when relevant. Equivalent existing
module names retain the same responsibilities and default loading requirement.
Necessary behavioral conditions stay beside the instructions they qualify.

Each persona's README also introduces the particular encounter it offers: what catches
this perspective's attention, what it asks of the reader and a concrete question to try.
The [README experience contract](references/readme-experience.md) preserves supported
character and useful introductions through upgrades, with consequential limitations
beside the promises they qualify. Detailed evaluation stays in linked records. This
editorial check runs inside the existing authoring pass and adds no recognition calls.
See [contrasting examples and a reviewed migration](references/readme-examples.md).

Transworld Identity names the evidence and assessment function. It connects the
representation to an identified historical record under explicitly changed circumstances;
it does not claim numerical identity, metaphysical essence or fabricated memories.

| Reported status | Meaning |
| --- | --- |
| Candidate | One or more required gates are incomplete, failed or inconclusive |
| Standard accepted | Current package, source and bounded machine-recognition gates pass |
| Research assessed | Separately authorized research exists; report each result and scope |

Source-grounded, machine-recognized, useful beyond a minimal persona prompt, likely to
pass informed human assessment and comprehensively evaluated are different claims.
An 80/100 recognition score is a provisional engineering threshold, not 80% human
acceptance. The generic control does not establish superiority to a minimal persona
prompt. Human review is not required for ordinary delivery. Calibration is separate,
explicitly budgeted tool-level research.

## Use and installation

Make this repository's `SKILL.md` available to your agent host as the `persona-distiller`
skill, then provide a public source corpus and the desired perspective/use. The skill
works from local files or authorized remote inputs and adapts paths to the host.
It needs Python 3.9+ and filesystem access. Standard scripts use the standard library;
optional research/schema tests use [requirements-release.txt](requirements-release.txt).
Model evaluation needs an authorized endpoint and explicitly configured models.

For ordinary work read the [standard workflow](references/standard-workflow.md),
[artifact template](references/output-template.md) and [recognition protocol](references/recognition-protocol.md).
They include executable commands, source contracts, caps, deadlines, resume rules and
source-review format. [Schemas](references/schemas/README.md) and the fictional
[example plan](assets/standard-plan.example.json) make the contracts reviewable.
Generate a copy with `recognition_runner.py example-plan`; replace every fictional
source, case and pattern before using it for a real assessment.

For existing personas use the [migration guide](references/migration.md). The migration
tool moves `fidelity-ledger/` to `transworld-identity/` without rewriting historical
records, preflights conflicts, supports read-only import and produces a relocation map.
Rename-only work makes zero new model calls. Partial progress and applicable outputs
survive restarts; changed dependencies invalidate only affected artifacts.

## Maintainer tools and validation

The source helpers remain available: `corpus_clean.py`, `segment.py`, `kwic.py`,
`token_count.py`, `name_audit.py`, `style_metrics.py` and `zh_metrics.py`. Recover only
what the scoped task needs. Quantitative register discovery, class admission,
held-out tests and comparator expansion belong to [explicit research](references/research-mode.md),
with their own recorded scope and budget. No live comprehensive benchmark is required
to validate this engineering implementation.

```bash
python3 -m pip install -r requirements-release.txt
python3 -m unittest discover -s tests -v
python3 scripts/validate_package.py /path/to/persona
```

Regression tests use fictional records and mocked model responses. They cover scoring
boundaries, per-dimension floors, disagreement, incomplete outputs, runtime isolation,
budget/resume, dependency invalidation, truthful status and lossless migration. These
verify implementation contracts, not empirical recognition validity. The strict
`validate_package.py --release --fidelity ...` command remains a research evidence check.

## Scope and contribution

Use public material the user has the right to use for analysis, study and ideation.
The output is perspective work, not forged attribution or deceptive impersonation.
Keep specification examples fictional or schematic; a real subject's example must
not silently become a universal rule. Preserve supported nuance and record limits.

See [MIGRATION.md](MIGRATION.md) for upgrade compatibility, [CHANGELOG.md](CHANGELOG.md)
for changes, and [LICENSE](LICENSE) for the MIT license. The license covers this tool's
original text, not the underlying source books.
