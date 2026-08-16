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

### Scoring the two classes added in 3.0

`procedure` and `verdict` are scored on the same five probes, but two of the rubrics need a
reading that is not obvious from the text above, and getting it wrong systematically underrates
both classes.

**`procedure` elements** — ordered method: a guard, a translation rule, a routing row.
- *Projectibility* is the probe that matters, and it should score high almost by construction: a
  procedure that does not generalise to an unseen question is not a procedure, it is a description
  of one answer. Score it against unseen **question types**, not unseen topics.
- *Interactional visibility* is often 0.0 for a guard that fires before the exchange begins. That
  is correct and is not a reason to drop the element; the class priority below protects it.
- A procedure with no stated position in the sequence is not admissible as `procedure`. Send it
  back as a `projectible_regularity` or reclassify it.

**`verdict` elements** — a stable judgment on a named object.
- *Projectibility* here means something narrower than for other classes: not "does it predict
  other stances" but "is it stable across the corpus". A verdict restated consistently in three
  clusters scores 1.0 even though it predicts nothing beyond its own object. This is deliberate.
  A store of settled cases is worth having precisely because it is *not* re-derived, and scoring
  it on reach would delete the whole class.
- *Cost / refusal* is scored normally, and often high: the verdicts worth storing are usually the
  ones that cost the person something to hold.
- A verdict must record its corpus hit count (`scripts/name_audit.py`) alongside its score. A
  judgment attested once, in an aside, is an aside — demote it to `episodic.md`.
- A verdict that could not have been produced by the person's own method layer is a remembered
  conclusion rather than a judgment. Keep it if it is well attested, but flag it in the ledger;
  it will not generalise, and a host agent that treats it as exemplary will misjudge the next
  object of the same kind.

## The deletion rule (hard)

After scoring, cut an element if **any** of these is true:

1. Composite **< 0.55**.
2. It introduces **generic language** — phrasing that would fit a thousand people.
3. It **forces meta-commentary** — you cannot include it without the persona narrating itself,
   hedging, or citing sources.
4. It **conflicts with a higher-scoring** core voice feature — keep the stronger one; drop the
   weaker rather than averaging them into a muddle.

Do not smooth, blend, or "partially include" low-value material. A deleted element that was merely
low-scoring (not generic/meta/conflicting) can still be **demoted** if it is attested and someone
might want it on demand — but it does not touch the core. A concrete, attested incident or
decision-record fragment demoted this way goes to `fidelity-ledger/episodic.md`; a demoted
expression or modulation element goes to `references/voice.md` instead (see `output-template.md`).

## Elevation & retention (hard) — why weights alone are not enough

The weights tilt toward the diagnostic signals, but ranking purely by composite still lets *volume*
defeat them: a corpus yields dozens of moderate style features and only a handful of cost-refusals,
so a flat top-N sort can fill the core with tidy generic style while the fingerprints spill into
references. The elevation rules below prevent that. They are not optional flavor — they are the
mechanism that makes the whole design work.

**1. Class priority in ranking.** Do not sort survivors by composite alone. Sort by **class first**,
then by composite within class:

```
procedure  ≈  cost_refusal  ≈  verdict  ≈  projectible_regularity
                                >   interactional   >   variation/modulation
                                >   preoccupation   >   stable_style
```

`procedure` joins the top band because it is the only class that tells the host agent what to do
*first*; a core full of positions with no ordered method has no way to reach a position on
anything the corpus did not already contain. `verdict` joins it because a settled case that gets
re-derived at runtime is the most detectable failure mode a persona has — the answer changes
slightly every turn, in a way no individual answer looks wrong.

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
       + 200 × min(n_procedure,     5)     # guard, translation rule, routing rows
       + 150 × min(n_verdict,       8)     # the roll-up costs less per entry than a rule
       + 140 × min(n_interactional, 5)
       + 120 × min(n_variation,     4)
