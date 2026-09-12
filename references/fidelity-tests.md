# Fidelity checks — gates (before assembly) and final verification (after)

**Research mode only.** These qualification requirements keep their strict meaning. Ordinary
builds/upgrades follow [standard-workflow.md](standard-workflow.md) and do not dispatch this full
protocol. Comprehensive evaluation needs an explicit request and a fixed shared call budget.
Stop at the limit, preserve inconclusive/failed/partial results and report a working version or
draft separately. References to re-testing below never authorize unbounded retries or test-set
replenishment during standard work.


These are the empirical answer to "did the distillation actually capture the person, or just produce
a plausible-sounding voice?" Two of them run **twice**, at two different points, and this is the
important structural fact: the projection test and the cost test first run as **mandatory gates
before Stage 4**, where their results feed back into inclusion and weighting; they then run again in
Stage 5 as final verification on the assembled core. All results go into `fidelity.json`, are logged
to the persona's `transworld-identity/provenance.md`, and feed the coverage report handed to the user. They stay outside the core and `references/`.

Everything logged to `transworld-identity/provenance.md` is a record for the human reader, not an
instruction for the embodied persona — write scores and caveats as facts about the distillation
("projection score 0.62, single-cluster"), never as a sentence telling the persona what to say when
evidence is thin. See `output-template.md`'s Transworld Identity section for the phrasing rule.

```
Stage 3 scoring ─► GATE: projection test + cost test ─► (fail → re-curate / re-weight, loop)
                                                     └─► (pass) ─► Stage 4 assembly ─► Stage 5 final verify
```

The existing release thresholds are unchanged. Do not lower them to complete a workflow.

---

## 1. Held-out projection test  (tests projectible regularities)

The core claim of a good persona is that it can take positions the person never explicitly stated
in the tested passage. This test checks that directly. **Run it first as a pre-assembly gate on the
top-ranked projectible regularities, then again on the assembled core in Stage 5.**

1. Before extraction, split the metadata inventory by underlying work/episode into train,
   development and final test with `scripts/holdout_split.py`. Related passages never cross
   partitions. Construction and register discovery see train only.
2. Use development items for the pre-assembly gate and repeated curation. Keep target answers
   out of the prediction context. Compare the same model/settings under a minimal persona role
   prompt and the candidate core with permitted references; save both actual answers.
3. Freeze the assembled package, confirm its development gate, then predict on the untouched
   final set in fresh contexts. Score only after predictions are saved. A final failure blocks
   release. Once final evidence guides revision it becomes development, so a new untouched test
   is needed. A fixed seed does not undo exposure or prevent pretraining familiarity.
4. Grade each item 2 for stance and reasoning, 1 for direction only, 0 for a miss. Record both
   conditions' item grades and rationales, overall scores, `hit_2` and `hit_1` separately, and
   per-domain findings. A .50 gate floor still applies; a baseline regression also blocks release.
   A tie does not establish that the distillation adds value.

See [release-evidence.md](release-evidence.md) for isolation, artifacts and the executable
release command. The final set must never supply extracted regularities, refusals or examples.

- **≥ 0.70** — solid; the regularities generalize. Proceed.
- **0.50–0.70** — usable but flag the weak domains in the coverage report.
- **< 0.50** — the regularities are over-fit to specific statements. **As a gate, this fails:** go
  back to Stage 3 and re-curate (down-weight the over-fit elements, promote better-generalizing
  ones), or narrow the persona's claimed scope, then re-score and re-run. Do not proceed to assembly,
  and never ship a confident persona over a failed projection test.

Record the score (overall, `hit_2`/`hit_1`, and per-domain) in `transworld-identity/provenance.md`,
plus any re-curation or weight change it triggered. Report per-domain where you can — a persona can
project well on its home turf and poorly elsewhere, and the user needs to know which is which.

**Describe the sampling, always.** A score whose sampling is not described is a number without a
denominator. State how many items were masked, how the mask was distributed across topic domains,
and — when the mask fell mostly inside the corpus's strongest domain, which is the default outcome
of random masking over an uneven corpus — say so, and give an honest expectation for the domains it
did not reach. `scripts/holdout_split.py --stratify` distributes the mask across domains instead;
prefer it, and when you cannot (too few items in a domain to stratify), record that reason rather
than reporting the unstratified score as though it covered everything.

## 2. Cost test  (tests refusals / decisions)

The most identification per token lives in incentive-vs-characteristic divergences, and the most
common failure is silently dropping them during curation. This test runs in two forms.

**As a pre-assembly gate:**
1. Enumerate **every** attested divergence pair from Stage 2 (convenient move vs characteristic move).
2. Confirm the high-signal ones **survived curation and are slated for the core** (the elevation
   rules in `scoring.md` should already guarantee this; the gate verifies it).
