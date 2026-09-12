# Independent evaluation and release evidence

**Research mode only.** These qualification requirements keep their strict meaning. Ordinary
builds/upgrades follow [standard-workflow.md](standard-workflow.md) and do not dispatch this full
protocol. Comprehensive evaluation needs an explicit request and a fixed shared call budget.
Stop at the limit, preserve inconclusive/failed/partial results and report a working version or
draft separately. References to re-testing below never authorize unbounded retries or test-set
replenishment during standard work.


Read this before Stage 1 and again before release. The JSON checks bind recorded
results to exact files. They cannot establish that a model context was isolated,
that a source grouping is historically correct, or that a grader was honest.
Preserve the actual prompts, answers, grading rationales and context manifests.
Never manufacture scores to satisfy a validator.

## Split before construction

Create a metadata-only inventory before reading for traits or refusals:

```json
{"passages": [
  {"id": "p001", "group": "work-or-episode-a", "domain": "ethics"},
  {"id": "p002", "group": "work-or-episode-b", "domain": "ethics"},
  {"id": "p003", "group": "work-or-episode-c", "domain": "ethics"}
]}
```

All excerpts, translations and retellings of the same work or episode share a
group. Use stable IDs and a source locator inventory. Assign groups from provenance,
not from the traits the evaluation should discover. Three groups is a mechanical
minimum, not a recommendation for adequate test power.

```bash
python3 scripts/holdout_split.py passages.json --seed 42 --frac .12 --dev-frac .15 --out split.json
```

The fractions allocate whole groups; report realized passage counts and domain
coverage. Optional `--stratify` allocates within consistent group domains; thin
strata stay in training and are explicitly uncovered. The splitter rejects old
ungrouped inventories because passage-level masking cannot isolate related texts.

Materialize three separate text collections using `split.json`. Give construction
only `train`, including during register discovery and evidence extraction. A
separate evaluator receives development prompts and keeps their target passages
hidden from the prediction context. Development results may guide curation. Keep
final-test texts and answers out of extraction, scoring, register discovery,
examples, references and development feedback. If the distiller already read that
material, it is development material; obtain a new untouched final set.

## Prediction and baseline

Freeze prompts and a 0/1/2 rubric before each run. The prompt describes the
situation without revealing the person's actual response. Predict in a fresh
context with only the prompt and permitted runtime files. A separate scoring
context may see the target passage and rubric after both predictions are saved.
Use the same model, settings, task information and tool permissions for:

- A minimal `Think like <person>` baseline without the distilled package.
- The candidate skill and only its permitted references.

The baseline controls partly for pretraining familiarity; it does not prove that
public source material is absent from model training. Record exact model/settings,
baseline prompt, both answers and a rationale for each score. Report 2-point hits,
1-point hits, overall score and baseline difference, plus per-domain findings.

Use development for the pre-assembly gate and iterations. Once assembly is stable,
confirm the development gate on the final bytes, then open the final test once.
A final failure is a failed release. If it guides a revision, retire that test into
development and obtain a new untouched test set before making an independent
release claim. Do not change the seed until a run passes. A narrowed scope also
needs a new independent final assessment if the previous final answers were seen.

## Artifact contract

Keep `fidelity.json`, `split.json`, and `registers.json` together in
`transworld-identity/` (or pass an external `--fidelity` path whose sibling files have
those names). The complete machine format is
[schemas/fidelity.schema.json](schemas/fidelity.schema.json).

`fidelity.json` records:

- `content_hash`, `split_hash`, `registers_hash`, `stale`, `register_families`.
- `isolation`: `split_before_extraction: true`, `construction_partitions: ["train"]`,
  `test_exposures: 1`. These are auditable declarations, not tool-proven isolation.
- `projection.gate` and `projection.final`: each has `content_hash`, `passed`,
  `overall`, `baseline`, `hit_2`, `hit_1`, `fresh_context`, `model`, `settings`,
  `baseline_prompt`, and `items`. Each item has `id`, `prompt`, `answer`,
  `baseline_answer`, `score`, `baseline_score`, `rationale`. IDs exactly cover the
  development or test partition respectively. Scores are integers 0/1/2. An
  aggregate is `sum(score)/(2*n)`. Both phases must score at least .50 and must
  not regress against the baseline. Ties permit release but demonstrate no gain.