```

Preoccupation and stable_style contribute **nothing**. They never earn space; they fill space the
diagnostics have already earned. Saturation is ~8,340 — a corpus that maxes every term.

The two new terms are priced differently on purpose. A procedure costs more per element than a
refusal because it has to be written as an ordered move with its precondition attached, and the
routing table it feeds carries a row of framing per entry. A verdict costs less because verdicts
amortise: the first one pays for the section and the lookup convention, and each additional one is
a line. The caps reflect what a core can carry before the reader stops finding anything —
eight verdicts scan; twenty are a reference table and belong in `frameworks.md` §4 with only the
roll-up in the core.

**Step 2 — corpus ceiling.** From `coverage_map.json`, first matching row wins:

| condition | ceiling |
|---|---|
| `firsthand_ratio` < 0.50 | **4,000** |
| `total_tokens` < 50k **or** `n_clusters` < 4 | **4,000** |
| `total_tokens` < 250k **or** `n_clusters` < 9 | **6,000** |
| otherwise (≥250k tokens, ≥9 clusters, ≥2 periods in `temporal_spread`) | **7,500** |

The two richer rows moved up by 500 and 1,000 in 3.0 to absorb the mandatory slots added to the
core template — the axis, the three-part question-reading procedure, the vocabulary throttle, the
stop condition, and a loading contract that grew from four lines to five parts. The thin-corpus
rows did not move: a corpus that cannot support the diagnostics does not get more room to say so
in.

**Step 3 — clamp.**

```
core_budget = clamp(supply, floor = 3,000, ceiling)
```

Measure against the rendered `SKILL.md` including frontmatter, **in tokens counted by
`scripts/token_count.py`**, ±10% tolerance. Record `core_budget`, its inputs, the ceiling row that
applied, and the tokenizer constants used, at the top of `scores.json`. Word counts are not a
substitute: the ratio of tokens to words differs by roughly a factor of two between an English and
a Chinese corpus, so a package budgeted in words is systematically mis-sized in one direction or
the other, and nothing in the pipeline would report it.

Worked: a dialogue-rich 180k-token corpus in 11 clusters yielding 3 cost-refusals, 5 regularities,
2 procedures, 4 verdicts, 3 interactional moves, 2 modulation patterns → supply
2,200+750+900+400+600+420+240 = **5,510**, ceiling 6,000 → budget **5,510**. The same curation over
a 30k-token corpus → ceiling 4,000 → budget **4,000**, and the lowest-ranked survivors go to
references.

### When supply exceeds the ceiling

The 0.55 deletion rule governs Stage 3; it says nothing about Stage 4, where the material has
already survived and the constraint is space rather than quality. Without a rule for this case a
distiller improvises, and the improvisation is almost always the same one: compress every section
a little. That is the worst available option — it degrades the sections that carry identification
in order to preserve the ones that do not.

Relocate in this order, stopping when the core fits:

1. **`stable_style` surplus → `voice.md`.** Every style element beyond the two or three most
   identifying ones. The 20% cap is an upper bound, not a target.
2. **`preoccupation` beyond the first → `voice.md` §8 or the ledger.** A second preoccupation is
   almost never doing work the first is not.
3. **`verdict` entries beyond the roll-up → `frameworks.md` §4.** The core keeps the lookup
   directive and the bare list of settled objects; the judgments themselves live in the module.
   This is usually the largest single recovery available and it costs nothing at runtime, because
   the loading contract already routes the host agent to §4 before it reasons about a named object.
4. **Routing-table rows → the cluster module they route to.** Keep the guard, the translation rule,
   and the highest-fan-in rows.
5. **Only then, compress prose** — and compress within a section, never across the ladder.

What may never be relocated to make room: the axis, the guard, the minimum cost-refusal, the
vocabulary throttle, the stop condition, or any part of the loading contract. If the core still
does not fit after step 5, the ceiling row is wrong for this corpus or the curation kept too much;
record which, in the ledger.

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
         + 220 × max(n_registers - 1,  0)         # internal register split: header, no-pool line,
         |                                        #   and a second column of style guidance (cap 3)
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
| `n_registers` | how many register families from `registers.json` have material inside this cluster (capped at 3) |
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
2. **Demote its concrete, attested material to `fidelity-ledger/episodic.md`** (events, not concepts
   or expression — see `output-template.md`'s episodic scope) and let the core, `frameworks.md`, and
   `voice.md` carry what mattered.

A persona with six clusters and four modules is a normal, honest outcome. Six thin modules is not.

### Cap saturation is a re-cut signal, not a trim signal

The formula saturates around **5,215** — deliberately below the 6,000 ceiling, the same relationship
the core's supply has to its own ceiling. So the ceiling only ever catches a hand-written overrun,
and the interesting signal is elsewhere: if `n_apparatus > 12` or `n_moves > 12`, the cluster is
carrying **two registers**. Never buy the space back by deleting evidence — that treats the symptom
(a fat file) and leaves the cause in place.

There are two legitimate fixes, and the choice between them turns on a single question: **do the
two registers cover the same topic domain?**

- **No — RECUT.** The cluster spans two domains as well as two registers, and the boundary drifted.
  Go back to Stage 1 and re-cut with `segment.py` by period or theme. This is the default.
- **Yes — SPLIT_IN_MODULE.** Two registers, one domain: the same subject matter handled in a
  written register in one source and a spoken one in another. Re-cutting here is the wrong
  instrument, because the two halves would each need the full prohibition frame against all the
  same siblings, and fencing cost is the term that grows fastest with sibling count. Instead the
  module stays one file and declares the split internally: a header naming both registers with the
  measurements that distinguish them, an explicit line that the two sets of statistics must never
  be pooled, and style guidance listed separately per side. Pass `--registers 2 --shared-domain` to
  `scripts/cluster_budget.py`, which prices the extra frame and reports the verdict as
  `SPLIT_IN_MODULE` instead of `RECUT`.

"Same topic domain" is checked against the cluster's `n_applications`, not against intuition: if
the two sides answer the same entry-situations, it is one domain.

### Report the runtime load, not the package size

The `clusters/` directory's total is not a constraint; modules load one at a time. What matters is
the worst-case weight of a single exchange:

```
loaded_worst_case = core_budget + 2 × max(module_budget) + voice.md + frameworks.md
```

Two modules because a close secondary ranking may load one. Record this line in
`fidelity-ledger/provenance.md` alongside the core budget.

## The standing modules are computed too

Until 3.0 the two standing modules were the last place in the skill where a size was a guess: both
`frameworks.md` and `voice.md` carried a soft ~4,000 band while the core and every cluster module
were computed from what survived. The band was wrong in both directions at once — it under-served
a person with a large apparatus and it invited padding in a person with a small one — and it was
self-contradictory besides, since the skill's own argument against flat bands applies to these two
files more strongly than to the clusters, whose sizes at least vary with their source.

**`frameworks.md`.** The driver is populated layers and entries, not corpus mass:

```
supply_f = 700                                    # §0 operating note + section frames
         + 120 × min(n_constructs,   20)         # §3 entries: definition + clusters + hit count
         + 200 × min(n_procedure,     6)         # §1 entries carry order and precondition
         + 130 × min(n_epistemic,     6)         # §2
         +  90 × min(n_verdict,      24)         # §4 — one line each once the frame is paid for
         + 110 × min(n_moves,        10)         # §5
         +  70 × min(n_personal,      6)         # §6
         +  25 × min(n_constructs,   40)         # §7 index row per named construct

