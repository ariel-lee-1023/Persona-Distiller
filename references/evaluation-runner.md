# Optional evaluation runner

This multi-step runner is **research only**. Standard builds use
[recognition_runner.py](../scripts/recognition_runner.py) and the
[standard workflow](standard-workflow.md). Initialize research explicitly with a
fixed authorized budget. All predictions, grading, continuations and retries share it.

The HTTP adapter accepts a user-chosen chat-completions-compatible endpoint and
model. Set `EVALUATION_API_KEY` if bearer authentication is needed. It sends `model`,
`messages`, `temperature`, `stream:false` and reads `choices[0].message.content` and
provider `usage`. Credentials are not logged. Use material authorized for that endpoint.

## Explicit research mode

Only after a user requests comprehensive evaluation, record the fixed allowance:

```bash
python3 scripts/workflow.py init transworld-identity/research.sqlite \
  --runtime /path/to/runtime-skill --plan research-plan.json --mode research \
  --budget 40 --authorization "User explicitly requested comprehensive evaluation with 40 calls"
```

Forty is an example, not a default or an assurance that all gates fit. Count expected
candidate, baseline, neighbor, grader and continuation calls before choosing the
fixed budget. Research uses the existing version 2 suites with
`defined_before_extraction: true`, a `baseline_prompt`, and tasks with `id`, `prompt`,
`partition` (`development`/`final`), `group`, `kind` and named `criteria`. Related
scenario groups cannot cross partitions. Follow [release-evidence.md](release-evidence.md)
for source splits, and [behavioral-evaluation.md](behavioral-evaluation.md) for task
metadata. Projection IDs match the assigned source partition. Identity needs
`subject`, `identity_candidates` and `neighbors` with IDs `neighbor1`, `neighbor2`, etc.
It uses only the `identity` criterion; the grader sees candidate names and anonymous
answers, never the expected actor.

Pass the research database to `predict --workflow ... --kind persona`; choose
`--phase development` or, once ready, `--phase final`. Grading inherits the same
database from prediction. Research thresholds and `validate_package.py --release`
are unchanged. Exhausting the budget yields incomplete research, not a weaker gate.

Final groups are claimed before dispatch. The same workflow may resume the exact
experiment with unchanged suite, runtime, model and settings, reusing saved calls;
this continues its one exposure. It cannot reassign those groups to a changed
experiment. A different registry or renamed group does not create independence.
A final failure used for revision remains a failed release; new independent
qualification requires untouched evidence and explicitly authorized remaining work.

## Records, interruption and review

Every provider dispatch first reserves a call in the workflow database. Completion
and raw responses are persisted there, including partial progress. Repeating a
command reuses matching completed calls; it does not reset the budget. Failed or
interrupted attempts remain charged. Inspect them before using `--retry`; a lost
response may already have consumed provider time. Standard content changes require
`workflow.py repair WORKFLOW`; only one repair pass is permitted.

Run directories separately save runtime snapshots, prompts, requests/responses,
actual retrieval paths/spans, provider usage and status. Failures are sealed too.
Files are exclusively created, read-only and hash-manifested. They detect edits,
missing files and additions, but cannot defend against an owner recomputing hashes.
Workflow checkpoints retain runtime bytes and input hashes; the local SQLite ledger
is persistent accounting, not a claim of immutable or independently attested history.

```bash
python3 scripts/evaluation_runner.py verify transworld-identity/runs/predict-RUN
```

Disputed grades remain visible and cannot be exported as resolved evidence. A human
correction is keyed by `task-id/condition` and supplies `criteria`, integer `score`
(0/1/2), `reviewer`, `rationale`, and for identity an optional `choice`:

```bash
python3 scripts/evaluation_runner.py review transworld-identity/runs/grade-RUN \
  --corrections corrections.json --runs-root transworld-identity/runs
```

Review creates a sealed child, preserving prior judgments. A model used to prepare
corrections counts as another evaluation call; reserve it in the same workflow.
Human review of saved evidence makes no model call.

`export-persona` is research-only. It combines the existing paired projection and
behavioral fragments from resolved, sealed grade runs. Standard records feed the
separate completion report and cannot masquerade as research exports. Keep original
and partial results. See [standard-workflow.md](standard-workflow.md) for completion,
external/delegated accounting, stop commands and enforcement limits. Unit tests use
mock responses; they establish dispatch mechanics, not real persona fidelity.

## Reconstruction scope and protocol compatibility

New persona predictions record `structure_revision: 2` and
`context_protocol: "declared-retrieval"`. They use the declared runtime catalog and
retrieval protocol without a hidden Host scope contract. Reconstruction scope stays
in `transworld-identity/scope.md`; it is not in the runtime catalog. `--legacy-replay`
explicitly selects and records the historical injection for a persona replay. Missing
metadata in old records remains legacy evidence requiring inspection. Books conditions,
retrieval behavior, manifests and comparison prompts are unchanged by this revision.
