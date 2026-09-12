# Bounded builds and incremental upgrades

Ordinary builds and upgrades use **standard** mode. “Improve”, “upgrade”, “publish”
and “meet the latest version” do not request comprehensive research qualification.
Use **research** only for an explicit comprehensive evaluation request, with a
fixed call budget and recorded authorization before dispatch. Publication permission
is separate from evaluation scope; this workflow does not publish existing personas.

This changes scheduling and completion, not source quality, scoring formulas or
research thresholds. Preserve attribution, speaker boundaries, dates, applicability,
ordered procedures, costly commitments, interactional moves and concrete examples.
Preserve useful existing runtime material unless a specific correction justifies an
edit. A smaller evaluation budget is not a reason to shorten or simplify the persona.

## Start with the existing artifact

For upgrades, inspect the core, affected references, known limitations and reusable
results before editing. Identify content changes separately from formatting or
packaging changes. Preserve unaffected modules. Read additional passages or recover
missing substantive material with OCR when a real content gap calls for it. Do not
acquire sources just to replenish independent test sets in standard mode.

Record a plan before work:

```json
{
  "operation": "upgrade",
  "change_type": "content",
  "scope": "Restore the applicability condition in the topic module",
  "affected_modules": ["references/clusters/c01-topic.md"],
  "known_limitations": ["Blind identity evaluation remains incomplete"],
  "reusable_evidence": ["fidelity-ledger/prior-topic-review.json"]
}
```

`operation` is `new` or `upgrade`; `change_type` is `content` or `formatting`.
Affected modules are paths relative to the actual runtime root. Plan the files a new
build will create as well. The runtime root may be a nested skill or a canonical
root exposed by a discovery symlink. Keep its path stable while the workflow runs.

```bash
python3 scripts/workflow.py init fidelity-ledger/workflow.sqlite \
  --runtime /path/to/actual/skill-root --plan plan.json
python3 scripts/workflow.py status fidelity-ledger/workflow.sqlite
```

Initialization is exclusive: reuse the same database after interruption, never
initialize a fresh one to reset consumption. It stores mode, scope, affected files,
initial runtime bytes/hashes, budget, request/response records and item status.
Store this private maintainer database outside runtime references. Model prompts,
source excerpts and responses may be present; publish only appropriate summaries.

## Standard evaluation allowance

- New build: up to four short candidate responses and one review.
- Upgrade: up to two targeted candidate responses and one review.
- Eight model calls total, including retrieval continuations, grading, retries,
  delegated work and repair checks. The ceiling is not a target.
- At most one bounded repair pass. No baseline or neighboring-persona comparison.
- Formatting-only changes need no new model evaluation; document why content is unchanged.

The runner uses the shared database before every provider call. Reservations count
immediately, even if a request fails or the process dies. Completed requests with
identical relevant inputs are reused. Failed prediction runs also seal their completed
answers in `predictions.json`; a human may review those partial results for delivery.
They cannot be passed to the research grader as a completed prediction run. An unfinished reservation is not permission
to call again: inspect it, then explicitly use `--retry` if a retry is warranted
and budget remains. Invalid saved responses stay visible; do not overwrite them.

A standard task names only the references it needs. The core and scope contract are
always included. Changes outside those dependencies do not regenerate its answer.
Changing relevant inputs requires the single repair pass:

```bash
python3 scripts/workflow.py repair fidelity-ledger/workflow.sqlite
```

All calls share the overall limit; a repair does not add eight more calls. A new
model reviewer is still a grading call. A human reading already saved outputs does
not consume a model call. Human source review still needs an actual source locator,
excerpt, assessment and the condition or exception checked.

For a host or delegate that calls models outside the runner, reserve each call first
with `workflow.py reserve WORKFLOW --item ID --role candidate --candidate RESPONSE_ID --request request.json`.
The request JSON must include the actual prompt/settings and relevant input hashes.
A `saved_response` means reuse it without dispatch. Otherwise record the returned ID
with `workflow.py finish WORKFLOW --call-id ID --response response.json` or `--error REASON`. Use roles
`candidate`, `baseline`, `neighbor`, `grader`, or `delegated`; delegates producing
candidates or grades use those specific roles so their per-pass caps also apply.
Do not launch opaque multi-call delegation: each provider call needs a reservation.

At exhaustion, stop dispatch and package the supported current result. Additional
calls require explicit authorization, recorded with `workflow.py authorize-more WORKFLOW --calls N
--authorization "the user's additional evaluation instruction"`. This adds a fixed
allowance without deleting past consumption or resetting the repair counter. A host
must verify the authorization; the tool cannot establish who supplied that string.

## Lightweight content checks and completion

