# Migrating from 2.x to 3.0

## Current executable evaluation contracts

Re-run register discovery on the original units. Current `registers.json` requires observation
and subsample stability evidence; `INSUFFICIENT_EVIDENCE` cannot support release. Do not add a
`stable: true` label to old measurements. Undefined ratios are JSON null.

Rebuild `scores.json` using `scripts/score_elements.py` and the class evidence described in
[scoring.md](references/scoring.md). Old composite scores do not establish current admission.
Budget and tokenizer records can accompany the scorer output, but do not alter its decisions.

Existing projection, position-retention and style results do not satisfy the new behavioral
gates. Collect final reasoning transfer, pressure, historical-scope and blind neighboring-thinker
trials using [behavioral-evaluation.md](references/behavioral-evaluation.md). Run records can be
collected with the optional [evaluation runner](references/evaluation-runner.md). Keep original
evidence and append new results; do not relabel development trials as final evidence.


3.0 changes the shape of three intermediate artifacts, adds required fields to two of them,
introduces a pass that runs before all previously-existing Stage 2 work, and promotes one conditional
test to mandatory.

**Nothing you already shipped is invalid.** A persona package produced under 2.x is a package; it
does not stop being one. What changes is the *log*: the JSON artifacts in a 2.x work directory will
not validate against the 3.0 schemas without a pass, and a 2.x package re-opened for a fold-in will
be missing measurements that 3.0 assumes exist.

Two questions decide how much work this is.

**Are you re-running, or folding in?** If you are re-distilling a corpus from scratch, ignore
everything below except the last section — run 3.0 as written and the artifacts will be right by
construction. If you are folding new material into an existing 2.x package, work through the tables.

**Was the corpus stylistically uniform?** If the body of work is one genre from one period for one
audience, most of 3.0's additions record something you were implicitly asserting anyway, and the
migration is mechanical. If it spans career phases, genres, or audiences, then 3.0 will very likely
tell you the 2.x baseline was an average of two voices — and that is not a field to backfill but a
measurement to redo.

---

## 1. Run Pass A0, even on an existing package

This is the one step that is not a field rename, and it is first because everything else depends on
what it returns.

```bash
python3 scripts/register_discover.py <clusters-or-corpus-dir> --json persona_work/registers.json
```

Then fill in the hand-added fields — family names, the nominated default, any within-family gradient
ordering, and boundaries that cut across clusters. The script measures; those four are readings, and
`registers.json` is unfinished without them. Validate against
[`references/schemas/registers.schema.json`](references/schemas/registers.schema.json).

**If it returns `n_registers = 1`:** record it and continue. Your 2.x pooled baseline was a
legitimate measurement of a single-register corpus, and the rest of this migration is bookkeeping.

**If it returns `n_registers > 1`:** your 2.x style baseline is an average of two or more habits the
person never had, and so is anything derived from it — the avoid-list, the modulation rules, and the
style-match score that passed. Re-measure per family, rebuild `voice.md` §0–§3 from the family
structure, and re-run the style-match test. This is real work, and it is the reason 3.0 is a major
version. The alternative is a persona whose measured voice belongs to nobody.

Then run the discrimination gate, which is no longer optional at `n_registers > 1`:

```bash
python3 scripts/discrimination_test.py sample <clusters-dir> --seed 42 --mask-names --key key.json
python3 scripts/discrimination_test.py score key.json --answers <your blind classifications>
```

Below 0.70, collapse families rather than shipping a distinction the persona cannot perform. If
discovery and this test disagree, **reduce** the family count — do not re-run discovery at a looser
threshold until the numbers come out as hoped.

---

## 2. `extractions.json`

