# Fidelity checks — gates (before assembly) and final verification (after)

These are the empirical answer to "did the distillation actually capture the person, or just produce
a plausible-sounding voice?" Two of them run **twice**, at two different points, and this is the
important structural fact: the projection test and the cost test first run as **mandatory gates
before Stage 4**, where their results feed back into inclusion and weighting; they then run again in
Stage 5 as final verification on the assembled core. All results go into `fidelity.json`, are logged
to the persona's `provenance.md`, and feed the coverage report handed to the user — **never** into
the core.

Everything logged to `provenance.md` under this file is a record for the human reader, not an
instruction for the embodied persona — write scores and caveats as facts about the distillation
("projection score 0.62, single-cluster"), never as a sentence telling the persona what to say when
evidence is thin. See `output-template.md`'s `provenance.md` section for the phrasing rule.

```
Stage 3 scoring ─► GATE: projection test + cost test ─► (fail → re-curate / re-weight, loop)
                                                     └─► (pass) ─► Stage 4 assembly ─► Stage 5 final verify
```

Default thresholds are starting points; record whatever you use.

---

## 1. Held-out projection test  (tests projectible regularities)

The core claim of a good persona is that it can take positions the person never explicitly stated
in the tested passage. This test checks that directly. **Run it first as a pre-assembly gate on the
top-ranked projectible regularities, then again on the assembled core in Stage 5.**

1. From the qualifying passages (those that evidenced projectible regularities and cost-refusals),
   mask **10–15%** using `scripts/holdout_split.py` with a fixed seed so the split is reproducible
   and auditable.
2. From the *remaining* evidence only, predict the person's stance/move on each masked item —
   reason as the persona, not from having seen the answer.
3. Compare each prediction to the masked truth. Score alignment per item
   (2 = correct stance and reasoning, 1 = right direction/wrong reasoning, 0 = miss) and aggregate
   to a 0–1 score.

- **≥ 0.70** — solid; the regularities generalize. Proceed.
- **0.50–0.70** — usable but flag the weak domains in the coverage report.
- **< 0.50** — the regularities are over-fit to specific statements. **As a gate, this fails:** go
  back to Stage 3 and re-curate (down-weight the over-fit elements, promote better-generalizing
  ones), or narrow the persona's claimed scope, then re-score and re-run. Do not proceed to assembly,
  and never ship a confident persona over a failed projection test.

Record the score (overall and per-domain) in `provenance.md`, plus any re-curation or weight change
it triggered. Report per-domain where you can — a persona can project well on its home turf and
poorly elsewhere, and the user needs to know which is which.

## 2. Cost test  (tests refusals / decisions)

The most identification per token lives in incentive-vs-characteristic divergences, and the most
common failure is silently dropping them during curation. This test runs in two forms.

**As a pre-assembly gate:**
1. Enumerate **every** attested divergence pair from Stage 2 (convenient move vs characteristic move).
2. Confirm the high-signal ones **survived curation and are slated for the core** (the elevation
   rules in `scoring.md` should already guarantee this; the gate verifies it).
3. Any high-signal divergence not slated for the core is **re-included or elevated before assembly** —
   or, only if genuinely marginal, **logged** in `provenance.md` with the reason it was left out.

**Presence assertion (final, at Stage 5):** if the corpus contains any high-signal cost-refusal or
interactional move, the assembled core **must contain at least one**. If it does not, delivery is
blocked — return to Stage 3. Enforce the same minimum during elevation so this is true by
construction; the assertion here is the backstop.

Pass condition: no high-signal cost-refusal is absent from the core without a logged justification,
and the minimum-presence assertion holds. A persona that has lost its costly commitments will feel
articulate and generic — these two forms are the guard against exactly that. Log the divergence
inventory and its in-core status to `provenance.md`.

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

## 4. Discrimination test  (tests *claimed internal variation* — conditional)

Run this **only when the persona claims registers**: "in interviews I do X, in essays Y", "before
2015 I held Z", "each work has its own vocabulary". For a single-register persona it does not apply
and is omitted from `fidelity.json`.

Tests 1–3 all ask one question from three angles: does this read like the person? None asks whether
the person's registers can be **told apart** — and that is prior. A generated passage can match the
aggregate baseline perfectly while being indistinguishable from every other register the core
claims, so the style-match test cannot catch this failure. If the registers are not separable in the
source, the modulation rules are decoration: the host agent cannot act on a distinction the corpus
does not support, and the voice will average toward one register whatever the rules say.

1. `scripts/discrimination_test.py sample clusters/ --per-cluster 2 --seed 42 --mask-names --key
   key.json` prints unlabelled passages and writes the answer key to a file.
2. Classify every passage by register signature alone — **before** opening the key.
3. `… score key.json --answers <ids>` scores it and lists the confused pairs.

- **≥ 0.90** — separable; per-register rules are load-bearing. Keep them.
- **0.70–0.90** — usable; name the confusable pairs in the coverage report and merge the worst.
- **< 0.70** — the registers are not distinct in this corpus. **Collapse them** into one honest
  voice and record the decision. A core that promises a distinction it cannot perform is worse than
  one that never claimed it.

Use `--mask-names` and trust that number over the unmasked one. Recognising a cast of characters is
not recognising a register, and a user's utterance will never contain the cast. Read the confusion
list as diagnosis, not noise: a pair confused repeatedly is one register wearing two labels, and the
fix is to merge them in the core rather than to re-run with a different seed.

The ceiling this measures is generous — classifying the subject's own prose is easier than routing a
stranger's sentence — so treat a high score as *the registers carry information*, not as field
accuracy.

---

## `fidelity.json`

Record both phases — the gate result and the final result — so the loop is auditable:

```json
{
  "projection": {
    "gate": {"overall": 0.58, "passed": true, "recurations": 1,
             "note": "1st pass 0.44 (economics over-fit) → re-curated → 0.58"},
    "final": {"overall": 0.74, "by_domain": {"political philosophy":0.82,"economics":0.55}},
    "seed": 42, "n_masked": 12
  },
  "cost": {"total_divergences": 9, "slated_for_core": 9, "in_core_final": 8,
           "logged_out": 1, "missing_unlogged": 0, "presence_assertion": "pass"},
  "style": {"sentence_len_delta": 0.08, "hedge_rate_delta": 0.03,
            "modulation_reproduced": true, "notes": "clipping-under-contest present"},
  "discrimination": {"score": 0.85, "n": 20, "seed": 42, "mask_names": true,
                     "confusable_pairs": ["c07->c01"]}
}
```

Mirror the same facts into `provenance.md` in prose/table form (which core element came from where,
its projection score, and its cost-gate status), so the persona's provenance file is self-contained.

## What goes in the coverage report to the user

A short, honest wrap-up (kept out of the core):

- what the corpus covered well vs. thin domains and temporal gaps (from `coverage_map.json`);
- the fidelity scores in plain terms — the final projection score (and that it cleared the gate),
  whether every high-signal cost-refusal is present, and the style-match result — and where the
  persona should be trusted less;
- if a gate forced re-curation or a **reduced-scope** decision, say so plainly;
- how to improve the persona: which kind of additional material would most raise the weak scores
  (e.g. "more live dialogue would sharpen the interactional moves"; "the 2011–2014 gap makes that
  period unreliable").

This is the release valve for all the honesty the core is not allowed to contain. Use it fully.
