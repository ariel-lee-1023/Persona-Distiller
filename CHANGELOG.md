# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Generated personas are now delivered as directly discoverable local-agent projects: runtime
  files live under `.agents/skills/<slug>-perspective/`, while the human-facing
  `fidelity-ledger/` remains outside `.agents/`.
- `scripts/validate_package.py` now requires exactly one nested Agent Skill, verifies that its
  directory matches frontmatter `name:`, and validates runtime references from that skill root.

## [3.0.0] — 2026-08-16

3.0 is a major release. It changes the shape of three intermediate artifacts, adds required fields
to two of them, introduces a stage that runs before all previously-existing Stage 2 work, and
promotes one conditional test to mandatory. Packages produced under 2.x remain valid artifacts, but
their logs will not validate against the 3.0 schemas without a pass. See [MIGRATION.md](MIGRATION.md).

The release has one governing theme. Every change below closes a gap where the specification's
correctness depended on the distiller *noticing* something — and a distiller that had noticed would
not have needed the rule. A gate that fires only when someone already suspects the failure it
detects is not a gate; a field that is filled in when remembered is not a record; a formula whose
unit is implied is not a measurement. So the work is mostly relocation of judgment: from the
distiller's attention into the corpus's own numbers, into required fields, into scripts, and into
verdicts that name the remedy instead of merely flagging the problem.

### Added

- **Pass A0 — register discovery, and `scripts/register_discover.py`.** The single most consequential
  change in 3.0. Through 2.x, style features were measured over the corpus as a whole and the
  question of whether the corpus contained *one* voice was never asked; it was answered implicitly,
  in the affirmative, by the act of pooling. When a body of work spans career phases, genres, or
  audiences, that pooled baseline is not a measurement of the person but an average of two of them —
  a mean sentence length halfway between two habits the person never had — and the failure is
  invisible in the output, because an average of two registers looks exactly like an ordinary set of
  numbers. Everything downstream then inherits the fiction: the avoid-list forbids constructions one
  register uses freely, the modulation rules describe drift between two things rather than movement
  within one, and the style-match test at Stage 5 passes, because it compares generated prose against
  the same fiction it was generated from.

  Pass A0 now runs before any feature is measured. `register_discover.py` measures every unit on one
  feature vector, builds the pairwise distance matrix, and proposes a family assignment with the
  separation statistics behind it, writing `registers.json` (new schema:
  `references/schemas/registers.schema.json`). Downstream measurement is then per-family first and
  pooled second. `n_registers = 1` is a legitimate and common result — what is not legitimate is
  never asking.

  The division of labour is deliberate and is stated in the spec because it is the part that will be
  got wrong under pressure: **the script measures; the reader decides.** Naming a family, nominating
  a default, ordering a within-family gradient, and recording where a family boundary cuts across a
  cluster are readings, not measurements, and `registers.json` is marked unfinished until those
  hand-added fields are filled. And when discovery and the discrimination gate disagree, the rule is
  to *reduce* the number of families — not to re-run discovery at a looser threshold until the
  numbers come out as hoped.

- **Two new element classes: `procedure` and `verdict`.** Both were previously buried inside
  `regularity`, and both were lost for the same structural reason: the Stage 3 rubric scored them
  low, and the deletion rule then removed exactly the material a reader recognises fastest.

  A **`procedure`** is an *ordered* method step, and it now requires `order`, `precondition`, and
  `on_fail`. The ordering is the whole reason it needs its own class. An unordered pile of heuristics
  gives a host agent no way to know what runs first, so it applies them simultaneously — and the
  guard whose entire value was firing before everything else never fires at all. A method the persona
  cannot execute in sequence is not a method; it is a list of things the person believed.

  A **`verdict`** is a standing judgment about a named object, and it requires `object`, `judgment`,
  and `corpus_hits`, plus the usual ≥2 independent clusters so that a judgment made once in an aside
  stays an aside. Verdicts scored badly under the old rubric because a judgment on a proper name
  predicts nothing beyond its own object — which is exactly why they kept getting cut, and exactly
  why the host agent then re-derived a slightly different verdict on every turn, on a question the
  corpus had already settled.

- **Class-prefixed element ids** — `PROC CR VD PR IM MOD PP` — enforced in the schema against the
  element's `type`. A flat `e017` makes the class distribution unreadable, and the class distribution
  is precisely what the elevation rule and the Stage 5 presence assertion both have to read. The
  prefix/type agreement is structural rather than advisory because a prefix that has drifted from its
  type is worse than no prefix at all: it is a label a reader will trust.

- **`scripts/token_count.py`** — one explicit token estimator for every budget in the skill, and
  `tokenizer` is now a **required** field in `scores.json`. Every budget here is denominated in
  tokens, and a budget without its unit is not a number: the same package measures roughly twice as
  large in Chinese as in English under a word-based count, so "4,000" silently meant two different
  sizes in two runs of the same skill. Counts Han and kana characters separately from Latin words;
  `--calibrate` adjusts the rates against a real tokenizer where one is available.

