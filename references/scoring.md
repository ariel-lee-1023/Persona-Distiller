# Stage 3 — Multi-probe curation & deletion

This is where the value is. The job is to score every candidate from `extractions.json` on five
probes, combine them into one identification score, and then **delete aggressively**. Get this
right before you polish anything else.

## The composite

```
identification = 0.30·projectibility
               + 0.25·cost_refusal
               + 0.20·expressive_match
               + 0.15·interactional
               + 0.10·preoccupation
```

Each sub-score is 0–1. The weights are defaults — tunable, but keep the ordering: the two hardest,
most diagnostic probes (projectibility, cost/refusal) together outweigh everything else. This
ordering *is* the correction against the natural bias toward easily-measured surface style. If you
ever find the core filling with tidy style facts, the weighting is doing its job and you should let
it cut them.

## Scoring each probe (0–1 rubrics)

**Projectibility (0.30)** — does it predict held-out stances?
- 1.0 — from this element alone you can correctly infer the person's position on questions they
  never explicitly addressed; confirmed in the Stage 5 projection test.
- 0.5 — recurs and generalizes somewhat, but predictions are shaky or under-tested.
- 0.0 — reproduces a specific known statement only; no reach beyond it.

**Cost / refusal (0.25)** — does it sit on an incentive-vs-characteristic divergence?
- 1.0 — a documented line the person held against their own audience/interest, with both the
  convenient move and the characteristic move attested.
- 0.5 — a standing commitment that recurs but carried little visible cost.
- 0.0 — no divergence; agrees with what anyone in their position would conveniently say.

**Expressive match (0.20)** — alignment with the *measured* style distribution, including variation.
- 1.0 — a distinctive feature or a modulation *pattern* well outside the generic baseline.
- 0.5 — present but only mildly distinctive.
- 0.0 — a bare average indistinguishable from generic prose. (Most raw metrics land here — that is
  correct, and why this probe is capped at 0.20.)

**Interactional visibility (0.15)** — observable as a move in exchange.
- 1.0 — a repeated, recognizable concede/reframe/dig-in/shift-footing pattern across dialogues.
- 0.5 — appears in exchange but inconsistently.
- 0.0 — never observable interactionally (pure monologue artifact).

**Preoccupation / gravitational weight (0.10)** — the theme they keep returning to.
- 1.0 — surfaces across several *unrelated* clusters; the person cannot stay away from it.
- 0.5 — a recurring interest within one domain.
- 0.0 — mentioned once or twice.

## The deletion rule (hard)

After scoring, cut an element if **any** of these is true:

1. Composite **< 0.55**.
2. It introduces **generic language** — phrasing that would fit a thousand people.
3. It **forces meta-commentary** — you cannot include it without the persona narrating itself,
   hedging, or citing sources.
4. It **conflicts with a higher-scoring** core voice feature — keep the stronger one; drop the
   weaker rather than averaging them into a muddle.

Do not smooth, blend, or "partially include" low-value material. A deleted element that was merely
low-scoring (not generic/meta/conflicting) can still be **demoted to references** if it is attested
and someone might want it on demand — but it does not touch the core. A concrete, attested
incident or decision-record fragment demoted this way goes to `references/episodic.md`; a
demoted expression or modulation element goes to `references/voice.md` instead (see
`output-template.md`).

## Elevation & retention (hard) — why weights alone are not enough

The weights tilt toward the diagnostic signals, but ranking purely by composite still lets *volume*
defeat them: a corpus yields dozens of moderate style features and only a handful of cost-refusals,
so a flat top-N sort can fill the core with tidy generic style while the fingerprints spill into
references. The elevation rules below prevent that. They are not optional flavor — they are the
mechanism that makes the whole design work.

**1. Class priority in ranking.** Do not sort survivors by composite alone. Sort by **class first**,
then by composite within class:

```
cost_refusal  ≈  projectible_regularity   >   interactional   >   variation/modulation
                                                            >   preoccupation   >   stable_style
```

**2. Reserved claim.** Cost-bearing refusals, standing commitments, and variation/modulation
patterns get *first claim* on core space. Fill them in before any stable style feature, then fill
remaining budget down the priority ladder.

**3. Style-metric cap.** Pure style averages (stable_style class) may occupy **at most ~20%** of the
core's elements. If you are over the cap, the surplus style features go to **`references/voice.md`**
regardless of their composite — the core is a fingerprint, not a stylometry report. The cap is a
*routing* rule, not a discard rule: everything above it is kept, in the module built to hold it and
loaded whenever sustained prose is written in the voice. Same for surplus modulation patterns.
Elements cut under the 0.55 rule are still cut; `voice.md` takes the demoted, not the deleted.