| 2.x | 3.0 | What to do |
|---|---|---|
| `id: "e017"` | `id: "PROC3"`, `"CR2"`, `"VD7"`, `"PR4"`, `"IM1"`, `"MOD2"`, `"PP5"` | Re-id every element with the prefix matching its `type`. The schema enforces agreement, so a mismatch fails loudly rather than quietly. |
| `type: "regularity"` on an ordered method step | `type: "procedure"` + `order`, `precondition`, `on_fail` | Split these out. See below. |
| `type: "regularity"` on a judgment about a named object | `type: "verdict"` + `object`, `judgment`, `corpus_hits` | Split these out. See below. |
| no `register_family` | `register_family: "R1"` | Only meaningful if Pass A0 returned more than one family. |

**Finding the procedures.** Go through your `regularity` elements and ask of each: does this describe
something the person does *before* something else? If yes, it is a procedure, and you now owe three
fields. `order` is its position in the sequence. `precondition` is what has to be true for it to
apply. `on_fail` is what the person does when it does not resolve the question — and this is the field
that will be hardest to backfill, because 2.x never asked for it, so it is frequently not in your
notes. Go back to the corpus for it rather than inventing it. A procedure with a guessed `on_fail`
is worse than one you demote back to `regularity`.

The reason for the requirement is worth restating, since it is what makes the backfill worth doing:
an unordered pile of heuristics gives a host agent no way to know what runs first, so it applies them
simultaneously — and the guard whose entire value was firing before everything else never fires.

**Finding the verdicts.** Ask of each remaining `regularity`: is this a standing judgment about a
*named* object? If yes, it is a verdict, and `corpus_hits` must come from an actual run of
`name_audit.py`, not from memory:

```bash
python3 scripts/name_audit.py --package <package-dir> --corpus <corpus-dir> --json audit.json
```

Verdicts still need ≥2 independent clusters. A judgment attested once, in an aside, stays an aside
and goes to `fidelity-ledger/episodic.md`.

Expect this step to *find* material rather than merely relabel it. Verdicts scored badly under the
2.x rubric — a judgment on a proper name predicts nothing beyond its own object — so the deletion
rule removed them, which is why 2.x packages tended to lose exactly the judgments a reader recognises
fastest, and why the host agent then re-derived a slightly different one on every turn.

---

## 3. `scores.json`

| 2.x | 3.0 | What to do |
|---|---|---|
| no `tokenizer` | **required** | Run `token_count.py` and record what it declares. |
| ceiling ∈ {4000, 5500, 6500} | ceiling ∈ {**4000, 6000, 7500**} | Re-derive from the same coverage-map rows; the thresholds are unchanged, only the values. |
| `supply` without procedure/verdict terms | `+ 200·min(n_procedure,5) + 150·min(n_verdict,8)` | Recompute after step 2. Most 2.x cores come out **larger**, which is the intended correction. |
| `counts` without `procedure` / `verdict` | both present | From step 2. |
| `cluster_budgets[].recut_flagged: true` | `verdict: "RECUT"` or `"SPLIT_IN_MODULE"` | Decide which. See below. `recut_flagged` still validates, as deprecated. |
| no `standing_budgets` | `frameworks.md` / `voice.md` budgets | Compute them; the flat ~4,000 is gone. |
| no `coefficients_source` | `"defaults"` unless overridden | Record it. |

**The `recut_flagged` split is the one judgment call in this table**, and getting it backwards is
costly in a specific way. 2.x had one boolean for two opposite remedies:

- The cluster spans **two topic domains** → it was mis-segmented. **RECUT**: back to `segment.py`.
- The cluster sits in **one domain** but its material arrives in two registers → re-cutting would
  separate a subject from itself. **SPLIT_IN_MODULE**: keep one module, declare an internal A/B
  register split with a no-pooling header, and give separate style guidance for each.

Check `shared_domain` against the cluster's application count rather than by impression, and let
`cluster_budget.py` make the call:

```bash
python3 scripts/cluster_budget.py --single --apparatus 13 --moves 2 --applications 1 \
  --fragments 1 --siblings 0 --words 3000 --words-firsthand 10000 --registers 2 --shared-domain
```

