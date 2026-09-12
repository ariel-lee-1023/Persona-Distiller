# Register evidence with sparse counts

Scheduling follows [standard-workflow.md](standard-workflow.md). Preserve these content and
admission rules; reuse applicable evidence on upgrades. Missing evidence leaves new candidates
pending outside the operative core, not assigned invented metrics. Inconclusive findings do not
authorize another corpus-wide pass, threshold changes or unbudgeted evaluation.


`register_discover.py` treats ratios as descriptive, not sufficient evidence for
separation. Zero versus positive has an undefined ratio, recorded as JSON null.
A difference can force incompatibility only after sufficient source observations,
minimum event count and absolute effect size checks.

Defaults are explicit provisional settings:

- At least 600 words (English) or Han characters (Chinese) and 20 sentences per
  unit, at least two comparable units, and three non-overlapping equal-length
  subsamples of at least 100 tokens per unit.
- At least five observed events on the higher-frequency side and a difference of
  ten events per 10,000 tokens for frequency dimensions.
- Length differences of at least 3 tokens for mean/median, 5 for the 90th
  percentile, and .10 for long-sentence share, in addition to the ratio criterion.
- Ratio above 3 on at least three supported dimensions, with zero-denominator
  differences considered only after the support/absolute checks.
- At least .80 agreement across subsamples for each proposed pair decision and
  the resulting family coassignments. With three samples this requires all three.

`--min-tokens`, `--min-events`, `--min-rate-delta`, `--subsamples`,
`--min-stability`, `--ratio-threshold`, and `--dims-threshold` are recorded in the
artifact. They are not population-calibrated norms; publish sensitivity findings
and do not lower thresholds until a desired result appears.

The largest gap in normalized distances alone no longer creates families. Sparse
changes can be magnified by normalization, so unsupported pairs remain eligible
for pooling. A persistent supported contrast still separates units. Mixed language
metrics require separate runs. Nonfinite JSON is never emitted.

Thin or unstable evidence yields `INSUFFICIENT_EVIDENCE`, zero declared register
families and retained diagnostic measurements. It blocks a verified release; it
must not be reinterpreted as `SINGLE_REGISTER`. Gather comparable text or report
that the register question remains unresolved. The release validator checks the
declared schema, matrix integrity, unit membership and stability before using a
single-family exemption. Subsampling reduces one source of instability; it cannot
establish that repeated paragraphs are independent observations or cure a biased
source selection. Inspect duplicates and source diversity during acquisition.
