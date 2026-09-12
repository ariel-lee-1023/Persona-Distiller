# Standard production and completion

Standard is the default for fresh builds and upgrades. Comprehensive research needs
explicit authorization and a fixed budget; publishing or upgrading does not imply it.
Use a finite source-processing boundary separately from evaluation. At that boundary,
narrow supported scope or deliver a candidate. Keep source recovery outside the repository.

## Prepare the artifact and contract

Follow [situated-evidence.md](situated-evidence.md), [output-template.md](output-template.md)
and, for existing personas, [migration.md](migration.md). Preserve supported content and
contextualize overbroad rules. Source claims do not need a numerical research admission
score. No automatic register certification, held-out experiment or comparator expansion.

Prepare a JSON plan using [recognition-plan.schema.json](schemas/recognition-plan.schema.json).
Its `contract` records subject, intended use, supported `period_domains`, supplied sources,
relative output location, delivery target and `source_boundary`: priority materials,
finite `reading_units` and `ocr_pages`. In provenance explain what a reading unit means
and record actual use. A schema-valid schematic example can be generated locally:

```bash
python3 scripts/recognition_runner.py example-plan --out /path/to/work/plan.json
```

Replace the fictional evidence, cases and diagnostic patterns with the actual bounded
production findings. Do not run the example as an empirical persona assessment.
The plan holds three cases in order (characteristic, changed_condition, interpersonal),
situated evidence and three to five source-backed patterns with anchors 0..4.
Each case optionally names only its relevant runtime references. Core and scope are
always loaded. Equivalent scope module names use `runtime_routes.scope`; framework
and voice routes can be supplied to the structural validator through `--routes`.

`generation` configures the user's authorized chat-completions endpoint URL, generator
model, two judge models, temperature, answer/judge output-token caps, input-token limit,
per-request timeout, fixed Unix `deadline`, and `max_words: 250`. Prefer a different
judge model when available within budget; same-model fresh contexts remain valid with
the dependence recorded. Input limits use UTF-8 bytes as a conservative token bound.
The word check counts CJK characters individually; this conservative bound may require
shorter CJK responses. Endpoint credentials use `PERSONA_API_KEY`, never a saved key.

## Compose the reader's introduction

Once the supported perspective and runtime behavior are established, draft the README
and its first question or illustrative encounter in the same authoring pass. Follow the
reader-facing contract in [output-template.md](output-template.md) and read
[readme-experience.md](readme-experience.md). Match the promise to the actual package;
retain useful existing prose and locally label editorial illustrations. Record only
the status currently supported, then patch status and affected qualifications after
assessment instead of regenerating the README.

A README-only task with unchanged recognition inputs uses the existing assessment
applicability and zero new recognition calls. Skip new plan/ledger initialization and
freezing for that task; check links, status consistency and existing input dependencies.
A newly noticed runtime defect follows the existing scoped repair rules, not an
unrequested rebuild.

## Initialize once, freeze before answers

Prepare a workflow plan that adds `scope`, `affected_modules`, `operation` (`new` or
`upgrade`) and `change_type` (`content` or `formatting`) to the recognition plan.
Paths are relative to the actual runtime root. Store the SQLite workflow in private
scratch; its resumable prompts/runtime snapshots may include machine-local paths.
Publish the portable run artifacts and validation summary, not the scratch database.

```bash
python3 scripts/workflow.py init /path/to/work/workflow.sqlite \
  --runtime /path/to/persona --plan /path/to/work/plan.json
python3 scripts/recognition_runner.py freeze --runtime /path/to/persona \
  --plan /path/to/work/plan.json --workflow /path/to/work/workflow.sqlite \
  --run /path/to/persona/transworld-identity/runs/build-01
python3 scripts/recognition_runner.py run --workflow /path/to/work/workflow.sqlite \
  --run /path/to/persona/transworld-identity/runs/build-01
```

Initialization is exclusive; never reset consumption by replacing the database.
Freeze persists actual runtime/module, profile, source-packet, scenario, rubric and
configuration hashes, with a hash manifest. It creates evidence/profile documents if
absent; existing evidence must match the plan. A supplied profile document is also
frozen and given to judges. Confirm its consistency with the structured profile.
Changing criteria or runtime needs a new run directory, preserving the previous one.

The runner uses six fresh generation contexts with equal task facts, no tools and a
250-word limit backed by output-token caps. The generic control is instructed to answer
competently and sees no persona. Neither receives profile/rubric/test answers. Two fresh
judges see all anonymous pairs in reversed order, frozen evidence and rubric. All output
and scoring details are in [recognition-protocol.md](recognition-protocol.md).

