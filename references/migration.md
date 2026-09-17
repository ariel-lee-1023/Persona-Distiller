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

## Align the activation entry

On a skill upgrade, add or correct the activation entry immediately after the core's
title, following [output-template.md](output-template.md). Require full default reading
of the core, voice and framework modules before the first substantive response,
including short answers. Briefly define each module's role; retain equivalent existing
filenames by naming their actual paths. Reuse fully retained context and reload lost
files after compaction. Keep topic/source modules conditional.

Reconcile later core rules, reference introductions, README usage and host instructions
that still make voice or frameworks optional. Preserve unrelated prose and historical
records. Add both modules to every active standard recognition case's explicit reference
list; the runner cannot infer them from prose. Changed loaded inputs invalidate affected
assessment claims. Record actual applicability without rewriting frozen runs or launching
new recognition calls beyond the authorized scope and budget.

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

## Redistribute reconstruction scope (structure revision 2)

This supersedes the old mandatory runtime-scope rule. Inspect scope passages before
moving anything. Coverage, source availability, editions, translation and verification
gaps belong in `transworld-identity/scope.md`. Necessary attribution constraints belong
concisely in the core; conditions on a method or concept belong beside it; expressive
qualifications belong in voice when useful. Keep consequential practical limitations
beside README promises and preserve the introduction. Record destinations and reasons
for every material passage. This is editorial judgment, not keyword classification.

Reconcile an existing reconstruction account deliberately, preserving disagreements
and both original versions. Remove scope loading from core and host instructions,
update active plans to revision 2 with explicit case references, then remove the old
file after accounting for incoming links. Never leave a runtime redirect or symlink
into assessment. An independently useful optional operational module may still use
the basename `scope.md`; no replacement mandatory file is required.

The helper accepts a reviewed JSON `--scope-plan`. It previews by default; `--apply`
executes the same preflight and writes the reviewed edits. Preview is a useful review
surface, not a new permission step. Its fields are:

- `structure_revision: 2`, `reviewer`, `legacy_scope` (the old relative file path).
- `changes`: distinct objects with `path`, `before_hash` (SHA-256 with `sha256:` prefix,
  or null for absent files), and full reviewed UTF-8 `content` (null deletes the file).
  A changed existing canonical scope also needs `reconciliation_reason`.
- `passages`: `start_line`, `end_line` in the original scope, `destinations` (relative
  paths with optional anchors) and `reason`. Account for every nonblank source line.
- Optional `recognition_plan`: the complete current revision-2 plan, used to compare
  actual requests with preserved frozen runs. Also update the active plan file in
  `changes` where it lives in the repository. Without a current plan, applicability
  remains explicitly unresolved.

```bash
python3 scripts/migrate_identity.py /path/to/persona --scope-plan /path/to/work/reviewed.json
python3 scripts/migrate_identity.py /path/to/persona --scope-plan /path/to/work/reviewed.json --apply
```

The helper stages changes, checks paths and host boundaries, then archives all changed
original files in `transworld-identity/migrations/<id>/originals/`. The migration record
keeps passage disposition, before/after hashes and request dependencies. Conflicting
or stale bytes stop before mutation. Reapplying a completed unchanged mapping is a
no-op. Source review must still confirm the meaning and sufficiency of redistribution;
mechanical coverage cannot prove that a philosophical condition survived correctly.

Removing injected scope generally changes persona requests, even after semantic
redistribution. Preserve old answers as history; reuse only complete matching requests
and configurations, including unchanged controls. Judge-only evidence changes can
reuse matching answers but require new judgments. README or unused maintainer edits
require zero model calls. Never drop an old dependency to manufacture a match.
A layout migration can finish without new recognition and should report Candidate
when no applicable pass remains. Any further assessment retains the eight-call budget
and explicit additional-budget rules; there is no automatic research escalation.
