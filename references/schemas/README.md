# Artifact schemas

Machine-readable [JSON Schema](https://json-schema.org/) (draft 2020-12) definitions for the
intermediate artifacts the pipeline writes to its work directory.

**None of these files are produced by this repository.** They describe artifacts the distiller
generates at runtime, in its work directory (default `persona_work/` — see
[pipeline.md](../pipeline.md)), for one specific corpus. There is no universal `extractions.json`;
shipping one would mean shipping some particular person's extraction output as if it were a
template.

What the repository ships is their *shape*. The schemas exist so those artifacts have one
canonical, validatable form rather than five illustrative snippets scattered across the reference
docs — several of which carry `//` comments for readability and are therefore not parseable as
JSON if copied verbatim.

Some schemas carry worked `examples` blocks. Where a schema and a prose snippet disagree, the
schema is authoritative.

## Standard production contracts

- [evidence.schema.json](evidence.schema.json): situated evidence, stable IDs and curation decisions.
- [recognition-plan.schema.json](recognition-plan.schema.json): finite build contract, cases, profile, evidence and model limits.
- [recognition-judge.schema.json](recognition-judge.schema.json): anonymous pair scores, citations and comparisons.
- [validation.schema.json](validation.schema.json): current hashes, separate gates, budget, lineage and supported claims.

The runner additionally checks cross-record references, exact answer passages, case
coverage, frozen hashes and deterministic acceptance. Schema validity alone cannot
establish source truth, isolation or human recognition. Standard production does not
require the older research-only admission and certification artifacts below.

## Index

| Artifact | Stage | Schema | Prose |
|---|---|---|---|
| `clusters/manifest.json` | 1 — segment | [`clusters-manifest.schema.json`](clusters-manifest.schema.json) | [pipeline.md](../pipeline.md), [acquisition.md](../acquisition.md) |
| `coverage_map.json` | 1 — coverage map | [`coverage-map.schema.json`](coverage-map.schema.json) | [pipeline.md](../pipeline.md), [acquisition.md](../acquisition.md) |
| `registers.json` | 2 — Pass A0 register discovery | [`registers.schema.json`](registers.schema.json) | [extraction.md](../extraction.md) |
| `extractions.json` | 2 — extraction | [`extractions.schema.json`](extractions.schema.json) | [extraction.md](../extraction.md) |
| `scores.json` | 3 — curation audit log | [`scores.schema.json`](scores.schema.json) | [scoring.md](../scoring.md) |
| `fidelity.json` | gate + 5 — verification | [`fidelity.schema.json`](fidelity.schema.json) | [fidelity-tests.md](../fidelity-tests.md) |
| `passages.json` | 1: metadata inventory before extraction | [`passages.schema.json`](passages.schema.json) | script docstring |

`passages.json` is the one artifact you hand *to* a script rather than receive from the pipeline —
`scripts/holdout_split.py` reads it. The grouped v2 output (`split.json`) is checked by the release validator; the
script is its source of truth.

`registers.json` is written by `scripts/register_discover.py`. A handful of its fields are marked
**hand-added** in the schema: the script measures, but naming a register, nominating a default,
ordering a gradient, and noting where a family boundary cuts across a cluster are readings, not
measurements. Those fields are what turn a measurement dump into a decision record, and the file is
not finished until they are filled in.

The two Stage 1 schemas also carry the results of **corpus acquisition**, which runs before Stage 1
when the source is remote: `attribution` plus the optional `source_url` / `retrieved` / `revision`
on each cluster, and the `sources[]` records plus `firsthand_ratio` on the coverage map. See
[acquisition.md](../acquisition.md).

## Constraints the schemas encode

Beyond field types, a few of the skill's hard rules are expressed structurally:

- A cluster requires an **`attribution`** label — `firsthand | secondhand | mixed | unknown`. It is
  required rather than optional because three hard rules read it (expression and modulation
  extraction runs on firsthand clusters only; a projectible regularity needs at least one firsthand
  cluster; cost-refusals and interactional moves attested only secondhand are flagged unverified and
  cannot satisfy the Stage 5 presence assertion), and an absent label defaults in practice to the
  optimistic reading. Making it required means a manifest cannot stay silent about whose words these
  are.
- A `regularity` **or `verdict`** element requires **≥2 clusters** — the corroboration rule from
  Stage 2. A judgment attested once, in an aside, is an aside; it goes to `episodic.md`.
- Element **ids carry a class prefix** — `PROC CR VD PR IM MOD PP` — and the prefix must agree with
  the `type`. A flat `e017` tells a reader nothing, whereas a prefixed id makes the class
  distribution readable by scanning, which is what the minimum-presence assertion and the elevation
  rules both need. The agreement is enforced structurally because a prefix that has drifted from its
  type is worse than no prefix: it is a label a reader will trust.
- A `procedure` element requires `order`, `precondition`, and `on_fail`. The ordering is the whole
  reason procedures are a class of their own — unordered heuristics give a host agent no way to know
  what runs first, so it applies them simultaneously and the guard, whose entire value is firing
  before everything else, never fires at all.
- A `verdict` element requires `object`, `judgment`, and `corpus_hits`.
- A `cost_refusal` element requires `convenient_move`, since the divergence between the convenient
  response and the attested one *is* the signal. It is optional for `interactional`, where a move
  can be characteristic without a convenient counterpart to diverge from.
- Each retained scorer decision requires a `rank`. Admission happens before class priority,
  within-class score, and deterministic ID tie-breaking. `score_elements.py` implements these rules.
- `scores.json` requires the scorer version, input hash, class order, decisions and retained IDs.
  Budget and tokenizer records are optional companion fields in this schema; record them in the
  fidelity ledger whenever allocating runtime space.
- Each `cluster_budgets` entry carries a **`verdict`** — `OK | FLOOR | RECUT | SPLIT_IN_MODULE` —
  rather than the bare `recut_flagged` boolean of 2.x, which could only say that a cluster was
  overloaded and not what to do about it. The distinction matters in one direction only: an
  overloaded cluster spanning two topic domains was mis-segmented and goes back to Stage 1, while an
  overloaded cluster in one domain carried in two registers must *not* be re-cut, because that
  separates a subject from itself. `recut_flagged` is retained, deprecated, so 2.x logs still
  validate.
- `scores.json` also carries **`cluster_budgets`** — one entry per cluster *considered* for a
  `clusters/*.md` module, including any the 1,800 floor rejected. Recording the rejections is the
  point: it turns "this cluster did not earn a module" into an auditable decision rather than an
  omission. Each entry keeps its input counts and an optional realised size, which is the only data
  a future recalibration of the formula's coefficients has to work from.
- `fidelity.json` requires **`content_hash`** and **`stale`**. Curation is a loop, and a result whose
  package has changed underneath it is stale whether or not anyone marked it — the hash makes that
  mechanically checkable rather than a matter of memory.
- All current within-class scores are bounded to 0–1. Optional legacy probe fields use the same bounds.

Some rules are deliberately **not** encoded, because valid records violate them:

- **The 3,000-token core floor** — `budget` is not bounded below by it, because a reduced-scope core
  shipped against a genuinely thin pool is a valid outcome, not a malformed record. What the schema
  does insist on is that the shortfall be *visible*: `floor_triggered` is required.
- **The firsthand requirement on regularities** — the label lives in the manifest and the rule binds
  in `extractions.json`, and no schema can follow a cluster id across files. The enum makes the fact
  recordable; enforcing it is on you.

## Validating

Release validation checks `fidelity.json` and `registers.json` against their declared schemas
before interpreting their contents. Install the release dependency with
`python3 -m pip install -r requirements-release.txt`. Missing dependencies or invalid artifacts
fail release validation. Additional cross-field checks reconcile the register verdict, unit and
family counts, complete family membership, matrix labels, dimensions, numeric values, symmetry
and zero diagonals. Both single-family and multiple-family evidence must pass these checks.

For optional standalone checks of other artifacts:

```bash
pip install check-jsonschema
check-jsonschema --schemafile references/schemas/scores.schema.json path/to/scores.json
```

The scripts that produce these artifacts write shapes that validate as-is:
`register_discover.py --json` against `registers.schema.json`, and `cluster_budget.py --json`
against the `cluster_budgets` item shape in `scores.schema.json`. If one of them stops validating,
the script and the schema have diverged — fix the pair, and do not paste output that does not
validate into a log that claims to.

Release evidence now requires grouped splits made before extraction, paired baseline/item answers and per-result hashes. See [release-evidence.md](../release-evidence.md). Legacy ID-only passage inventories must be regrouped by work or episode; old final scores cannot be relabeled as independent tests.

## Current admission and behavioral contracts

`scores.json` now records the output of `score_elements.py`: class admission and within-class
ranking, not a universal weighted retention score. Existing weight/composite examples are
historical; use [scoring.md](../scoring.md). `fidelity.json` requires the four behavioral gates
in [behavioral-evaluation.md](../behavioral-evaluation.md). `registers.json` requires stability
evidence and permits `INSUFFICIENT_EVIDENCE`; undefined ratios are null, never Infinity.

New recognition plans and validation writes carry `structure_revision: 2`. Recognition
cases require explicit `references`. Standard production includes the complete voice
and framework modules in every case, plus relevant topic modules. The schema and runner
still permit `[]` for core-only diagnostics or historical replay; that capability does
not satisfy the standard authoring contract. The runner does not infer required modules
from the activation entry or route declarations. The optional `assessment_scope` selects
the canonical reconstruction report for frozen, separately hashed judge evidence. Legacy plans are inspected through explicit replay
or migrated with passage review; missing metadata is never silently upgraded.