**4. Sparsity protection.** A high-signal cost-refusal or variation pattern that clears the ≥2-cluster
bar is retained even if it is rarer than, and outscored on the composite by, an abundant style class.
Count never demotes a scarce diagnostic below a plentiful generic one.

**5. Minimum presence.** If the corpus contains *any* high-signal cost-refusal or interactional move,
the core must carry **at least one**. This is asserted again at the Stage 5 presence check; enforce
it here so it is true by construction, not by luck.

Fill the core to the computed budget (next section) under these rules — see `output-template.md`
for the section layout; everything else attested goes to references.

## The core budget is computed, not fixed

A flat cap is the wrong instrument. The core's job is to carry fingerprints, so its size should
track **how much diagnostic material actually survived curation**, bounded by **what the corpus can
honestly support** — not by a constant that a rich corpus under-uses and a thin one invites padding
to reach. Compute the budget after the survivor set is ranked and before you fill it.

**Step 1 — supply term.** Count survivors slated for the core by class (`n_*` are counts of
survivors of that class, before the budget decides how many are actually written):

```
supply = 2,200
       + 250 × min(n_cost_refusal,  6)     # incl. standing commitments
       + 180 × min(n_projectible,   7)
       + 140 × min(n_interactional, 5)
       + 120 × min(n_variation,     4)
```

Preoccupation and stable_style contribute **nothing**. They never earn space; they fill space the
diagnostics have already earned. Saturation is ~6,140 — a corpus that maxes every term.

**Step 2 — corpus ceiling.** From `coverage_map.json`, first matching row wins:

| condition | ceiling |
|---|---|
| `firsthand_ratio` < 0.50 | **4,000** |
| `total_tokens` < 50k **or** `n_clusters` < 4 | **4,000** |
| `total_tokens` < 250k **or** `n_clusters` < 9 | **5,500** |
| otherwise (≥250k tokens, ≥9 clusters, ≥2 periods in `temporal_spread`) | **6,500** |

**Step 3 — clamp.**

```
core_budget = clamp(supply, floor = 3,000, ceiling)
```

Measure against the rendered `SKILL.md` including frontmatter, ±10% tolerance. Record
`core_budget`, its inputs, and which ceiling row applied at the top of `scores.json`.

Worked: a dialogue-rich 180k-token corpus in 11 clusters yielding 3 cost-refusals, 5 regularities,
3 interactional moves, 2 modulation patterns → supply 2,200+750+900+420+240 = **4,510**, ceiling
5,500 → budget **4,510**. The same curation over a 30k-token corpus → ceiling 4,000 → budget
**4,000**, and the two lowest-ranked survivors go to references.

### The floor (3,000) is a diagnostic trigger, never a padding target

If `supply` lands under 3,000, the survivor pool is too thin to embody the person at full scope. Do
these in order — stop as soon as the pool clears:

1. **Re-examine the 0.45–0.55 cut band**, but only for `cost_refusal`, `projectible`,
   `interactional`, and `variation` candidates. The 0.55 threshold is tuned for an abundant pool; a
   thin pool means it was applied to a pool it was not tuned for. The ≥2-cluster evidence bar stays
   hard — re-scoring is not re-labelling.
2. **Check for under-extraction upstream.** A monologic corpus routinely yields `n_interactional`
   = 0; that is a corpus fact, not a curation failure, and Stage 2 will not find what is not there.
   Confirm against `dialogue_ratio` before assuming the pass was lazy.
3. **Ship a reduced-scope core below the floor.** Narrow what the persona claims in the frontmatter
   description, log the shortfall and the computed `supply` in `fidelity-ledger/provenance.md`, and
   name it in the coverage report.

Never top the core up with `stable_style` material to reach the floor. It would breach the 20% cap,
and it is precisely the failure mode this whole design exists to prevent: a core that is fluent,
correctly sized, and reads like anyone.

## The cluster-module budget is computed too

The core is not the only artifact that needs a size. Each `clusters/*.md` module needs one as well,
and for the same reason: a flat band is a guess that a rich cluster under-uses and a thin one is
invited to pad. Compute these after the demotion decisions are made — a cluster module's budget is a
function of what was routed *to* it.