Run structural, discovery-link and reference-link validation. For substantive
changes, review changed claims against sources, including an important condition or
exception where applicable. Inspect a few actual representative responses aimed at
the changed behavior for unsupported claims, lost qualifications and execution of
the intended method. Reuse saved responses when their dependency hashes still match.
A new build records at least two representative responses; an upgrade needs at least
one relevant saved response, normally two when separate behaviors changed.

Use [evaluation-runner.md](evaluation-runner.md) for isolated optional model calls.
Manual saved responses can also be reviewed; record their origin honestly. The
completion command makes no model calls and does not turn structural PASS into a
fidelity claim. Its review JSON contains:

```json
{
  "summary": "Restored A as a prerequisite to B, retaining exception C",
  "reviewer": "source reviewer",
  "usable": true,
  "limitations": ["Independent identity evaluation is incomplete"],
  "source_checks": [{
    "claim": "B requires A", "locator": "Work, chapter 2, page 10",
    "source_excerpt": "The actual short passage reviewed",
    "condition_or_exception": "C prevents applying B",
    "assessment": "The updated module retains both requirements", "passed": true,
    "dependencies": {"references/clusters/c01-topic.md": "sha256:ACTUAL_FILE_HASH"}
  }],
  "responses": [{
    "prediction_run": "runs/predict-RUN", "id": "case1",
    "assessment": "The saved answer applies A and preserves C",
    "checks": {"supported_claims": true, "qualifications": true, "method": true}
  }],
  "pending_elements": [{"id": "PROC-new", "missing_evidence": "Required transfer evidence", "operative_core": false}],
  "existing_evidence": [{"id": "unchanged-voice-review", "dependencies": {"references/voice.md": "sha256:ACTUAL_FILE_HASH"}}],
  "remaining_items": ["Research qualification was not commissioned"],
  "source_processing": {"passages_reviewed": 2, "ocr_pages_recovered": 0}
}
```

Paths in review records are relative to the review JSON. Alternatively a response
entry has `record` and `record_hash` instead of `prediction_run`/`id`; the saved JSON
must contain actual `prompt`, `answer`, and runtime `dependencies` hashes. Those
operator-produced records are auditable declarations, not proof of execution.
Mark prior research entries in `existing_evidence` with `evaluation: "research"` and their
actual status and record location, including partial or failed runs without a `fidelity.json`.
These keep evaluation status incomplete unless the current strict release validator passes.
Source checks must cover the changed substantive modules. Packaging/formatting
work may omit source checks and answers but records `formatting_only_rationale`.

```bash
python3 scripts/completion_report.py /path/to/persona-project \
  --workflow fidelity-ledger/workflow.sqlite --review review.json \
  --out fidelity-ledger/completion-01.json
```

This stops new dispatch, runs the existing structural validator, checks evidence
freshness and writes a new report without overwriting prior reports:

- Delivery: `incomplete_draft` or `usable_working_version`.
- Evaluation: `lightweight_checks_completed`, `research_evaluation_incomplete`, or
  `research_evaluation_passed`. The report separately records whether lightweight
  checks completed and whether research was not run, failed/incomplete, or passed.

If research evidence exists, the report executes the unchanged `--release` checks
on it and retains failures. A usable working version can coexist with a failed or
incomplete research gate. Research PASS is reported only from that strict validator.
If lightweight evidence or usable content is missing, deliver an explicitly incomplete
draft with the specific gap. Report limitations even when all lightweight checks pass.

## Inconclusive evidence and resumption

`INSUFFICIENT_EVIDENCE` remains an inconclusive finding. Narrow the voice/register
claim without discarding useful source-supported reasoning. Do not lower thresholds,
try additional subsets, or start another evaluation round automatically. Preserve
class-specific admission rules: a new element lacking their evidence stays pending
outside the operative core. Never fabricate transfer or discrimination metrics.
Existing useful material is not automatically deleted or retroactively declared to
have passed current rules. Record its actual evidence status and relevant limitations.

Mark only affected module-level evidence stale in the completion ledger; retain
unrelated current evidence. Whole-runtime research hashes remain strict: any byte
change still prevents an old full-package research result from qualifying the new
bytes. Do not relabel that result as fresh just because local checks are reusable.

Checkpoint with `workflow.py checkpoint WORKFLOW --record checkpoint.json`, where the JSON
has `remaining_items` and a separate `source_processing` record. The database retains
runtime bytes/hashes, completed calls, partial/failed attempts and remaining budget.
Resume necessary unfinished work only. When asked to finish, run `workflow.py stop`
and produce the best supported completion report. Preserve partial research records.
Evaluation limits bound dispatch, not source-processing time or total elapsed time.

The database enforces calls routed through it, including concurrent reservations.
It cannot count hidden host calls, inspect an agent's private context, verify a human
judgment, or prevent the machine owner deleting it. Content judgments, declared dependencies and formatting-only classification also remain
auditable reviewer declarations. These are enforcement limits,
not reasons to invent stronger evaluation claims or automatically run more tests.