- `cost`: current `content_hash` plus the existing inventory and presence fields.
  `in_core_final + logged_out == total_divergences`; unlogged losses must be zero.
- `style`: current `content_hash`, modulation and avoid-list results. If only style
  is stale, record `stale: ["style"]` and a nonempty `style_staleness_note`, mirrored
  in the human coverage report. Never report that old result as current.
- For multiple families, including after a merge, `discrimination`: current
  `content_hash`, `label_type: "register_family"`, `score`, `n`, `seed`, and
  `mask_names: true`. Score must be at least .70. Set top-level `merge_triggered`
  when a merge requires this check. If only one family remains, retain the rechecked
  comparison distance matrix and a nonempty `merge_review` instead of pretending a
  one-label classification measures separability.
- For multiple families, `register_selection`: current `content_hash`, `score`,
  and `cases`. Each case records `audience`, `task`, `stakes`, `expected`,
  `selected`, `observed`, generated `answer` and grading `rationale`. Cover every
  family with novel prompts lacking source titles/cast cues. A hit requires the
  expected, selected and independently observed family all to agree. Score at
  least .70. This measures choosing and producing a register, separately from
  recognizing an original passage.

Before release, install `requirements-release.txt` into the Python environment running the
validator. Release checks validate both `fidelity.json` and `registers.json` against their
declared Draft 2020-12 schemas before interpreting gate conditions. Missing schema support
fails release validation with installation guidance. Structural draft validation does not
need this dependency.

Register evidence must have unique unit IDs matching `n_units`, matrix labels naming every
recorded unit exactly once, and nonempty families partitioning those units exactly once.
Family IDs/counts, the single/multiple verdict and optional unit-family mirrors must agree.
The matrix label order defines row/column order and may differ from inventory order.
`z_distance` and optional `ratio_exceedances` must be square for those labels, contain finite
nonnegative numbers, be symmetric (relative tolerance 1e-9, absolute tolerance 1e-12), and have
exact zero diagonals. Exceedance counts must be integers. These requirements apply before
any single-family exemption from the multiple-register gates.

Generate a hash immediately before each evaluation, and attach it to that result.
Never update an old result's hash to make it appear fresh.

```bash
python3 -m pip install -r requirements-release.txt
python3 scripts/validate_package.py /path/to/persona --print-hash
python3 scripts/validate_package.py /path/to/persona --release --fidelity /path/to/transworld-identity/fidelity.json
```

The runtime hash is SHA-256 of compact UTF-8 JSON (`ensure_ascii=False`, separators
`,` and `:`) containing ordered `[relative_path, file_sha256]` pairs. `SKILL.md`
comes first, followed by every file under `references/` sorted by path. Every
hash includes a `sha256:` prefix. File hashes cover raw bytes. Discovery symlinks
do not change the hash; runtime files escaping the skill root are rejected. The
split and register hashes are SHA-256 of their raw JSON file bytes. The ledger is
excluded from the runtime hash so writing results cannot invalidate itself.

Structural validation remains available without `--release` for drafts. Only the
release invocation supports a claim of verified release gates. Missing, malformed,
failed or stale required evidence exits nonzero. Keep its validation report in the
ledger. Existing personas need new evidence only to claim current strict research qualification;
ordinary incremental delivery uses a separate completion report. Never retrofit passing declarations.

## Executable runs and new required evidence

Use the optional [evaluation runner](evaluation-runner.md) to execute controlled prediction,
separate blind grading and sealed records. Human corrections are appended as child records.
Release now also requires [behavioral evidence](behavioral-evaluation.md) for reasoning,
costly commitments under pressure, historical scope and identity recognition. These are
reported separately from position recall, cost inventory and style. Register discovery must
supply stable equal-length subsample evidence; insufficient evidence blocks the register claim.
