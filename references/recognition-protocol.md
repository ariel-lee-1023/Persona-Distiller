# Bounded machine recognition

Prepare cases and a source-backed profile during production. This is an internal
diagnostic suite, not an independent held-out experiment. Freeze/hash all inputs
before observing answers. Later criterion changes create a new version.

The profile contains three to five diagnostic patterns. Each links evidence IDs and
locators to circumstances, observable behavior, acceptable changes/exceptions, concrete
mismatches and why it is more informative than generic clarity or honesty. Include
concrete scoring examples for anchors 0 through 4. Patterns need not be individually
unique to identify a supported constellation.

## Three cases, six answers, two judges

1. A characteristic task with a meaningful choice or reasoning demand.
2. A variation changing one consequential circumstance, with historical background fixed.
3. Disagreement, pressure or interpersonal interaction beyond explanatory prose.

Collectively make all dimensions assessable. Supply fixed facts and stipulated changes
explicitly. Do not copy source questions whose answers are in runtime references.

Generate one persona answer and one competent generic-assistant control per case in
six separate fresh contexts. Give both the same scenario facts, tools and length limit.
Only the persona receives runtime instructions. Neither receives assessment artifacts.
The control must be competent. This comparison does not test a minimal persona prompt.

Request no self-identification. Preserve originals; narrowly conceal remaining literal
identity labels and log the exact transformations. Never edit substance to improve it.

Two fresh judge contexts assess all three anonymous pairs and the changed-condition
relationship. They receive frozen source evidence, profile, rubric and scenarios, with
no build conversation, generator rationale, condition labels or other judge verdict.
Reverse A/B order for judge two. Use a different model if available within the configured
budget; otherwise record same-model fresh contexts without claiming independent errors.

## Dimensions and deterministic rule

Score characteristic reasoning, priorities/tradeoffs, conditional coherence,
interaction/expression and diagnostic specificity. The runner requests both anonymous
slots to avoid disclosing which is the persona; only candidate scores enter acceptance.

| Score | Anchor |
| --- | --- |
| 0 | Contradicts relevant evidence in these circumstances |
| 1 | Mostly generic, superficial imitation or substantial mismatch |
| 2 | Plausible but weakly diagnostic, incomplete or mixed |
| 3 | Clearly supported and recognizable, with minor limitations |
| 4 | Strongly supported, distinctive and well adapted |

Each score needs an exact answer passage, evidence IDs and a concise justification.
Conditional coherence also explains the pair jointly and each answer's contribution.
Each case needs a recognizability preference A, B or tie, with diagnostic evidence.
Names, catchphrases and general answer quality earn no recognition credit alone.
If the actual presented A/B texts are identical (including after identity concealment),
the comparison counts as a tie regardless of judge preference. Preserve the reported
preference and record the effective tie and its reason; identical answers earn no wins.
Missing evidence is `unassessed`, never an invented zero or renormalized pass.

For each judge, `recognition_score = 100 * sum(15 candidate scores) / 60`.
Both judges must independently meet every condition:

- Overall at least 80/100 and every answer at least 15/20.
- Reasoning, priorities, conditional coherence and specificity at least 3 on every case.
- Interaction/expression at least 2 throughout.
- Persona preferred in at least two of three cases; ties are not wins.
- All cases/dimensions assessed and no unresolved material fabrication or fixed-history contradiction.

Keep full score matrices and pairwise reasons. Do not average judges to hide failure.
Both accept: `passed`. Both identify acceptance failure: `failed`. A separately verified
material source/attribution defect also fails. Missing outputs/evidence or acceptance
disagreement: `inconclusive`. No applicable assessment: `not_run`. Do not add a third
judge when one passes and one fails.

The thresholds are provisional engineering choices. 80/100 is not an 80% probability
of human acceptance, and three cases do not establish all-domain performance.

## Frozen records and enforcement

Use [standard-workflow.md](standard-workflow.md) for the executable interface. All
retries, delegates and repair retests share eight calls. No evaluation planning agents.
At most one targeted repair; after eight calls save corrections, invalidate affected
results, and deliver current status without automatic retesting.

Hash actual runtime/modules, profile, source packet, cases, rubric and configuration.
Record generator/judge model identifiers/settings, provider usage when available,
original answers, transformations, scores, evidence citations, budget and lineage.
Unknown provider model/usage stays unknown. A call ceiling is not a token/cost guarantee.

A runtime/reference/scenario/generation change invalidates affected answers. A profile,
evidence-packet or rubric change invalidates judges; unchanged answers remain reusable.
Path-only relocation of identical inputs needs a mapping, not new answers. Old whole-
package research passes stay attached to their original inputs.