frameworks_budget = clamp(supply_f, floor = 2,000, ceiling = 7,000)
```

**`voice.md`.** The driver is the number of register families, because a family is not a section —
it is a column in the gap table, a set of guardrails, a tag on every rule, and its own anti-drift
pairs. This is why the old flat band failed hardest on exactly the packages that needed the file
most:

```
supply_v = 600                                    # §0 frame + §11 measurement provenance
         + 550 × min(n_registers,     4)         # per family: identification line, guardrails,
         |                                        #   gap-table column, its own opening/closing set
         + 250 × (1 if any within-family gradient else 0)   # §1
         +  90 × min(n_rules,        18)         # §5 + §7 construction and modulation rules
         +  40 × min(n_avoid,        25)         # §6, quantified and family-tagged
         + 120 × min(n_pairs,         8)         # §10 anti-drift pairs
         +  60 × min(n_nopool_pairs,  6)         # §3

voice_budget = clamp(supply_v, floor = 2,000, ceiling = 7,000)
```

Both clamp to the same range, and both saturate below their ceiling (5,000 and 5,190) for the same
reason the cluster formula does: the ceiling should only ever catch a hand-written overrun, never a
legitimately rich module.

The floor here means something different from the cluster floor. A cluster below its floor does not
get a module at all. A standing module below 2,000 gets written anyway — there is nowhere else for
its material to go — but the shortfall is a finding: it means the corpus supports very little
apparatus, or very little measurable expression, and that belongs in the coverage report and in the
package's negative-space section rather than being padded out of sight.

### Calibration status — read before trusting the constants

The unit prices were fitted against **ten modules from a single corpus** (a 630k-word, ten-register
literary package). On that data the formula lands within a mean 3.8% / max 6.0% of the hand-written
lengths — inside the ±10% tolerance used for the core budget — and an ablation shows every term
earning its place: dropping any one of `n_apparatus`, `n_fragments`, `n_applications`, or the mass
term pushes max error to 9.7–16.2%, and a flat constant (which is what a band amounts to) reaches
18.9%.

That is a defensible set of magnitudes, not a universal constant. Ten points, one corpus, one
language, one genre. Treat the *structure* as settled and the *coefficients* as provisional. If a
run lands consistently 20%+ off in one direction across all its modules, the fixed term (600) is
the one to move first — it is the least corpus-invariant part of the formula.

The standing-module and register coefficients above are weaker still: they were set by the same
reasoning about what each structural element costs, and they have not been fitted against anything.
They are stated as formulas rather than bands because a formula can be corrected by data and a band
cannot.

**Recording a run so the next calibration has something to work with.** Guessed coefficients only
stop being guesses if runs are recorded, and a run is only comparable if the constants it used are
recorded with it. Every run therefore writes three things into `fidelity-ledger/provenance.md` §1
and §3:

1. The **coefficient set actually used** — `python3 scripts/cluster_budget.py --emit-coefficients`
   dumps it as JSON. A run that overrode constants with `--coefficients FILE` records the override
   and the reason.
2. The **tokenizer constants** from `scripts/token_count.py`, since every budget is denominated in
   its output.
3. The **realised sizes** of every module beside its computed budget — the residual, per module, is
   the entire dataset. Without it a package contributes nothing to the next fit.

This is the only feedback path the skill has: the tools cannot learn from a package that did not
write down what they told it.

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
  "tokenizer": {"script":"token_count.py","tokens_per_han_char":1.67,"tokens_per_latin_word":1.3},
  "n_registers": 3,
  "core_budget": {
    "supply": 5510, "ceiling": 6000, "ceiling_rule": "total_tokens<250k",
    "budget": 5510, "floor_triggered": false, "over_ceiling": false,
    "counts": {"cost_refusal":3,"projectible":5,"procedure":2,"verdict":4,
               "interactional":3,"variation":2}
  },
  "standing_budgets": {
    "frameworks": {"supply":4270,"budget":4270,"realised":4180},
    "voice": {"supply":4310,"budget":4310,"realised":4395}
  },
  "cluster_budgets": [
    {"cluster_id":"c03","supply":3310,"budget":3310,"realised":3260,
     "counts":{"apparatus":7,"moves":8,"applications":7,"fragments":13,"siblings":9,
               "registers":1},
     "words":101043,"words_firsthand":630298,
     "verdict":"OK"},
    {"cluster_id":"c06","supply":4995,"budget":4995,"realised":5010,
     "counts":{"apparatus":13,"moves":9,"applications":6,"fragments":19,"siblings":9,
               "registers":2},
     "words":74110,"words_firsthand":630298,
     "verdict":"SPLIT_IN_MODULE",
     "verdict_note":"two registers, one topic domain; internal A/B split with no-pooling header"},
    {"cluster_id":"c12","supply":1635,"budget":1800,
     "counts":{"apparatus":3,"moves":2,"applications":2,"fragments":4,"siblings":9,
               "registers":1},
     "words":25212,"words_firsthand":630298,
     "verdict":"FLOOR",
     "floor_resolution":"folded into c11's module as a subsection; shares register and period"}
  ],
  "coefficients_source": "defaults (cluster_budget.py --emit-coefficients recorded in provenance)",
  "decisions": [
    {"id":"CR1","type":"cost_refusal",
     "scores":{"projectibility":0.9,"cost_refusal":1.0,"expressive_match":0.4,
               "interactional":0.8,"preoccupation":0.7},
     "composite":0.80,"decision":"core","rank":2,
     "reason":"incentive-vs-characteristic divergence attested in 3 clusters; predicts well"},
    {"id":"PROC1","type":"procedure","order":1,
     "scores":{"projectibility":0.9,"cost_refusal":0.3,"expressive_match":0.2,
               "interactional":0.0,"preoccupation":0.4},
     "composite":0.51,"decision":"core","rank":1,
     "reason":"the opening guard; interactional 0.0 is expected for a pre-exchange check, and class priority carries it despite the composite"},
    {"id":"VD3","type":"verdict","object":"<named object>","corpus_hits":11,
     "scores":{"projectibility":1.0,"cost_refusal":0.7,"expressive_match":0.3,
               "interactional":0.2,"preoccupation":0.5},
     "composite":0.68,"decision":"frameworks",
     "reason":"stable across 4 clusters; beyond the core's roll-up, so §4 holds the judgment"},
    {"id":"MOD7","type":"expression",
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