- **`scripts/validate_package.py`** — mechanical check of a produced package, for the one defect
  class that survives careful reading. Ledger material sitting inside a runtime reference, a core
  load-list pointing at a cluster module nobody wrote, a near-empty file that does not say why,
  implementation language leaking into the core's own description: none of these look wrong on the
  page, because there is nothing on the page to notice. Judgment calls are returned as warnings
  rather than as false certainty, and `--strict` promotes them. `--headings` is required for the
  core-heading check and deliberately empty by default — a core may be written in the subject's own
  language, and a validator that imposes English headings would fail the most faithful packages.

- **`scripts/name_audit.py`** — back-checks every name the package uses against **literal corpus
  hits**, separating heading-like appearances from ordinary prose. The failure it catches has a
  precise mechanism: a tidy diagnostic label invented during distillation, or lifted from an editor's
  chapter heading, quietly acquires the authority of the person's own coinage — after which the
  persona uses, with total confidence, a term its subject never used. An editor's heading is not
  attestation. Its output is what `corpus_hits` on a `verdict` element is now required to come from.

- **`--stratify` for `scripts/holdout_split.py`**, with largest-remainder allocation across domain
  labels, plus a required sampling description in `fidelity.json` when stratification is off. A
  random mask over an uneven corpus lands mostly in the largest domain, and the resulting score is
  then read as though it described the persona rather than its biggest topic. A score whose sampling
  is not described is a number without a denominator.

- **`hit_2` and `hit_1` reported separately** in the projection results. The aggregate collapsed two
  different things: reaching the right conclusion by the person's own mechanism, and reaching it by a
  mechanism the person would reject. Both look like partial credit, but only the first generalises —
  the second is a persona that agrees with its subject about every case in the corpus and diverges on
  the first case outside it. A respectable aggregate with a low `hit_2` is now a specific, actionable
  diagnosis rather than a comfortable number.

- **`content_hash` and `stale` on `fidelity.json`, both required.** Curation is a loop: a gate sends
  the set backwards, clusters get merged, an element is demoted two batches after the score that
  justified keeping it. Nothing previously said what happens to a result when the thing it measured
  changes underneath it, so the default was that nothing happened — the number stayed, still labelled
  as this package's score, now describing a package that no longer existed. A result whose hash does
  not match the current package is stale whether or not anyone marked it, and that is mechanically
  checkable. Staleness is marked at the moment of the change, not at the end, when it will be
  forgotten. A stale style-match may ship if the coverage report says so; a stale projection or cost
  gate may not.

- **Computed budgets for `frameworks.md` and `voice.md`**, replacing the flat soft ~4,000. Both are
  now sized from the constructs, verdicts, moves and register families actually routed to them, on
  the same supply→clamp shape as the core and cluster budgets, clamped to 2,000–7,000. A flat band on
  the two standing modules had the same defect it had on cluster modules: a rich corpus quietly
  outgrew it and a thin one was invited to pad up to it.

- **`MIGRATION.md`** — what to do with 2.x artifacts, field by field.

### Changed

- **The discrimination test is now mandatory whenever `n_registers > 1`, and is re-triggered by any
  cluster merge.** Through 2.x it ran "only if the core claims registers", which put the gate
  downstream of the distiller's own judgment — it fired only when someone had already noticed the
  very thing it exists to detect. Now the corpus decides. The merge trigger closes the other half of
  the hole: a merge is precisely the operation that can pool two registers into one module without
  anyone deciding to.

- **`cluster_budget.py` returns a verdict instead of a boolean**, and the distinction it now draws is
  the substantive fix. 2.x had a single `recut_flagged`, which could say that a cluster was overloaded
  but not what to do about it — and the two remedies are opposite, so a single flag gave the wrong
  answer roughly half the time. An overloaded cluster spanning **two topic domains** was
  mis-segmented and goes back to `segment.py`: **RECUT**. An overloaded cluster in **one domain**,
  overloaded because its material arrives in two registers, must *not* be re-cut — that would
  separate a subject from itself — so the answer is **SPLIT_IN_MODULE**: keep one module, declare an
  internal A/B register split with a no-pooling header, and give separate style guidance for each.
  The verdict enum is `OK | FLOOR | RECUT | SPLIT_IN_MODULE`; `recut_flagged` is retained as
  deprecated so 2.x logs still validate. A per-register price and a `--coefficients` override were
  added at the same time, the latter so a future recalibration does not require editing the script.

- **Core budget: two new supply terms and raised ceilings.** `supply` now includes
  `200·min(n_procedure,5) + 150·min(n_verdict,8)`, and the ceiling rows move from 4,000 / 5,500 /
  6,500 to **4,000 / 6,000 / 7,500**. Procedures and verdicts are priced high because they are the
  two classes a host agent can actually *execute*; the old ceilings were set before either existed,
  so a corpus rich in both saturated a supply term it had no room to spend.

- **Class priority now reads `procedure ≈ cost_refusal ≈ verdict ≈ projectible > interactional >
  variation > preoccupation > stable_style`**, placing the two new classes in the top band rather
  than letting them compete on composite score against abundant style metrics.