**Do not recompute a 2.x budget and then declare the shipped module compliant with it.** If the
recomputed budget is materially larger, the module is under-built; say so in the ledger. A budget
retrofitted to justify what was already written is not a budget.

---

## 4. `fidelity.json`

| 2.x | 3.0 | What to do |
|---|---|---|
| no `content_hash` | **required** | Hash the package the results describe. |
| no `stale` | **required** (may be `[]`) | An empty array asserts every result matches the current package. Do not assert it lightly. |
| `projection.final.score` only | `+ hit_2`, `hit_1` | If you kept per-item scores, derive them; if not, re-run. |
| no sampling description | `stratified` or `sampling_note` | Required in practice when `stratified` is absent or false. |
| `discrimination` optional | required when `n_registers > 1` | From step 1. Add `required` and, where applicable, `merge_triggered`. |
| pooled style deltas only | `+ by_family` | Only if `n_registers > 1` — and if it is, a healthy pooled delta may be hiding one badly-off family. |

If you cannot derive `hit_2` and `hit_1` from your 2.x records, re-run the projection test rather
than back-filling a plausible ratio. The whole point of the split is that a good aggregate with a low
`hit_2` is a persona that agrees with its subject about every case in the corpus and diverges on the
first case outside it — a fabricated split conceals exactly the diagnosis it exists to produce.

---

## 5. `passages.json`

Bare and wrapped ID lists still validate. To use `--stratify`, move to one of the labelled forms:

```json
{"passages": {"p001": "political philosophy", "p002": "economics", "p003": "religion"}}
```

```json
{"passages": [{"id": "p001", "domain": "political philosophy"}, {"id": "p002", "domain": "economics"}]}
```

Labelling is worth the effort on any corpus whose domains are uneven, which is most of them: a random
mask lands mostly in the largest domain, and the score then gets read as though it described the
persona rather than its biggest topic.

---

## 6. The package itself

Two mechanical checks are new, and both are cheap to run against an existing 2.x package:

```bash
python3 scripts/validate_package.py <package-dir> --json validation.json
python3 scripts/name_audit.py --package <package-dir> --corpus <corpus-dir> --json audit.json
```

Expect findings. `validate_package.py` looks for the defect class that survives careful reading —
ledger material inside a runtime reference, a core load-list pointing at a module nobody wrote, a
near-empty file that does not say why — and none of those look wrong on the page, because there is
nothing on the page to notice. Pass `--headings` with the anchors you require; it is empty by default
so that a core written in the subject's own language is not failed for lacking English headings.

`name_audit.py` will most often flag names your package uses more confidently than the corpus
supports — a tidy label invented during distillation, or lifted from an editor's chapter heading,
which then acquired the authority of the person's own coinage. An editor's heading is not attestation.

Then bring `frameworks.md` and `voice.md` up to the layered templates in
[`references/output-template.md`](references/output-template.md) — `§0–§7` and `§0–§11`. A section the
corpus cannot fill is **marked absent, not deleted**: an absence a reader can see is information, and
a missing heading is not. The ordering in `frameworks.md` is not a filing convention — method and
epistemology come before ontology and verdicts, because a persona handed only conclusions can restate
them and cannot extend them.

---

## Shortest honest path

If you have a 2.x package and limited appetite for this:

1. Run Pass A0. If `n_registers > 1`, stop and decide whether to re-measure. That decision dominates
   everything else, and deferring it means every later number is measured against a fiction.
2. Run `validate_package.py` and `name_audit.py`. Fix what they find.
3. Split out procedures and verdicts, recompute the budgets, and note in the ledger where the
   recomputed budget exceeds what shipped.
4. Add `tokenizer`, `content_hash`, and `stale`. Leave `stale` honest.

Steps 1 and 2 catch the failures that are invisible from the output. Steps 3 and 4 make the next run
reproducible. Doing 3 and 4 without 1 produces a well-documented average of two people.