3. Any high-signal divergence not slated for the core is **re-included or elevated before assembly** —
   or, only if genuinely marginal, **logged** in `transworld-identity/provenance.md` with the reason it
   was left out.

**Presence assertion (final, at Stage 5):** if the corpus contains any high-signal cost-refusal or
interactional move, the assembled core **must contain at least one**. If it does not, delivery is
blocked — return to Stage 3. Enforce the same minimum during elevation so this is true by
construction; the assertion here is the backstop.

Pass condition: no high-signal cost-refusal is absent from the core without a logged justification,
and the minimum-presence assertion holds. A persona that has lost its costly commitments will feel
articulate and generic — these two forms are the guard against exactly that. Log the divergence
inventory and its in-core status to `transworld-identity/provenance.md`.

## 3. Style-match test  (tests expression rules)

1. Generate a few sample passages under the core's expression rules **plus `references/voice.md`**,
   on topics the corpus covers, including at least one *contested* prompt so modulation is
   exercised, and at least one passage long enough to drift (400+ words — the failure this test
   exists to catch is a voice that is right for three sentences and generic by the twelfth).
2. Run `scripts/style_metrics.py` on those samples — `scripts/zh_metrics.py` for a Chinese
   corpus, with the same flags used for the `voice.md` baseline, or the comparison is meaningless.
3. Compare the feature distributions against held-out **original** samples (set some aside in
   Stage 2 for this). Look at sentence-length shape, hedge/booster rates, punctuation rhythm, and —
   importantly — whether the *modulation* reproduces (do the samples tighten under contest the way
   the originals do?).
4. Check the avoid-list holds: none of `voice.md`'s "What I never write" items should appear in the
   generated samples. This is a cheap, binary check and it catches drift the distributions blur.

Test the pair as it will actually be used. The core alone is the *framing* configuration; the
sustained-prose configuration is core + `voice.md`, and that is what the promise of embodiment is
measured against. If it helps localize a failure, run the core alone as a control — a large gap
that closes when `voice.md` loads means the module is doing its job, not that the core is broken.

Report divergence qualitatively and on the key numbers. Large gaps mean the expression rules are
wrong or too generic — revise `voice.md` first (it holds most of the system), then the "How I
sound" section. Small gaps on averages but a missing modulation pattern is a real failure even if
the averages match, because the modulation is the individuating part. `voice.md`'s measured
baseline block should be the same numbers this test compares against; if they disagree, the module
was written from estimates rather than from a run — fix that before reading anything into the gap.

## 4. Discrimination test  (tests register separability — mandatory whenever `n_registers > 1`)

**The trigger changed in 3.0.** This test used to run "only when the persona claims registers",
which put the gate downstream of the distiller's own judgment: the check fired only if someone had
already noticed the thing the check exists to detect. It now runs whenever
`registers.json` reports `n_registers > 1` — a fact produced by measurement in Stage 2 Pass A0, not
a claim. It is also **triggered by any cluster merge**, because a merge is precisely the operation
that can pool two registers into one module without anyone deciding to.

For a corpus that `register_discover.py` returns as `SINGLE_REGISTER`, this test is omitted from
`fidelity.json` and the distance matrix stands in its place as the evidence. After a
merge that leaves only one family, recheck that matrix and record `merge_review`;
a one-label discrimination score would be meaningless.

The two tools are a pair and the order matters: **`register_discover.py` proposes, the
discrimination test disposes.** The first says "these units look like k families by their
measurements"; the second says "a reader given an unlabelled passage can actually tell them apart".
When the second disagrees with the first, **reduce the number of families** — merge the confused
pair and re-run. Do not re-run the discovery step with a different threshold until the numbers come
out the way you expected; that is fitting the instrument to the answer.

Tests 1–3 all ask one question from three angles: does this read like the person? None asks whether
the person's registers can be **told apart** — and that is prior. A generated passage can match the
aggregate baseline perfectly while being indistinguishable from every other register the core
claims, so the style-match test cannot catch this failure. If the registers are not separable in the
source, the modulation rules are decoration: the host agent cannot act on a distinction the corpus
does not support, and the voice will average toward one register whatever the rules say.

1. `scripts/discrimination_test.py sample clusters/ --registers registers.json --per-cluster 2 --seed 42 --mask-names --key
   key.json` prints unlabelled passages and writes the answer key to a file.
2. Classify every passage by register-family ID (`R1`, `R2`), not cluster identity, using register signature alone — **before** opening the key.
3. `… score key.json --answers <R1 R2 ...> --json discrimination-result.json` scores it and lists the confused pairs.