- **`frameworks.md` and `voice.md` are now layered templates asked of every subject** — `§0–§7` and
  `§0–§11` respectively — rather than free-form modules with a topic list. Two properties follow, and
  both were the point. First, the structure is **universal**: it is asked of every corpus, and a
  section the corpus cannot fill is *marked absent* rather than deleted, because an absence a reader
  can see is information and a missing heading is not. Second, the ordering inside `frameworks.md` is
  a substantive claim rather than a filing convention — **§1 Method** and **§2 Epistemology** come
  before **§3 Ontology** and **§4 standing verdicts**, because a persona handed only conclusions can
  restate them and cannot extend them. Get the method and the epistemology in place and the verdicts
  become derivable; ship the verdicts alone and you have built a quote database with opinions.
  `voice.md` opens with the register structure for the same reason: a host agent must choose a family
  before writing a sentence, rather than discovering afterwards that it wrote in the average of two.

- **`references/output-template.md` rewritten** around the two layered templates, the Fidelity Ledger
  layout, and the negative-space rule for legitimately near-empty sections. All examples in the
  specification are now **fictional or schematic** — no real distilled package appears as an
  illustration anywhere in the repository. A concrete example teaches the example: a reader shown how
  one particular corpus was handled starts matching their own corpus against that shape instead of
  against the rule, and the specification quietly narrows to the case it was demonstrated on. If a
  rule can only be explained by pointing at a package that already exists, it is not yet a rule.

- **The acquisition batch is now a named, forbidden boundary.** `pipeline.md` states it directly: the
  batches in which a corpus happened to be acquired are an artifact of how it was obtained and carry
  no information about the person, yet they are the most tempting available segmentation because they
  are already there. Segmenting on them produces clusters that are internally incoherent in exactly
  the way `segment.py` exists to prevent, and the resulting manifest looks entirely normal. The
  section gives the five-step correct move and a diagnostic for detecting the failure after the fact.

- **Schemas updated throughout**: `registers.schema.json` added; `n_registers` on the coverage map;
  the eight-value type enum, class-prefix patterns, and eleven conditional rules on
  `extractions.schema.json`; `tokenizer` (required), `standing_budgets`, `coefficients_source`, the
  new ceiling enum, and the cluster verdict on `scores.schema.json`; `content_hash`, `stale`,
  per-family style deltas, and the discrimination trigger on `fidelity.schema.json`; the two
  domain-labelled input forms on `passages.schema.json`. `register_discover.py --json` and
  `cluster_budget.py --json` both write shapes that validate as-is, so a validation failure there
  means the script and the schema have diverged.

### Deferred

Four register-handling refinements and three fidelity extensions were scoped for this release and
deliberately held for **3.1.0**, rather than shipped partially specified. 3.0 establishes the
register structure as a first-class artifact; the follow-on work builds on it and is not worth
rushing to fit a version number.

### Earlier in the 3.0 cycle

The entries below were made against `[Unreleased]` over the course of the 3.0 cycle and ship in this
release. They are kept in their original form, in the order they were written, because a couple of
them supersede each other and the sequence is part of the record.

#### Changed

- **`provenance.md` moved out of `references/` into a new top-level `fidelity-ledger/` package, and
  `episodic.md`'s scope clarified to a positive definition.** Two related fixes to the honesty
  split:
  - **Provenance relocation.** `references/` is host-agent-facing — the persona loads modules from
    it at runtime — so a file that maps core elements to sources, records computed budgets, and
    logs gate/fidelity scores never belonged inside it structurally, even though nothing in it was
    ever meant to be spoken. `provenance.md` now ships at
    `<slug>-perspective/fidelity-ledger/provenance.md`, a sibling of `references/` rather than a
    member of it. This makes the audience split structural instead of just documented: it is no
    longer possible for a host agent enumerating `references/` to pick up the audit file by
    accident. Content is unchanged — the per-element source table, the computed-budget log, and
    the mirrored `fidelity.json` results all move together, verbatim. Every cross-reference to
    `provenance.md` in `SKILL.md`, `output-template.md`, `fidelity-tests.md`, `scoring.md`,
    `pipeline.md`, and the JSON schemas now points at `fidelity-ledger/provenance.md`.
  - **`episodic.md` scope, clarified.** The module was previously defined only negatively
    ("attested but lower-scoring material," "expression and modulation elements do not go here"),
    which left the actual admission test implicit. It is now defined positively: `episodic.md`
    holds concrete, attested, one-off **happenings** — specific incidents, anecdotes, and
    decision-record fragments that a reader could point to as things that occurred, and that did
    not clear a cluster module's 1,800-token floor or were demoted from one for space. Two
    exclusions are now explicit rather than implied: named constructs go to `frameworks.md` even
    from a single aside (episodic keeps the incident, not the idea), and any expression/modulation
    element goes to `voice.md` regardless of where it was demoted from. `episodic.md` stays inside
    `references/` — it is still host-agent-facing, on-demand material, unlike the ledger.

