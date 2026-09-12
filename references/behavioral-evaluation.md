# Behavioral release evidence

**Research mode only.** These qualification requirements keep their strict meaning. Ordinary
builds/upgrades follow [standard-workflow.md](standard-workflow.md) and do not dispatch this full
protocol. Comprehensive evaluation needs an explicit request and a fixed shared call budget.
Stop at the limit, preserve inconclusive/failed/partial results and report a working version or
draft separately. References to re-testing below never authorize unbounded retries or test-set
replenishment during standard work.


Position recall, characteristic reasoning, costly commitment, identity recognition,
historical scope and surface style are separate results. A projection score of
.50 consisting entirely of direction-only answers no longer suffices for release:
the independent reasoning gate must also pass. Cost inventory still checks what
was retained, and the pressure gate checks what the generated persona does.

`fidelity.json` now requires `behavioral`, with a current `content_hash` and four
sections. The executable rules live in `scripts/behavioral_checks.py`; the shape
lives in `schemas/fidelity.schema.json`. Numeric floors below are explicit starting
criteria, not calibrated population norms. Keep failed and disputed trials.

## Reasoning and commitment

`reasoning` contains at least two distinct new-situation cases. Each records `id`,
`prompt`, `answer`, `method`, `rationale`, `disputed: false`, and boolean
`criteria.method` and `criteria.conditions`. A hit requires applying the
characteristic method and its execution conditions, not just reaching the familiar
conclusion. At least .70 of cases must pass both criteria.

`commitment` contains at least two cases whose prompts encourage a convenient
alternative. Each records `attested_choice`, `convenient_alternative`, `pressure`,
and the common case fields above. Grade `criteria.costly_choice` and
`criteria.resisted_pressure`; at least .80 must pass both. Use documented
commitments with their original conditions attached, not arbitrary refusals.

The private grading rubric contains the relevant source passages and reasoning
for each expected choice. Prediction receives the scenario and facts, not the
expected result. Generic advice about integrity does not meet a concrete costly
choice criterion. Disputed judgments need human review before release.

## Historical scope

`scope` contains at least three cases covering exactly these `scope_case` values:

- `attested_period`: a documented judgment in its supported period.
- `earlier_period`: a question from an earlier period where a later position must
  not overwrite the earlier one.
- `changed_conditions`: a changed situation requiring a fresh application or an
  explicit extrapolation boundary instead of transferring a standing verdict.

Every case must pass `criteria.period`, `criteria.conditions`, and
`criteria.attribution`. Save the prompt, actual answer, rationale and resolved
review status. A scope file and loading link alone cannot satisfy this gate.

## Blinded identity

`identity.candidates` names the target and at least two plausible neighboring
thinkers. Each task must have one generated answer for every candidate, using
exactly the same prompt and supplied facts. `identity.cases` records `id` (shared
across those candidate answers), `prompt`, `answer`, controller-held `truth`, and
`judgments`. Each answer needs at least two distinct reviewers, with a `choice`
from the candidate list, `blinded: true`, `disputed: false`, and a `rationale`.

Do not disclose which condition generated an answer to reviewers. They receive
candidate names and the same facts, and identify the authorial reasoning. Avoid
prompts that reward recalling a known quotation or slogan. Candidate generation
is symmetric: same model, settings and facts, with the target skill compared
against minimal neighboring-thinker roles. Report this asymmetry in evidence
available to each role; the test establishes discrimination under that setup,
not that the distillation beats equally developed neighbor skills.

The release checker reports accuracy per candidate and the unweighted mean across
candidates. Mean accuracy must be at least .70, with no candidate below .50. It
rejects missing neighbors, differing task facts, repeated reviewer identities or
unblinded judgments. Reviewer agreement is not presumed: retain separate choices.
Report target baseline recognition separately from the target-skill result.

## Runner integration

Follow [evaluation-runner.md](evaluation-runner.md). Task `kind` selects one of the
four behavioral sections above; include its metadata and criterion IDs in the
version 2 suite. Run two blind grade commands with different reviewers, then
`export-persona` to produce a `behavioral` fragment and any projection items.
Use the final partition for release. The runtime hash is captured at prediction;
editing the persona afterward invalidates the result.

A model reviewer is not a human panel. Record whether reviewers were humans or
models, their model/settings when applicable, and uncertainty in the human ledger.
Use human review for disputed source interpretation. The runner's simulated-backend
unit tests establish mechanics; they are not evidence of a real persona's fidelity.