## Budget, failure and reuse

Eight calls total includes retries, delegated calls and repair retests. Reserve a slot
persistently before dispatch. Failed or interrupted reservations remain charged.
Received responses persist immediately. Receipt and content usability are separate:
`output_usable` is unknown until validation, then true or false. Malformed or overlong
responses remain in the original charged call records and are excluded from reuse. A process timeout terminates its HTTP child. Deadline expiry
prevents new dispatch and bounds pending calls; never label an interrupted call complete.
Do not launch extra evaluation planning agents.

Resume the same `run` command; successful matching outputs are reused, not regenerated.
A lost JSON mirror is recovered from the persistent completed call. Use `--retry` only
for inspected failed/missing or unusable attempts within remaining budget. It also
replaces malformed judge JSON or invalid required judge fields, while preserving their
original records under `runs/<id>/attempts/` with hashes and relocation metadata.
At most one replacement per affected item is dispatched per explicit retry invocation;
newly invalid outputs stop that item. A valid failing or inconclusive judgment is usable
and is not resampled by `--retry`. Replacing an invalid response may leave too little
budget to finish recognition; report the remaining gap. There is at most one
repair pass (`workflow.py repair WORKFLOW`), with no extra calls. Once eight are consumed,
record the correction and stale results, then deliver the actual status. Additional
calls need explicit fixed-budget authorization; `authorize-more` records that authorization
without erasing consumption. A deadline extension must also be explicitly configured.

For later separately contracted work, initialize its own ledger and import matching
successful records with `workflow.py import-calls WORKFLOW --source PRIOR_WORKFLOW`.
Imports retain source database hash and call IDs, and are not new calls. Exact request
fingerprints decide reuse. Runtime/scenario/generation changes invalidate affected
answers; profile/rubric/evidence changes invalidate judgments, while unchanged answers
survive. Unrelated unloaded modules do not invalidate answers. A rename-only migration
uses no new generations and records applicability of historical results.

## Complete without model calls

Run `validate_package.py PERSONA` for structure. Prepare a source review JSON with
`summary`, `reviewer`, `reviewed_all_core_claims`, `limitations` and `source_checks`.
Each check has `claim`, `outcome`, `assessment`, `condition_or_exception`, `evidence_ids`,
and exact runtime `dependencies` from the frozen module hashes. Implementation safeguards
are explicitly marked `implementation_safeguard: true`. Review all retained core claims,
not only changed files. Describe machine-assisted editorial review honestly; it is not
an independent historical audit. Missing attribution, quotations or universal conditions
must be corrected or removed before claiming source-grounded status.

```bash
python3 scripts/completion_report.py /path/to/persona \
  --workflow /path/to/work/workflow.sqlite --review /path/to/work/source-review.json \
  --run /path/to/persona/transworld-identity/runs/build-01 \
  --out /path/to/persona/transworld-identity/validation.json
```

Completion recomputes acceptance from saved outputs without model calls. It checks
current runtime, source packet and profile applicability, retains prior validation bytes
in `history/`, and stops dispatch. Source-grounded, machine-recognized and research
outcomes stay separate. `standard_accepted` requires all three current gates to pass;
otherwise deliver `candidate` with visible limitations. Optional `--fidelity` checks a
separate strict research artifact; it cannot replace standard recognition.

Recorded hashes are tamper-evident, not protection against the owner rewriting history.
The ledger cannot count hidden calls outside its API, verify exhaustive source review,
or turn declared context isolation into independent model errors. Unknown token usage
or model identifiers stay unknown. Report actual usage when available; eight calls is
not a token/cost guarantee. Update only README status and qualifications affected by
the results. Explain practical consequences: an unavailable endpoint or exhausted
allowance means the relevant assessment remains incomplete; put the infrastructure
details in the linked assessment record. Preserve Candidate or Standard accepted exactly.

Alongside link and attribution checks, complete the four editorial questions in
[readme-experience.md](readme-experience.md): particularity, encounter, entry and honesty.
Point to concrete passages in the existing completion/provenance record and revise
specific weak passages once within this authoring pass. This is editorial judgment,
not human validation, a personality score or another evaluation round. Correct or
remove material false claims; style uncertainty alone does not restart assessment.
Preserve the introduction and examples unless results materially affect their accuracy.
Then stop. Publication follows existing user authorization, independently of acceptance.