- **`episodic.md` moved out of `references/` into `fidelity-ledger/`, alongside `provenance.md`.**
  Superseding the entry directly above: on reflection, `episodic.md`'s positive scope test — could
  a reader point to it as a specific attested happening? — makes it attested source material, not
  reasoning the host agent should load mid-embodiment, so it belongs with the audit trail rather
  than with `frameworks.md`/`voice.md`/`clusters/`. `episodic.md` now ships at
  `<slug>-perspective/fidelity-ledger/episodic.md`. Content and scope are unchanged — concrete,
  attested, one-off happenings that did not clear a cluster module's floor, with the same
  no-concepts/no-expression exclusions — only its location and audience designation move: it is now
  human-facing like `provenance.md`, never loaded by the host agent. `references/` therefore now
  holds only `frameworks.md`, `voice.md`, and `clusters/` — nothing in it is attested-but-unranked
  material anymore, only the standing and per-cluster modules the host agent loads at runtime. Every
  cross-reference to `episodic.md` in `SKILL.md`, `output-template.md`, and `scoring.md` now points
  at `fidelity-ledger/episodic.md`.

- **A mandatory real-world-retrieval line added to the core's "Loading depth" block, and a matching
  Stage 5 check.** The `references/`/`fidelity-ledger/` split governs which of *this repository's
  own files* answer a question about the person's frame — their frameworks, named constructs, and
  characteristic moves — and that corpus is the SOURCE OF TRUTH for exactly that, and only that; it
  was never meant to be evidence about the world the person did not personally generate. Every
  produced core now carries a fourth Loading-depth line, stated as host-agent operational guidance
  rather than persona voice, that any question turning on a real-world fact outside the corpus's own
  frozen record — an exact quotation, a current event, a law's present text, the state of a field
  today, a detail of the user's own situation, anything the corpus postdates or never covered —
  requires the host agent to retrieve that fact from the live world before running it through the
  persona's frame, exactly as it would for any other skill. This is a second, independent retrieval
  axis from the corpus-internal SOURCE OF TRUTH search: one governs which repository file answers a
  question about the persona; the other governs when the host agent must leave the repository
  entirely. Neither collapses into `voice.md`'s existing anti-drift rule against *narrating* a
  retrieval (naming the search instead of answering) — that rule bans describing the lookup inside
  the persona's voice; it has never meant, and must not be read to mean, that the lookup itself is
  skipped. Documented in `output-template.md` (exact wording and placement) and `SKILL.md` (Stage 4
  requirement, Stage 5 verification item).

#### Added

- **`provenance.md` phrasing rule: audit ledger for the human reader, never a runtime instruction.**
  A real distillation shipped a `provenance.md` line telling the persona what to *say* when a
  quotation wasn't attested ("paraphrases and says so") — the host agent read it as a behavior rule,
  and the persona narrated its own retrieval state mid-answer, breaking character. `provenance.md`
  is not loaded during embodiment and was already documented that way, but nothing previously told
  a distiller not to phrase a row as an imperative. Added an explicit phrasing rule to
  `output-template.md`'s `provenance.md` section and a pointer in `fidelity-tests.md`: write rows as
  third-person facts about the distillation, never as sentences instructing the embodied persona;
  a caveat that needs to surface in the persona's own behavior belongs in the core's retrieval-
  failure handling, written in voice, not in the audit file.