### What actually drives a module's size

Not the cluster's word count. Measured across a ten-module register package, module length correlated
+0.82 with retained evidence fragments and +0.70 with the cluster's own named constructs, but only
**+0.30 with cluster word count** — and while cluster sizes spanned 9.0×, the modules serving them
spanned 1.37×. A module carries *constructs and moves*, not proportional coverage of the source, so a
short dense cluster needs nearly as much room as a long discursive one. Corpus mass belongs in the
formula as a damped corrective, never as the driver.

### The formula, per cluster

```
supply_c = 600                                    # fixed frame: header block, orientation, sound
         +  90 × min(n_apparatus,     12)         # named constructs whose home is this cluster
         +  90 × min(n_moves,         12)         # argument shapes + interactional moves attested here
         +  85 × min(n_applications,   8)         # distinct situations this cluster is the answer to
         +  30 × min(n_fragments,     24)         # attested evidence passages retained
         +  80 +  15 × min(n_siblings, 9)         # prohibitions, incl. one fence per sibling module
         + 400 × sqrt(words_c / words_firsthand)  # damped corpus-mass corrective

module_budget_c = clamp(supply_c, floor = 1,800, ceiling = 6,000)
```

Counting rules, so these are read off Stage 2/3 artifacts rather than invented at write time:

| input | how to count |
|---|---|
| `n_apparatus` | named constructs in `frameworks.md` whose cluster column names *this* cluster and not the corpus at large |
| `n_moves` | demoted `projectible` + `interactional` elements whose evidence sits in this cluster |
| `n_applications` | distinct entry-situations the module is loaded for — for a persona with a router, the router's fan-in; otherwise the question-shapes this cluster answers better than its siblings |
| `n_fragments` | attested evidence passages retained in the module |
| `n_siblings` | other clusters that also get a module (capped at 9) |
| `words_c`, `words_firsthand` | `clusters/manifest.json` |

`n_siblings` is the term most often missing from hand-written estimates and the one that grows
fastest with corpus richness. A ten-register persona needs every module to fence itself off from nine
others — near-miss terms, borrowed vocabulary, the move that belongs to the next work. A
three-cluster persona needs almost none of that. **The separation cost scales with the number of
siblings, not with the cluster's own size**, which is exactly why a flat band gets worse as the
corpus gets better.

Run `scripts/cluster_budget.py` rather than computing by hand; it also raises the floor and re-cut
flags below.

### The floor (1,800) decides whether the cluster gets a module at all

This is the question `output-template.md`'s "one file per high-value source cluster" never defined.
Below 1,800 the cluster cannot carry a module that is more than a summary. Do **not** pad it. Either:

1. **Fold it into its nearest sibling module** as a subsection, if they share a register or period; or
2. **Demote its concrete, attested material to `episodic.md`** (events, not concepts or expression —
   see `output-template.md`'s episodic scope) and let the core, `frameworks.md`, and `voice.md`
   carry what mattered.

A persona with six clusters and four modules is a normal, honest outcome. Six thin modules is not.

### Cap saturation is a re-cut signal, not a trim signal

The formula saturates around **4,775** — deliberately below the 6,000 ceiling, the same relationship
the core's supply (6,140) has to its ceiling (6,500). So the ceiling only ever catches a hand-written
overrun, and the interesting signal is elsewhere: if `n_apparatus > 12` or `n_moves > 12`, the cluster
is carrying **two registers**, and the fix is upstream. Go back to Stage 1 and re-cut it with
`segment.py` by period or theme. Never buy the space back by deleting evidence — that treats the
symptom (a fat file) and leaves the cause (boundary drift, so one "cluster" averages two voices) in
place.

### Report the runtime load, not the package size

The `clusters/` directory's total is not a constraint; modules load one at a time. What matters is
the worst-case weight of a single exchange:

```
loaded_worst_case = core_budget + 2 × max(module_budget) + voice.md + frameworks.md
```

Two modules because a close secondary ranking may load one. Record this line in
`fidelity-ledger/provenance.md` alongside the core budget.

### Calibration status — read before trusting the constants

The unit prices were fitted against **ten modules from a single corpus** (a 630k-word, ten-register
literary package). On that data the formula lands within a mean 3.8% / max 6.0% of the hand-written
lengths — inside the ±10% tolerance used for the core budget — and an ablation shows every term
earning its place: dropping any one of `n_apparatus`, `n_fragments`, `n_applications`, or the mass
term pushes max error to 9.7–16.2%, and a flat constant (which is what a band amounts to) reaches
18.9%.

That is a defensible set of magnitudes, not a universal constant. Ten points, one corpus, one
language, one genre. Treat the *structure* as settled and the *coefficients* as provisional: when a
run finishes, record the realised module sizes and their inputs in `fidelity-ledger/provenance.md`
so the next calibration has more than one corpus behind it. If a run lands consistently 20%+ off in
one direction across all its modules, the fixed term (600) is the one to move first — it is the
least corpus-invariant part of the formula.

## Gate before assembly

Scoring does not flow straight into Stage 4. Before assembly, run the **projection gate** and **cost
gate** in `fidelity-tests.md`; a failing projection score means you re-curate (down-weight over-fit
elements, promote better-generalizing ones) or narrow scope and re-score, and a cost-gate miss means
you re-include or elevate the missing divergence. Record both outcomes in the persona's
`fidelity-ledger/provenance.md`, and note any weight change they triggered. Only a set that clears
both gates gets assembled.

## Auto-weighting hooks

- Dialogue-rich corpus (`coverage_map.dialogue_ratio` high) → nudge the interactional weight up
  (e.g. 0.15 → 0.20) and renormalize; monologic corpus → nudge it down toward projectibility.
- Narrow user focus → raise the weight of the requested facet and drop off-focus elements even if
  they score well, since they are out of scope for this persona.
- Record any weight change and why, at the top of the audit log, so the run stays reproducible.

## Audit log (`scores.json`)

Every decision is logged with its scores and a one-line reason, so the whole curation is
inspectable and defensible.

```json
{
  "weights": {"projectibility":0.30,"cost_refusal":0.25,"expressive_match":0.20,
              "interactional":0.15,"preoccupation":0.10},
  "weight_notes": "dialogue_ratio 0.35 → interactional 0.15 (unchanged)",
  "core_budget": {
    "supply": 4510, "ceiling": 5500, "ceiling_rule": "total_tokens<250k",
    "budget": 4510, "floor_triggered": false,
    "counts": {"cost_refusal":3,"projectible":5,"interactional":3,"variation":2}
  },
  "cluster_budgets": [
    {"cluster_id":"c03","supply":3310,"budget":3310,
     "counts":{"apparatus":7,"moves":8,"applications":7,"fragments":13,"siblings":9},
     "words":101043,"words_firsthand":630298,
     "floor_triggered":false,"recut_flagged":false},
    {"cluster_id":"c12","supply":1635,"budget":1800,
     "counts":{"apparatus":3,"moves":2,"applications":2,"fragments":4,"siblings":9},
     "words":25212,"words_firsthand":630298,
     "floor_triggered":true,"recut_flagged":false,
     "floor_resolution":"folded into c11's module as a subsection; shares register and period"}
  ],
  "decisions": [
    {"id":"e017","type":"cost_refusal",
     "scores":{"projectibility":0.9,"cost_refusal":1.0,"expressive_match":0.4,
               "interactional":0.8,"preoccupation":0.7},
     "composite":0.80,"decision":"core","rank":2,
     "reason":"incentive-vs-characteristic divergence attested in 3 clusters; predicts well"},
    {"id":"e041","type":"expression",
     "scores":{"projectibility":0.1,"cost_refusal":0.0,"expressive_match":0.5,
               "interactional":0.0,"preoccupation":0.0},
     "composite":0.10,"decision":"cut",
     "reason":"bare sentence-length average; generic; below threshold"}
  ]
}
```

## Two worked examples

**Kept.** A candidate `cost_refusal`: the person repeatedly argues *against* a position their own
readership favors, taking the unpopular side on principle, attested in three clusters, and from it
you can correctly predict their stance on a fresh case. Scores: projectibility 0.9, cost 1.0,
expressive 0.4, interactional 0.8, preoccupation 0.7 → composite **0.80** → **core**, high rank.
This is the kind of element that earns identification.

**Cut.** A candidate `expression`: "uses moderately long sentences, average 22 words." Scores:
projectibility 0.1, cost 0.0, expressive 0.5, interactional 0.0, preoccupation 0.0 → composite
**0.10** → **cut**. Generic and below threshold; a persona built on this reads like anyone. If a
*modulation* version existed ("sentences collapse to clipped fragments the moment a claim is
contested"), that would score far higher on expressive match and interactional and might reach the
core — the pattern individuates where the average does not.