- **≥ 0.90** — separable; per-register rules are load-bearing. Keep them.
- **0.70–0.90** — usable; name the confusable pairs in the coverage report and merge the worst.
- **< 0.70** — the registers are not distinct in this corpus. **Collapse them** into one honest
  voice and record the decision. A core that promises a distinction it cannot perform is worse than
  one that never claimed it.

Use `--mask-names` and trust that number over the unmasked one. Recognising a cast of characters is
not recognising a register, and a user's utterance will never contain the cast. Read the confusion
list as diagnosis, not noise: a pair confused repeatedly is one register wearing two labels, and the
fix is to merge them in the core rather than to re-run with a different seed.

The mapping comes from `registers.json` families and `units[].clusters`. Two works in one
family have the same answer. A source mapped to multiple families is rejected: sample homogeneous
units or recut it. Record confusions between families, not between source works.

Also run a behavioral selection test on novel audience/task/stakes prompts with no source-title
or cast cues. Cover every family, save the generated answer and selected family, and grade which
family the answer actually realizes. Record this separately as `register_selection`; a correct
label without the matching generated behavior is a miss. See `release-evidence.md`.

The ceiling this measures is generous — classifying the subject's own prose is easier than routing a
stranger's sentence — so treat a high score as *the registers carry information*, not as field
accuracy.

---

## 5. Re-test obligation (applies to every test above)

Curation is a loop, not a pass. A gate sends the set backwards; clusters get merged; an element is
demoted two batches after the score that justified keeping it. Nothing in the skill previously said
what happens to a score when the thing it measured changes underneath it, so the default was that
nothing happened: the number stayed in `fidelity.json`, still labelled as this package's score,
now describing a package that no longer exists. Two rounds of un-re-tested edits stacked on top of
each other is the commonest way a package's reported fidelity quietly stops being true, and it
leaves no trace at all in a static results table.

The rule:

1. **Any change to the curated set or the assembled package invalidates the tests it touched.** Mark
   them stale immediately, in `fidelity.json`'s `stale` array, at the moment of the change — not at
   the end, when it will be forgotten.
2. **`fidelity.json` carries a `content_hash`** over the package files each result was computed
   against. A result whose hash does not match the current package is stale whether or not anyone
   marked it, and this is mechanically checkable.
3. **A reduced-scope decision must be re-tested, not merely recorded.** Narrowing what the persona
   claims is a legitimate response to a failed gate, but it only works if the narrowed persona then
   *passes* — otherwise the narrowing is an assertion, not a fix. Re-run the failed gate against the
   reduced scope and record the passing score.
4. **What can ship stale:** nothing that gated assembly. A stale style-match result may ship if the
   staleness is stated in the coverage report; a stale projection or cost gate may not.
5. **The batch log in `provenance.md` carries a mandatory `Not re-tested` field** for exactly this
   reason. "None" is a valid entry only when the gates were actually re-run.

---

## `fidelity.json`

The authoritative release format and commands are in
[release-evidence.md](release-evidence.md) and
[schemas/fidelity.schema.json](schemas/fidelity.schema.json). Record per-result hashes,
both development and final item answers/grades, the paired baseline, grouped split hashes,
register-family mapping, cost presence, style and register selection results. Mirror the same
facts into the human ledger. Structural validation without `--release` is a draft check only.

## What goes in the coverage report to the user

A short, honest wrap-up (kept out of the core):

- what the corpus covered well vs. thin domains and temporal gaps (from `coverage_map.json`);
- the fidelity scores in plain terms — the final projection score (and that it cleared the gate),
  whether every high-signal cost-refusal is present, and the style-match result — and where the
  persona should be trusted less;
- if a gate forced re-curation or a **reduced-scope** decision, say so plainly — and give the
  post-narrowing score, since a reduced scope that was never re-tested is a claim rather than a fix;
- any result currently marked stale, and what changed underneath it;
- the register finding: how many families the corpus contains, or, for a single-family package,
  that the distance matrix was computed and supports pooling;
- how to improve the persona: which kind of additional material would most raise the weak scores
  (e.g. "more live dialogue would sharpen the interactional moves"; "the 2011–2014 gap makes that
  period unreliable").

This is the release valve for all the honesty the core is not allowed to contain. Use it fully.

## Behavioral gates and executable workflow

Projection remains a recall/stance comparison and cost remains an inventory check. Neither
substitutes for the required [behavioral gates](behavioral-evaluation.md): method application on
new situations, commitments under pressure, blind identity discrimination against neighboring
thinkers, and historical-scope behavior. `validate_package.py --release` enforces these separately.
Use [evaluation-runner.md](evaluation-runner.md) for isolated prediction, actual retrieval
capture, blind grading and human review. Final cases never feed construction or development.