- **Four tools for pipeline steps that were described but not equipped.** The skill shipped
  measurement and splitting, and left ingestion, segmentation, evidence retrieval, and
  register-separation to be done by hand. Each is a place where a run goes wrong quietly: the
  numbers still come out tidy, so nothing signals a problem until the persona is already built on
  them.
  - **`scripts/corpus_clean.py` (Stage 1) — extraction-damage census and repair.** `pipeline.md`
    said to flag garbled extractions, which catches the visible failures. It does not catch the
    three that leave fluent, readable prose: lost fi/fl/ff ligatures (`rst` for *first*, `dierence`
    for *difference*), words wrapped across lines by justified typesetting (`transporta- tion`,
    counted as two words, inflating sentence-length means by 1–2%), and EPUB anchor residue that
    enters the corpus as high-frequency "content words". Detection is two-stage and the stages are
    not interchangeable: an anomalously low `f` rate is a *screen* that false-positives on short
    files, while suspect-token density is the *verdict*, and damaged corpora run 50–100× a clean one
    on it. Repairs are conservative — tokens that are also real English words are reported but not
    changed without `--aggressive`, and a hyphen is closed up only when whitespace follows it, so
    `self-love` survives while `transporta- tion` is joined.
  - **`scripts/segment.py` (Stage 1) — cut clusters, emit a schema-valid manifest.** Segmentation is
    required and load-bearing — the projectibility probe needs ≥2 independent clusters — but was
    unequipped. Hand-cutting a multi-work volume produces two errors that are invisible afterwards:
    *boundary drift*, where a slice runs into the next work and every per-cluster metric then
    averages two registers, and *editorial bleed*, where introductions, translator's notes and
    endnotes are captured as the subject's own words and quietly inflate the firsthand ratio the
    whole run is scored against. Takes line numbers or regex boundaries — prefer regexes, which
    survive re-extraction — strips repeating running headers, flags clusters too small to
    corroborate, and reports the firsthand ratio that sets the core-budget ceiling.
  - **`scripts/kwic.py` (Stage 2) — keyword-in-context evidence retrieval.** Every extraction carries
    example passages and every Stage 5 test scores against them, but `grep` cannot produce them:
    extracted prose puts whole paragraphs on single lines thousands of characters long, so a match
    returns the paragraph, and a match straddling a line break is missed entirely. `--count` makes
    the ≥2-independent-clusters check a single command. One trap is documented in the script's own
    warning path because it costs an hour every time: the pattern is a Python regex, and `a\|b` —
    the habit from grep and sed — matches a literal pipe and returns nothing, which is
    indistinguishable from a corpus that genuinely lacks the passage.
  - **`scripts/discrimination_test.py` — a new conditional gate.** The three existing checks ask one
    question from three angles: does this read like the person? None asks whether the person's
    *registers can be told apart*, and that is prior for any core claiming internal variation —
    per-work, per-period, per-venue. The style-match test structurally cannot catch the failure,
    because a passage can match the aggregate baseline perfectly while being indistinguishable from
    every other register the core promises. Samples passages, hides the labels, scores a blind
    classification, and names the confused pairs. Below 0.70 the instruction is to **collapse** the
    registers into one honest voice: a core that promises a distinction it cannot perform is worse
    than one that never claimed it. `--mask-names` exists because recognising a cast of characters is
    not recognising a register, and a user's utterance will never contain the cast.
- **`scripts/zh_metrics.py` — the expression-measurement script for Chinese corpora.** The whole
  fine-grained expression pass, the expressive-match probe, `voice.md`'s measured baseline, and the
  Stage 5 style-match test all rest on `style_metrics.py`, which tokenises on `[A-Za-z]` and counts
  English hedges and boosters. On a Chinese corpus it returns zeros for every feature that matters —
  and it returns them *silently*, so the failure looks like a corpus with no measurable style rather
  than a tool that cannot read it. That is the worst shape a gap can take in a pipeline whose whole
  claim is "measured, never estimated". This computes the same feature classes in the units Chinese
  prose is actually measured in: sentence length in 汉字, Chinese hedge/booster sets (simplified and
  traditional), punctuation rhythm including 《》 and the interpunct that marks transliterated names,
  person-reference ratios, a character-n-gram fingerprint in place of a word segmenter, and a
  discourse-scaffolding absence check that feeds `voice.md`'s avoid-list directly. Stdlib only, like
  the other two.
- The script **ships with no vocabulary list**. A distiller's tool must not carry one subject's
  jargon, so tracked terms are passed in with `--terms` (inline or a file) and reported as
  per-10k rates alongside everything else.

#### Changed

- **The four new tools are wired into the steps they belong to, not merely listed.** Stage 1 in
  `SKILL.md` and `pipeline.md` now open with the damage census and route segmentation through
  `segment.py`; Stage 2 and `extraction.md` Pass B point at `kwic.py` for evidence and for the
  ≥2-cluster check; Stage 5 and `fidelity-tests.md` gain the discrimination test as a fourth,
  conditional check with its own thresholds and its own instruction on failure. A tool named only in
  a script index gets read after the mistake it prevents.
- `references/schemas/fidelity.schema.json` gains an optional `discrimination` object — score, n,
  seed, whether names were masked, and the confusable pairs — so the new gate is as auditable as the
  other three. It is optional by design: a single-register persona has nothing to discriminate, and
  recording a score of `1.0` for a test that did not apply would be worse than recording nothing.
- Stage 2, `extraction.md` Pass A, `output-template.md`'s "measured, never estimated" rule, and the
  Stage 5 style-match procedure now name the Chinese script where the Latin one would fail, and
  `output-template.md` additionally asks which script and flags produced a `voice.md` baseline
  table — a table nobody can re-run is not a measurement.

## [2.0.0] — 2026-08-04

Sizing and voice. Two of the skill's constants turned out to be doing less work than they looked
like they were doing. The ~5,000-token core cap never bound — shipped cores land at 2,000–4,600
tokens — and had no lower edge, so it neither restrained a rich distillation nor caught a thin one;
it is now a per-run computation with a floor. And the 20% style cap correctly kept the core a
fingerprint, but a fingerprint is enough to *frame* an answer in someone's voice and not to *write*
one at length, which left the skill promising more embodiment than it shipped; the rest of the
expressive system now ships as `references/voice.md`, a standing module co-equal with
`frameworks.md`.

Major, because two intermediate-artifact schemas gained required fields.

### Changed

