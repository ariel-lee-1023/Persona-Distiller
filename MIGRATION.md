# Migration to bounded production and Transworld Identity

The current standard replaces ad hoc lightweight samples with a three-case machine
recognition gate: six fresh answer contexts and two fresh judge contexts within eight
total evaluation calls. Standard acceptance requires package integrity, source integrity
and applicable recognition passes. Otherwise report Candidate, retaining usable work.
Research outcomes are separately scoped; old results are not converted into recognition
scores or probabilities of human acceptance.

Follow [incremental migration](references/migration.md) for existing personas and
[standard workflow](references/standard-workflow.md) for first adoption, resume and repair.
Do not rebuild every module or re-OCR a corpus merely because the standard changed.

README upgrades follow the [reader experience contract](references/readme-experience.md).
Preserve effective introductions, narrator, examples and the existing language. Recover
flattened prose selectively from available history against current scope, retaining
current installation and status. README-only changes with unchanged recognition inputs
preserve assessment applicability and consume zero new recognition calls.

`migrate_identity.py` relocates `fidelity-ledger/` to `transworld-identity/`, preserving
bytes and historical hashes, updating active routes and recording a relocation map.
Operational audit scripts in the evidence directory are updated with their exact
originals archived and their before/after hashes recorded; scripts in historical run
and archive trees remain untouched. Already renamed directories can repair these audit
scripts as well. Execute the canonical audit to verify the migration.
It preflights file and directory conflicts, preserves unrelated files and never generates
model answers. Read-only import is available for a separately unpacked repository/archive.
Historical manifests retain original paths; the resolver maps them without rewriting
history. Keep no duplicate live evidence tree.

Historical `fidelity.json`, source extractions, style statistics, answers and transcripts
remain evidence of their original inputs/protocol. Unknown fields stay unknown. Keep
whole-package results attached to their actual revision. New standard artifacts are
`evidence.json`, `recognition-profile.md`, `validation.json` and frozen `runs/<run-id>/`.
A pure directory rename requires structural/path checks and an applicability record,
not a new behavioral run. First adoption of recognition uses the bounded protocol.

Existing old SQLite workflow databases remain readable for accounting. Do not resume
an old ad hoc standard suite as if it were recognition. A separately scoped adoption
uses a new recorded contract; successful exact requests may be imported with original
lineage, while old lightweight requests normally do not match the new protocol.
Within the same standard run, reuse the same ledger across interruptions and the one
repair pass; never initialize another to reset consumption.

The old multi-step `evaluation_runner.py` now dispatches only explicitly configured
research workflows. Existing strict research schemas and hashes retain their meaning.
The class scorer leaves conflicting eligible claims pending for contextual review,
rather than resolving source contradictions through class/rank/ID order.

For older pre-3.0 research artifacts, preserve originals. Research partitioning and
schema migration remain documented in [release evidence](references/release-evidence.md)
and [schema index](references/schemas/README.md); missing research fields need not be
reconstructed to deliver an ordinary candidate or perform a rename-only migration.
