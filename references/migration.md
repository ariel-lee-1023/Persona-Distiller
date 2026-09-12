# Incremental migration to Transworld Identity

Read the existing persona as material. Record revision, working-tree state, runtime
hashes, layout, source inventory, evidence and evaluation status before changing it.
Preserve unrelated user edits. Classify claims as preserve, contextualize, correct/remove
or unresolved, with reasons and evidence links. Missing tests do not justify restarting
production or discarding a useful persona.

## Preserve the reader's encounter

When revising the README, read [readme-experience.md](readme-experience.md). Inspect its
introduction, distinctive examples, useful questions and narrator before editing.
Classify relevant passages as preserve, qualify, replace or remove, with brief reasons
in the existing migration/provenance record. Keep the README's language and unrelated
user edits. Directory renames, metadata updates and assessment-protocol changes default
to preserving effective prose; source/scope changes warrant edits to affected passages.

For introductions flattened by earlier migrations, inspect available local Git history
or supplied earlier versions. Recover useful passages selectively, checking current
scope and source support. Retain current installation facts and reject obsolete or
unsupported promises. If no earlier version is available, compose from the current
supported material and describe it as new writing, not recovered voice. A technical
upgrade alone does not justify rewriting the introduction.

## Relocate evidence without rewriting history

The only canonical evidence directory is `transworld-identity/`. Run:

```bash
python3 scripts/migrate_identity.py /path/to/persona
# Read-only import from a separate, already unpacked legacy repository/archive:
python3 scripts/migrate_identity.py /path/to/destination --import-from /path/to/legacy-copy
```

The tool inventories `fidelity-ledger/`, preflights conflicts, preserves exact file bytes,
moves or merges identical records, verifies hashes and updates active path references.
It records Git baseline, relocation mapping and file hashes under the canonical tree.
Different destination contents stop before mutation; reconcile them explicitly without
overwriting either record. Evidence symlinks require explicit reconciliation. Source
import never modifies the source repository. No model calls are made.

Operational scripts inside the evidence directory are relinked too. Script files outside
`runs/`, `history/`, `migrations/`, `archive/`, `archives/` and `snapshots/` are treated as
operational copies. Before changing one, migration preserves its exact bytes and file
mode under `migrations/<id>/originals/`, and records original/current paths and hashes in
`operational_updates`. Historical scripts within those reserved trees stay unchanged.
Legacy paths to changed operational scripts resolve to the preserved originals; current
canonical paths select the working copies. Execute the current audit after migration.
Running migration on an already renamed directory can repair its remaining operational
scripts without creating another evidence tree.

Historical manifests, transcripts and hashes remain unchanged even when they contain
old paths. `migrate_identity.resolve_record()` maps old relative paths to canonical
records, with read-only legacy fallback. It rejects ambiguous conflicting records.
Keep no duplicate live evidence tree. Git can recognize exact-byte renames when the
user later commits; the migration tool neither commits nor publishes.

Apply contextual corrections selectively. Recover only relevant missing passages from
existing supplied material, within the source boundary. Preserve nuanced voice and
scope. Explain dated verdicts, changes in evidence, exceptions and modern extrapolation.
Do not add material to satisfy a quota or turn inconclusive results into apparent support.

For every previous result record: applicable unchanged; historical evidence useful to
unchanged modules; superseded for changed inputs/protocol; or incomplete/unavailable.
Never invent missing fields or reinterpret an old score as the new recognition score.

| Change | Smallest check path |
| --- | --- |
| Rename/links/metadata, actual model inputs unchanged | Structural/path checks and applicability mapping; zero new answers |
| README-only prose, all recognition inputs unchanged | Preserve current assessment applicability; editorial/link checks, zero new recognition calls |
| First adoption of recognition | Review retained/changed core claims, then three-case bounded recognition |
| Fully reusable current recognition run | Reuse valid artifacts and check changed structure |
| Changed recognition inputs | Replace affected artifacts within the shared eight-call budget |

Each new assessment version freezes inputs before outputs. Use the same workflow
ledger for resume/repair; never create another ledger to reset its budget. Later,
separately scoped work has a new recorded contract and may import matching successful
calls with their original lineage; see `workflow.py import-calls`. Import does not
change historical records or certify changed dependencies.

Finish with current hashes, changed modules, added evidence, claim decisions,
relocation and applicability in `transworld-identity/`. Patch the README's actual
Candidate or Standard accepted status and affected limitations without replacing its
opening. Translate incomplete assessment into useful expectations and keep endpoint,
call allowance and migration details in linked records. Place use-affecting limitations
beside their promises and avoid duplicating them without a distinct purpose. Historical
research remains historical. Completion does not require inventing a pass or obtaining
fresh held-out sources. Publication follows the user's authorization, not this migration document.