- **The core's token budget is now computed per run, not fixed at ~5,000.** The flat cap was the
  wrong instrument in both directions: it was never binding in practice (shipped cores landed at
  2,000–4,600 tokens, so it disciplined nothing), and it had no lower edge at all, so a
  under-curated 2,000-token core passed every check the skill made. The budget is now a **supply
  term** over the diagnostic material that actually survived curation — `2,200 +
  250·min(n_cost_refusal,6) + 180·min(n_projectible,7) + 140·min(n_interactional,5) +
  120·min(n_variation,4)` — clamped between a floor and a corpus-derived ceiling. Preoccupation and
  stable style contribute nothing to supply: they fill space the diagnostics have already earned,
  and letting abundant style buy more room is the exact inversion the skill exists to prevent.
- **Ceilings come from `coverage_map.json`**, first match winning: 4,000 when `firsthand_ratio` <
  0.50 or the corpus is small (< 50k tokens or < 4 clusters), 5,500 mid, 6,500 for a large
  multi-period corpus. A persona built mostly from other people's words does not get to be large.
- **Reference module budgets split by file type**, replacing the single ~800–2,000 range that every
  shipped persona already violated by 2–4×: `clusters/*.md` ~1,500–4,000 with a hard 6,000 ceiling
  (split by period or theme rather than trimming evidence), `frameworks.md` and `episodic.md` soft
  ~4,000, and `provenance.md` uncapped — it is one row per core element and is not loaded during
  embodiment, so completeness beats size.
- `references/pipeline.md`: `firsthand_ratio` is now shown in the `coverage_map.json` example (it
  was only described in `acquisition.md`), and the coverage map's stated jobs include picking the
  core's ceiling row.

### Added

- **`references/voice.md` — a standing expressive-system module, co-equal with `frameworks.md`.**
  The 20% style cap keeps the core a fingerprint, and that is right, but a fingerprint is enough to
  *frame* an answer in someone's voice and not to *write* one at length — so the cap on its own left
  the skill promising more embodiment than it shipped. The rest of the system now has a home: favored
  constructions with attested fragments, the **avoid-list** (words and openings conspicuously missing
  from the corpus — as diagnostic as the favored ones, and until now homeless despite Pass A being
  told to measure them), modulation rules as trigger → shift pairs, register range across settings
  and periods, lexical fingerprint, the `style_metrics.py` measured baseline, and anti-drift pairs
  for long generations. Built from **firsthand clusters only**. The two standing modules are now the
  deliverable pair: what the person thinks with, and how the person sounds.
- **The style cap became a routing rule, not a discard rule.** Surplus expression and modulation
  elements go to `voice.md` rather than being scattered into `episodic.md` or lost; material cut
  under the 0.55 deletion rule stays cut. `voice.md` takes the demoted, never the deleted — otherwise
  it becomes the stylometry report the core was protected from. `episodic.md` no longer holds
  expression/modulation at all.
- **The style-match test now runs the configuration that ships.** Samples are generated under the
  core **plus `voice.md`** — that pair is the sustained-prose configuration — with at least one
  contested prompt and at least one sample long enough to drift (400+ words), since a voice that is
  right for three sentences and generic by the twelfth is exactly what this test exists to catch. A
  new `avoid_list_violations` count is required in `fidelity.json`: cheap, near-binary, and it
  catches drift the distributions blur. Running the core alone is now described as a control, not
  the test.
- **A 3,000-token core floor, defined as a diagnostic trigger rather than a quota.** Landing under
  it means the survivor pool is too thin for a full-scope core, and the response is ordered:
  re-examine the 0.45–0.55 cut band for diagnostic classes only (the 0.55 threshold is tuned for an
  abundant pool), check whether the shortfall is an upstream corpus fact rather than a curation
  failure, and failing both, ship a reduced-scope core with the shortfall logged in `provenance.md`
  and named in the coverage report. Topping the core up with `stable_style` material to reach the
  floor is prohibited — it would breach the 20% style cap and produce exactly the fluent, correctly
  sized, anyone-shaped core the design is built against.
- `provenance.md` now records the computed budget, the ceiling row, the core's actual size, and any
  floor resolution, so the core's *size* is auditable alongside its contents.

### Breaking

- **`fidelity.json` requires `style.avoid_list_violations`** (an integer; record `0` when the corpus
  supported no avoid-list). Existing fidelity records will fail validation until the field is added.
- **`scores.json` requires a new `core_budget` object** (supply, ceiling, ceiling_rule, budget,
  floor_triggered, counts by class; `floor_resolution` when the floor was tripped). Logs written
  before this change will fail schema validation — add the block, or re-derive it from the run's
  coverage map and survivor counts. The ceiling is enumerated to `4000 | 5500 | 6500` so a budget
  cannot quietly exceed what the corpus supports.

## [1.2.0] — 2026-07-27

Remote corpus acquisition. The corpus path stopped being hardcoded in 1.1.0, but the corpus was
still assumed to be local files already on disk. It can now be a git repository, a file URL, or a
docs site, wiki, or published note collection — with a procedure that separates the person's
material from the container's scaffolding, and classifies whose words each cluster actually
contains.

### Added

- **`references/acquisition.md`** — the corpus-acquisition procedure, run *before* Stage 1 (not a
  sixth stage; the five-stage framing is unchanged). Covers resolving the source type, fetching by
  type, corpus-versus-container separation, attribution classification, source independence, chunking
  for wikis and note collections, honest degradation, and crawl rights.
- **Corpus/container separation with mandatory user confirmation** — a repository or a site is a
  *container*. Everything acquired is inventoried and classified as corpus or scaffolding (READMEs
  describing the collection, build and CI config, templates, navigation and index pages, licence
  files, contributions by anyone other than the subject), and the classification is shown to the user
  for confirmation before Stage 1. Handed a URL, the old behaviour varied by host, and its worst case
  was silent: a fluent persona of the repository's own scaffolding.
- **Attribution classification** — every acquired unit, and every cluster it produces, is labelled
  `firsthand`, `secondhand`, `mixed`, or `unknown`. Most online knowledge bases are secondhand;
  distilling a well-organised set of someone's *notes on* a thinker yields a persona of the
  note-taker's summarising prose.
- **Three hard rules following from attribution** — expression and modulation extraction runs on
  `firsthand` clusters only, and `style_metrics.py` is never run on secondhand text because it
  measures the wrong person's prose; a projectible regularity requires at least one `firsthand`
  cluster, with secondhand clusters able to corroborate but not to carry one alone; and cost-bearing
  refusals or interactional moves sourced only from secondhand material are flagged unverified and
  cannot satisfy the Stage 5 cost/presence assertion.
- **Source-independence collapsing** — the ≥2-cluster corroboration rule assumes clusters are
  independent evidence. Two pages of one knowledge base derived from the same underlying work are
  *one* source and are now collapsed before scoring, so a single source cannot silently satisfy a
  rule designed to require two.
- **Chunking guidance for wikis and note collections** — group short pages by topic or by the
  underlying source work until each cluster can carry evidence, and deduplicate first, since
  repetition inside one knowledge base is not recurrence across clusters and otherwise reads as a
  preoccupation that does not exist.
- **Cluster attribution fields** — `clusters-manifest.schema.json` gains a required `attribution`
  enum plus optional `source_url`, `retrieved` (ISO 8601 date), and `revision` (commit SHA), because
  remote content changes and reproducibility needs the retrieval pinned.
- **Acquisition records on the coverage map** — `coverage-map.schema.json` gains optional `sources`
  (type, location, retrieval date, revision, licence) and `firsthand_ratio`, the number that says how
  much of a persona came from the person rather than from people writing about them.

### Changed

- **`SKILL.md` — Inputs** now names four accepted source types (local path or directory, git
  repository URL, plain file URL, docs site / wiki / note collection) instead of "one or more files,
  or a directory".
- **`SKILL.md` — Host environment** — the *Corpus in* row states that the source may be remote, and
  that network access and `git` are host capabilities to check rather than assume; missing either
  means saying so and asking for the material locally, never reconstructing it from training-data
  recollection of the person.
- **`SKILL.md` — pipeline preamble** establishes that acquisition precedes Stage 1, and the reference
  list points at `references/acquisition.md`.
- **`references/pipeline.md`** — the extraction-routing section now opens by requiring acquisition
  and the confirmed corpus/scaffolding split first, and the `clusters/manifest.json` snippet carries
  `attribution`.
- **`references/schemas/README.md`** — the index rows for the two Stage 1 artifacts point at
  `acquisition.md`, the required `attribution` label joins the list of structurally encoded rules,
  and the firsthand requirement on regularities is recorded among the rules deliberately left
  unencoded, since no schema can follow a cluster id across files.

## [1.1.0] — 2026-07-27

Host portability + artifact schemas. The skill previously assumed the filesystem layout of one
specific agent host; it now runs anywhere. Intermediate artifacts gain canonical JSON Schemas.

### Added

- **`SKILL.md` — "Host environment" section** — the three host-dependent locations (corpus in, work
  directory, persona out) are now named explicitly and resolved once at the start of a run, instead
  of being hardcoded. States that suggested tools are preferences with fallbacks, and that both
  scripts are standard-library-only under any Python 3.
- **Explicit work-directory creation** — `references/pipeline.md` now instructs the agent to create
  the work directory before Stage 1 and explains why the artifacts must survive the whole run: the
  control flow is a loop, the deletion rule is only defensible with the audit log intact, and the
  coverage report and `provenance.md` are built from those files.
- **`.gitignore`** — blocks the work directory, generated `*-perspective/` personas, stray
  intermediate artifacts, and source-corpus formats (`*.pdf`, `*.epub`, `*.mobi`, `*.azw`,
  `*.docx`, and corpus directories). This last group protects the claim in `NOTICE.md`: a single
  careless `git add -A` on a corpus directory would republish the source works. Shipped schemas are
  explicitly re-included so no JSON rule can shadow them.
- **`references/schemas/`** — JSON Schema (draft 2020-12) for every intermediate artifact the
  pipeline writes, each with a worked example: `clusters-manifest.schema.json`,
  `coverage-map.schema.json`, `extractions.schema.json`, `scores.schema.json`,
  `fidelity.schema.json`, and `passages.schema.json` (the input `holdout_split.py` reads).
  Previously these shapes existed only as illustrative snippets across four reference files,
  two of which carry `//` comments and so do not parse as JSON if copied verbatim.
- **Structurally encoded rules** — the schemas express several of the skill's hard constraints
  rather than only field types: a `regularity` element requires ≥2 corroborating clusters, a
  `cost_refusal` or `interactional` element requires `convenient_move`, a `core` decision requires
  a `rank`, and all probe scores and composites are bounded to 0–1.
- **`references/schemas/README.md`** — artifact-to-stage-to-schema index, and an explicit note on
  the two rules deliberately left unencoded (the 0.55 deletion threshold, which valid `cut` records
  fall below, and weights summing to 1.0, which JSON Schema cannot express).

### Changed

- **Work directory is now relative** — `persona_work/` under the current working directory, or a
  host-provided scratch location, replacing the hardcoded `/home/claude/persona_work/`.
- **Corpus input and persona output locations are resolved from the host** rather than fixed to
  `/mnt/user-data/uploads/` and `/mnt/user-data/outputs/`. Those paths remain documented as one
  host's convention, not as the contract.
- **Extraction routing table restructured into preferred / fallback columns** — every format has a
  named stdlib or common-CLI fallback, so a host lacking a document-reading tool degrades output
  quality and logs it in the coverage report rather than failing the run.

### Fixed

- **`README.md` script usage** — the `holdout_split.py` example passed a corpus directory, which
  the script cannot read; it requires a JSON list of passage IDs or inline `--ids`. Corrected, and
  the `--ids` form added.
- **`SKILL.md` script description** — now states that `holdout_split.py` takes a JSON passage-ID
  list rather than a corpus path.

## [1.0.0] — 2026-07-23

Initial public release.

### Added

- **`SKILL.md`** — the core skill: a five-stage pipeline (ingest & segment → multi-granularity
  extraction → multi-probe curation & deletion → assemble → fidelity verification) for
  distilling one person's corpus into an embodiment-ready persona skill.
- **Family-resemblance framing** — recognition treated as redundant, overlapping probes rather
  than a clean partition of the person; corroboration across probes is retained rather than
  deduplicated away.
- **Hard-signal prioritisation** — cost-bearing refusals, patterns of variation, and
  interactional moves weighted above easily-counted surface style.
- **Five-probe scoring composite** — projectibility (0.30), cost/refusal signal (0.25),
  expressive match (0.20), interactional visibility (0.15), preoccupation (0.10).
- **Deletion rule** — hard cut below 0.55 composite, plus unconditional cuts for generic
  language, forced meta-commentary, or conflict with a higher-scoring voice feature.
- **Elevation rule** — survivors ranked by class priority before composite, capping pure style
  averages at ~20% of the core so abundant style metrics cannot crowd out sparse fingerprints.
- **Pre-assembly gates** — projection gate and cost gate run *before* Stage 4 and feed back into
  curation as control signals, making the pipeline a loop rather than a straight line.
- **The honesty split** — no disclaimers or meta framing inside the embodiment artifact;
  coverage gaps, citations, and confidence relocated to `references/` and the user-facing
  coverage report.
- **`references/pipeline.md`** — Stage 1 mechanics, extraction routing by file type, coverage
  map schema.
- **`references/extraction.md`** — Stage 2 expression-DNA taxonomy, projectible-regularity
  verification, cost-bearing and interactional catalogue.
- **`references/scoring.md`** — Stage 3 probes in depth, worked scoring examples, deletion rule,
  audit-log format.
- **`references/output-template.md`** — Stage 4 core template and references-package layout,
  with a filled example.
- **`references/fidelity-tests.md`** — Stage 5 projection, cost, and style-match procedures,
  thresholds, and reporting.
- **`scripts/style_metrics.py`** — countable expression features (sentence-length distribution,
  hedge/booster rates, punctuation rhythm, lexical diversity, person-reference ratios, top
  content terms and bigrams). Standard library only.
- **`scripts/holdout_split.py`** — reproducible seeded split of passages into keep/masked sets
  for the held-out projection test.
- **Operating modes** — full distillation (default), analyze-only, and fold-in/update against an
  existing persona.
- **Scope statement** — perspective and thinking-style work only; explicit refusal of deceptive
  impersonation and forged attribution.

[Unreleased]: https://github.com/ariel-lee-1023/persona-distiller/compare/v3.0.0...HEAD
[3.0.0]: https://github.com/ariel-lee-1023/persona-distiller/compare/v2.0.0...v3.0.0
[2.0.0]: https://github.com/ariel-lee-1023/persona-distiller/compare/v1.2.0...v2.0.0
[1.2.0]: https://github.com/ariel-lee-1023/persona-distiller/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/ariel-lee-1023/persona-distiller/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/ariel-lee-1023/persona-distiller/releases/tag/v1.0.0
