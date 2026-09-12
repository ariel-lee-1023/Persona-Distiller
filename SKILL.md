---
name: persona-distiller
description: >-
  Distill one person's provided public record (books, essays, transcripts, interviews,
  decision records) into a reusable persona or perspective skill with a compact core,
  references and an operational scope contract. Extract characteristic reasoning,
  cost-bearing refusals, interactional moves and register variation, then verify with
  independent projection and baseline comparisons, cost and style checks, and register
  tests. Use when the user wants to distill, channel, think like, write as, or build a
  persona, voice skill or system prompt embodying a specific person, even without saying
  "skill". Work from the provided corpus without inventing documented positions.
---

# Persona Distiller

Turn a corpus of one person's public material into a persona another agent can *embody* —
not a biography, not a summary, not a quote database. The output is a lean core `SKILL.md`
optimized so that a reader familiar with the person's record cannot easily tell its output
apart from the real thing on public topics the corpus covers.

## Governing idea: recognition is a family resemblance

You are not building a clean taxonomy of the person. Recognition in text is a
family-resemblance practice: the *same* identity shows up redundantly, at different grains,
through overlapping probes — a sentence rhythm here, a refusal there, a recurring move when
cornered, a theme they keep circling back to. No single probe is definitive; the overlap is
the signal. So do **not** try to partition the person into mutually-exclusive buckets, and do
**not** dedupe away a trait just because it surfaces in three different probes. Redundant
corroboration across probes is *strength*, and it is exactly what you keep.

Two consequences shape everything below:

1. **Fight the pull toward easily-measured style.** Sentence length, hedge-word frequency,
   and favorite punctuation are trivial to count — and almost everyone's are somewhat generic.
   The signals that actually individuate a person are *harder* to extract and *higher* value:
   **ordered procedures** (what they do first, and what they do when it fails), **cost-bearing
   refusals** (positions they held against their own incentive), **standing verdicts** (the
   judgments they arrive at repeatedly, by name, about specific objects), **patterns of variation**
   (how their register shifts under pressure, audience, or stakes), and **interactional moves**
   (how they concede, reframe, dig in, or shift footing in exchange). The scoring weights below
   deliberately elevate these. When in doubt, spend your budget on the hard signals, not the easy
   ones.

   A corollary that is easy to miss: **one person can have more than one voice.** A body of work
   written across a career, or across genres, or for different audiences, frequently contains two
   or three sharply distinct registers. Averaging them produces a style baseline that describes
   nobody — a mean sentence length halfway between two habits the person never actually had — and
   every downstream measurement then inherits that fiction. So the register structure is
   discovered *first*, in Stage 2 Pass A0, before any feature is measured. Do not treat one author
   as one voice until the numbers say so.

2. **Delete without mercy.** The core is an embodiment artifact, and every low-value line
   dilutes voice and adds distance. Anything that scores below threshold, reads as generic,
   forces meta-commentary, or conflicts with a higher-scoring voice feature gets **cut** — not
   softened, not averaged in. A tight 4k-token core that nails the fingerprints beats a
   comprehensive 15k-token one that reads like everyone.

## The hard rule about the OUTPUT (read this twice)

The generated persona `SKILL.md` contains **no honesty language, no uncertainty disclaimers,
no provenance hedging, and no meta framing** — no "based on available sources", no "the person
seems to", no "as an AI embodying". Those move the reader out of the voice and destroy
identification. This is a deliberate departure from provenance-forward distillers.

The detailed Fidelity Ledger remains human-facing: citations, scores, confidence and audit
history live there. The host also needs a compact operational scope contract in
`references/scope.md`: supported domains and periods, conditions on standing judgments,
earlier/later positions, and the boundary between attestation and extrapolation. Load it with
the core before answering. It is host guidance, not persona prose or an audit dump. Preserve
the expressive core while identifying extrapolation when attribution or changed circumstances
make that distinction material; never turn an extension into a documented quotation or position.
See `references/output-template.md` for the contract.

---

## Inputs

**Required:** the person's public record, as any of four source types — **local files or a
directory**; a **git repository URL**; a **plain file URL**; or a **docs site, wiki, or published
note collection**. Formats: PDF, EPUB, DOCX, TXT, Markdown, HTML, or transcripts; mixed is fine.
Where the corpus lives depends on the host (see **Host environment** below); if the location is not
given, ask for it rather than guessing. Anything remote is fetched and classified before Stage 1 —
procedure in `references/acquisition.md`, and skipping it is how you end up distilling a
repository's scaffolding, or someone's notes *about* the person, instead of the person.

**Optional:** a focus statement, e.g. "decision style in public controversies" or "overall
voice for analysis tasks". If omitted, default to overall identification.

Output quality is strictly bounded by corpus coverage, diversity, and signal density. If the
corpus is thin, you produce a smaller, honestly-scoped core — you never fabricate probes to
fill it out.

---

## Host environment

This skill makes no assumption about which agent runs it or what the filesystem looks like. Three
locations are host-dependent; resolve each **once, at the start of the run**, and reuse the
resolved paths throughout.

| What | How to resolve |
|---|---|
| **Corpus in** | Whatever the user points you at — and it may be **remote**, not a local path. Some hosts stage uploads in a fixed directory (on claude.ai, `/mnt/user-data/uploads/`); others expect a path or a working-tree location. If unstated, ask. Network access and `git` are host capabilities: **check them, never assume them**, and if either is missing say so and ask for the material locally (`references/acquisition.md`). |
| **Work dir** | Create one. Default to `persona_work/` under the current working directory. Prefer a host-provided scratch or temp location when one exists. Create it before Stage 1 — nothing later works without it. |
| **Persona out** | Wherever the host delivers artifacts to the user (on claude.ai, `/mnt/user-data/outputs/`); otherwise the current working directory, unless the user says otherwise. The delivered project is `<slug>-perspective/`; its runnable skill root is `<slug>-perspective/.agents/skills/<slug>-perspective/`. |

Two further portability rules:

- **Tools are optional, never assumed.** Where a stage suggests a document-reading tool, a
  converter, or a companion skill, treat it as a preference. If the host does not have it, fall
  back to the stdlib route named alongside it. Every script in `scripts/` is standard-library-only
  and runs under any Python 3 — no install step, no network.
- **If the work dir lands inside a git repository**, ensure it is ignored before writing to it.
  It fills with extracted full text of the source corpus, which must not be committed. This
  repository's own `.gitignore` covers the default name.

---

## Pipeline (five stages, run in order)

Each stage has a detailed reference file. Read the reference before executing that stage the
first time; the summaries below are orientation, not the full procedure.

**Acquisition precedes Stage 1.** If the corpus is remote, fetch it, separate the person's material
from the container's scaffolding with the user's confirmation, and label every unit `firsthand` /
`secondhand` / `mixed` / `unknown` before ingesting anything → `references/acquisition.md`.

### Stage 1 — Ingest & segment

Before trait extraction, freeze a metadata-only inventory grouped by underlying work or episode,
including related excerpts/retellings in the same group. Run `scripts/holdout_split.py` to make
train, development and final-test partitions. Construction, including register discovery, uses
train only. Development drives curation; final evidence stays sealed until a fresh-context final
assessment. Read [references/release-evidence.md](references/release-evidence.md) now for isolation,
baseline comparisons, split format and executable release requirements.
Read the corpus. Extract text with structure preserved (headings, speaker turns, timestamps).
Segment into coherent **clusters** — per work/chapter, per interview, per decision record, per
time period. Build an internal **coverage map**: domains covered, dialogue-vs-monologue ratio,
decision density, temporal spread. This map drives later auto-weighting and the honest coverage
report. Run `scripts/corpus_clean.py` over `raw/` first — converted corpora lose ligatures, wrap
words across lines, and carry markup residue, none of which looks like damage but all of which
corrupts the expression pass silently. Then cut the clusters with `scripts/segment.py`, which
writes a schema-valid `clusters/manifest.json` and reports the firsthand ratio that sets the core
budget's ceiling. → See `references/pipeline.md` (Stage 1) for extraction routing by file type, and
`references/schemas/` for the validatable shape of every intermediate JSON artifact.

### Stage 2 — Multi-granularity extraction
Run a discovery pass, then three measurement passes:

- **Pass A0 — register discovery** *(new in 3.0; runs before everything else in Stage 2)*. Measure
  every cluster on the same feature vector, cluster the clusters, and let the corpus tell you how
  many voices it contains. `scripts/register_discover.py` writes `registers.json` — a distance
  matrix, a proposed family assignment, and the separation statistics behind it. Nothing downstream
  is valid until this runs: a single pooled baseline over a multi-register corpus is not a
  measurement of the person but an average of two of them, and it is invisible in the output
  because it looks like a perfectly ordinary set of numbers. The script measures; **you** name the
  families, nominate a default, order any within-family gradient, and record where a family
  boundary cuts across a cluster. Those fields are hand-added and the file is unfinished without
  them. `n_registers = 1` is a legitimate, common result — record it and move on; what is not
  legitimate is never asking.
- **Fine-grained expression pass** — countable features *and their modulation*, **measured per
  register family** and only then pooled. Run `scripts/style_metrics.py` on each family (and
  per-cluster) so these are measured, not guessed — or `scripts/zh_metrics.py` for a Chinese
  corpus, where the Latin tokeniser returns zeros. Capture how features shift, not just their
  averages, and record the **cross-family gap** for every feature: a gap wider than the
  within-family spread is the thing `voice.md`'s no-pooling rule is built out of.
- **Coarse-grained projectible-regularity pass** — recurring thought-moves and decision
  heuristics. A regularity qualifies only if it (a) appears in ≥2 independent clusters and
  (b) predicts stance on held-out questions from the same corpus. Store with source clusters and
  example passages.
- **Interactional & cost-bearing pass** (prioritize dialogue and decision records) — standing
  commitments, refusals, and moves (concede / reframe / dig in / shift footing). Flag every case
  where the *convenient or generic* response diverges from the person's *attested characteristic*
  response. These flags are gold.

**Eight element classes, and ids that carry their class.** 3.0 splits two classes out of
`regularity`, because collapsing them cost the produced persona its two most operational assets.
**`procedure`** is an *ordered* method step — it requires `order`, `precondition`, and `on_fail`,
since an unordered pile of heuristics gives a host agent no way to know what runs first, so it
applies them all at once and the guard whose entire value was firing first never fires.
**`verdict`** is a standing judgment about a named object — it requires `object`, `judgment`, and
`corpus_hits`, and (like any regularity) ≥2 clusters, so that a judgment made once in an aside
stays an aside. Element ids are now class-prefixed — `PROC CR VD PR IM MOD PP` — and the prefix
must agree with the `type`; a flat `e017` makes the class distribution unreadable, which is
precisely what the elevation rule and the Stage 5 presence assertion both have to read.

Pull evidence with `scripts/kwic.py` rather than `grep` — extracted prose puts whole paragraphs on
single lines, so `grep` returns the paragraph and misses matches that straddle a break. Its
`--count` mode is the ≥2-independent-clusters check made cheap.
→ Full taxonomy and what-to-look-for: `references/extraction.md`.

### Stage 3 — Multi-probe curation & deletion *(the main differentiator — do this carefully)*
Score every extracted element 0–1 on a weighted composite:

| Probe | Weight | What it measures |
|---|---|---|
| Projectibility | **0.30** | held-out prediction performance within the corpus |
| Cost / refusal signal | **0.25** | sits on a documented divergence between incentive and characteristic move |
| Expressive match | 0.20 | alignment with the person's *measured* style distribution, including variation |
| Interactional visibility | 0.15 | observable in dialogue or exchange |
| Preoccupation / gravitational weight | 0.10 | the theme they keep returning to across unrelated clusters |

**Deletion rule (hard):** cut any element scoring below **0.55** composite, *and* cut any element
— regardless of score — that introduces generic language, forces meta-commentary, or conflicts
with a higher-scoring core voice feature. No smoothing, no averaging across low-value material.
Log every keep/cut with its probe scores and a one-line reason so the decision is auditable.

**Elevation rule (hard):** the weights alone are not enough — style metrics are abundant and
cost-refusals are sparse, so raw ranking lets volume crowd the fingerprints out. So rank survivors
by **class priority first** (procedure ≈ cost-refusal ≈ verdict ≈ projectible regularity >
interactional > variation > preoccupation > stable style), then by composite *within* class.
Procedures, cost-bearing refusals, standing verdicts, and variation/modulation patterns get first
claim on core space and are retained even when sparser than style metrics; pure style averages may
fill **at most ~20%** of the core. Everything else attested goes to references.

**Core budget (computed, not fixed):** size the core to the diagnostic material that survived,
bounded by what the corpus supports — `supply = 2,200 + 250·min(n_cost_refusal,6) +
180·min(n_projectible,7) + 200·min(n_procedure,5) + 150·min(n_verdict,8) +
140·min(n_interactional,5) + 120·min(n_variation,4)`, clamped between a **3,000 floor** and a
`coverage_map`-derived ceiling (**4,000** thin or `firsthand_ratio` < 0.50 / **6,000** mid /
**7,500** large and multi-period). The two new terms are priced high because procedures and
verdicts are the classes a host agent can actually *execute*, and the 2.x ceilings were set before
they existed — a corpus rich in both saturated a supply term it had no room to spend. Preoccupation
and style still contribute nothing to supply. Landing under the floor means the pool is too thin,
not that the core needs filler: revisit the 0.45–0.55 cut band for diagnostic classes only, then
ship reduced-scope and say so.

**Every budget in this skill is denominated in tokens, so count them with one counter.** Run
`scripts/token_count.py` and record the tokenizer in `scores.json`, where it is now a required
field. A budget without its tokenizer is a number without a unit: the same package measures roughly
twice as large in Chinese as in English under a word-based count, and "4,000" then silently means
two different sizes in two runs of the same skill. → The formula, the floor procedure, the standing
module budgets, worked scoring examples, weight-tuning, and the log format: `references/scoring.md`.

### Gate before Stage 4 — mandatory, and it feeds back *(do not skip)*
Assembly is downstream of passing two gates, plus a third whenever the corpus carries more than one
register family. Their results are logged to the persona's `fidelity-ledger/provenance.md` and are
**used to adjust inclusion and weighting** — they are control signals, not just reports:
- **Projection gate** — run the development projection test (procedure in `fidelity-tests.md`) on the
  top-ranked projectible regularities *now, before assembly*. If it misses threshold, re-curate:
  down-weight the over-fit elements, promote better-generalizing ones, or narrow the persona's
  claimed scope — then re-score. Loop until the revised or narrowed candidate passes on development evidence.
- **Cost gate** — inventory every attested incentive-vs-characteristic divergence from Stage 2 and
  confirm the high-signal ones survived curation and are slated for the core. Any missing one is
  re-included or elevated *before* assembly, not after.
- **Discrimination gate** — **mandatory whenever `registers.json` reports `n_registers > 1`**, and
  re-triggered by any cluster merge. Through 2.x this test ran "if the core claims registers", which
  put the gate downstream of the distiller's own judgment: it fired only when someone had already
  noticed the very thing it exists to detect. Now the corpus decides. `register_discover.py`
  proposes and this test disposes — when they disagree, **reduce** the number of families rather
  than re-running discovery at a looser threshold until the numbers come out as hoped.

This loop is what stops a style-heavy, low-projectibility set from reaching the (structurally
correct) template and inheriting its bias.

**Results go stale, and staleness is now recorded rather than remembered.** Curation is a loop: a
gate sends the set backwards, clusters get merged, an element is demoted two batches after the score
that justified keeping it. Every result in `fidelity.json` therefore carries the `content_hash` of
the package it was computed against, plus a `stale` array naming results invalidated and not yet
re-run. Mark staleness at the moment of the change, not at the end, when it will be forgotten. A
stale style-match result may ship if the coverage report says so; a stale projection or cost gate may
not. → `references/fidelity-tests.md`.

### Stage 4 — Assemble core + package references + Fidelity Ledger
Create one self-contained project at `<persona-out>/<slug>-perspective/`. Write the runtime core to
`.agents/skills/<slug>-perspective>/SKILL.md`, its host-facing depth modules to
`.agents/skills/<slug>-perspective>/references/`, and the human-facing audit trail to the
project-level `fidelity-ledger/` (provenance, budgets, gate and test results). The inner skill
directory must exactly match the core frontmatter `name:`. The core follows a fixed template and obeys the
no-meta rule absolutely. Concrete, attested episodes and decision-record fragments that did not
make a cluster module live in `fidelity-ledger/episodic.md` — attested but not reasoning material,
so it sits with the audit trail rather than the host-agent-facing package, and the host agent never
loads it. Provenance, scoring, fidelity records, and episodic material are never written under
`references/`; they go only to `fidelity-ledger/`, which the host agent does not load.

The core's host note must say to load `references/scope.md` before applying the persona. Keep
attested judgments conditional on domain, date and circumstances. A later position cannot
silently answer a question about an earlier period.

The core's "Loading depth (host-agent note)" block must also carry the mandatory fourth line: a
real-world-retrieval instruction, stated as host-agent operational guidance rather than persona
voice, distinguishing the two retrieval axes a produced skill actually has. `references/` answers
questions about **the person's own analytical apparatus** — their frameworks, moves, and voice —
by searching the runtime skill's own files; that is the corpus's SOURCE OF TRUTH, and it is closed
to the outside world by design. The project-level `fidelity-ledger/` is for human audit and is never
runtime context. It is a categorically different
question whether some **real-world fact the answer depends on** — an exact quotation, a current
event, the present text of a law, a detail of the user's own situation, anything the corpus
postdates or never covered — is true, and the corpus is not evidence about that; the host agent
must retrieve it from the live world before running it through the persona's frame, the same as it
would for any other skill. Skip the line only if the corpus is closed to all outside reference by
design, and say so explicitly if you skip it. → Exact wording and placement: the fourth
Loading-depth line in `references/output-template.md`.

**The two standing modules are layered templates, not free-form prose.** `frameworks.md` runs
§0–§7 and `voice.md` runs §0–§11, and both structures are universal — they are asked of every
subject, and a section the corpus cannot fill is marked absent rather than deleted, because an
absence a reader can see is information and a missing heading is not. `frameworks.md`'s ordering is
the substantive claim: **§1 Method** (how material is handled) and **§2 Epistemology** (what counts
as knowing, and what licenses a prediction) come *before* **§3 Ontology** and **§4 standing
verdicts**, because a persona given only conclusions can restate them and cannot extend them. Get
the method and the epistemology in place and the verdicts become derivable; ship the verdicts alone
and you have built a quote database with opinions. `voice.md` opens with the register structure for
the same reason — §0 families, §1 within-family gradient, §2 the cross-family gap table, §3
no-pooling markers — so that a host agent has to choose a register before writing a sentence, rather
than discovering afterwards that it wrote in the average of two.

Both modules are **standing and co-equal**: `frameworks.md` (what the person thinks with)
and `voice.md` (how the person sounds); `episodic.md` is not a third — it lives in `fidelity-ledger/`,
not `references/` (see below). The 20% style cap keeps the core a fingerprint, but a
fingerprint is not enough to *write* as someone at length, so the rest of the expressive system —
favored and **avoided** constructions, modulation rules, register range, lexical fingerprint, the
measured `style_metrics.py` baseline, and anti-drift pairs — is written to `voice.md` from firsthand
clusters only, and the core's loading block tells the host to load it before any sustained prose.
The cap routes surplus style there; it does not discard it. Material cut under the 0.55 rule stays
cut — `voice.md` takes the demoted, never the deleted.

`fidelity-ledger/episodic.md` is the residual record: concrete, attested, one-off material —
specific incidents, anecdotes, and decision-record fragments — that is real and citable but did not
clear a cluster module's own 1,800-token floor, or a decision/aside demoted from a cluster module
for space. It holds *events*, not concepts or expression: a named construct belongs in
`frameworks.md` even if it surfaced in a single aside, and any expression or modulation element
belongs in `voice.md` regardless of where it was demoted from. If it isn't a specific attested
happening someone could point to, it does not belong in `episodic.md`. It lives in `fidelity-ledger/`
rather than `references/` because it is attested-but-unranked source material, not something the
host agent should load into the embodiment context — the same reasoning that keeps provenance out
of `references/`.

**The cluster modules are budgeted too, by the same logic as the core.** Size each one with
`scripts/cluster_budget.py` before writing it — a flat band is a guess that a rich cluster under-uses
and a thin one is invited to pad, and it is how a package ends up at a third of the size its own
spec asked for without anything catching it. Module length tracks *conceptual density, not word
count*: it is a function of the constructs, moves and evidence routed to the cluster, plus a
fencing cost that scales with how many sibling modules it must distinguish itself from, plus a
damped corrective for corpus mass, plus a per-register price, since a cluster whose material arrives
in two registers has to teach both. The verdict carries more information than the number: **FLOOR**
(under 1,800 — this cluster has not earned a module; fold it into a sibling or demote it to
`fidelity-ledger/episodic.md`, never pad) and, when the input caps saturate, one of two opposite
remedies. If the overloaded cluster spans **two topic domains**, it was mis-segmented — **RECUT**,
back to `segment.py`. If it sits in **one domain** but carries two registers, re-cutting would
separate a subject from itself, so the answer is **SPLIT_IN_MODULE**: keep one module, declare an
internal A/B register split with a no-pooling header, and give separate style guidance for each. 2.x
had only the single `recut_flagged` boolean and so gave the wrong answer half the time; check
`shared_domain` against the application count rather than by impression.
→ Exact templates, the `voice.md` spec, and directory layout: `references/output-template.md`.
The module formula, its counting rules, the standing-module budgets, and calibration status:
`references/scoring.md`.

### Stage 5 — Final fidelity verification *(the gates already ran at 3.5; this confirms the assembled core)*
- **Independent final projection**: after confirming the development gate on the final bytes,
  run the reserved final test once in fresh prediction contexts, paired with a minimal persona
  baseline on the same model/settings. Save prompts, both answers and item grades. A failure
  blocks release; if used for revision, retire that set into development and obtain a new test.
  The final test is never the repeatedly optimized development set.
- **Cost / presence assertion** — re-confirm every high-signal divergence landed in the core, and
  assert the hard minimum: **if the corpus contains any high-signal cost-bearing refusal or
  interactional move, the core must contain at least one.** Failing this blocks delivery — go
  re-curate; it is the most common way a core ends up articulate but generic.
- **Style-match test** — generate sample passages under the core's expression rules **plus
  `voice.md`** (that pair is the sustained-prose configuration, so that is what gets tested),
  including one contested prompt and one long enough to drift; re-run `style_metrics.py`; compare
  feature distributions *and modulation* against held-out originals; and confirm nothing on the
  avoid-list appears.
- **Discrimination test** *(mandatory whenever `n_registers > 1`; also re-run after any cluster
  merge)* — `scripts/discrimination_test.py` samples passages, hides the labels, and you classify
  them blind using `--registers registers.json` and family labels. Also test whether novel audience/task/stakes prompts select and produce the right family, recording `register_selection` cases. The other three checks all ask whether this reads like the person; none asks whether
  the person's registers can be **told apart**, and a passage can match the aggregate baseline
  perfectly while being indistinguishable from every other register the core promises. Below 0.70,
  collapse the families into one honest voice rather than shipping a distinction the persona cannot
  perform.
- **Mechanical package validation** — run `scripts/validate_package.py <project> --release --fidelity <ledger>/fidelity.json` over the outer produced project directory. This enforces result hashes, split integrity, baseline comparisons and required gates as well as structure. See `references/release-evidence.md`; draft structure checks omit `--release`.
  It checks what a reader will not: ledger material sitting inside a runtime reference, a load-list
  in the core pointing at a cluster module nobody wrote, an `episodic.md` that is empty without
  saying why, implementation language leaking into the core's own description. Judgment calls come
  back as warnings rather than as false certainty; `--strict` promotes them. Pass `--headings` with
  the anchors you require — the checker will not impose English headings by default, since a core may
  be written in the subject's own language. A structural omission is the one defect class that
  survives careful reading, because there is nothing on the page to notice.
- **Scope boundary checks**: record answers for an attested judgment in its period, an earlier
  period with a different position, and changed conditions requiring extrapolation. Check that
  dates and conditions survive and extensions are not presented as documented positions.
- **Name audit** — run `scripts/name_audit.py --package <dir> --corpus <dir>`. It looks for every
  name the package uses **literally in the corpus**, and separates heading-like appearances from
  ordinary prose. The failure it catches has a specific mechanism: a neat diagnostic label invented
  during distillation, or lifted from an editor's chapter heading, quietly acquires the authority of
  the person's own coinage — and the persona then uses a term its subject never used. An editor's
  heading is not attestation. Thin support is a finding, not a formality.
- **Token accounting** — run `scripts/token_count.py` over the package and record realised sizes
  against the budgets in `scores.json`, under the estimator it declares. This is the only data a
  future recalibration of the coefficients has to work from, and a package that shipped at a third
  of its budgeted depth is otherwise indistinguishable from one that shipped correctly.
- **Real-world-retrieval line present** — confirm the core's "Loading depth" block carries the
  mandatory fourth line (or an explicit, justified skip) telling the host agent to retrieve
  real-world facts from outside the repository before running them through the persona's frame,
  and that it is written as host-agent guidance, not persona voice. A core missing this line reads
  as if the corpus were evidence about anything the user might ask — the same failure mode as
  fabricating material, just aimed at the world instead of the person.

Log all results to `fidelity-ledger/provenance.md` and the coverage report. If a check falls below
threshold, revise or narrow the core and re-test under the independent evaluation rules, or surface it to the user for corpus
improvement — never paper over it. → Procedures, thresholds, and reporting:
`references/fidelity-tests.md`.

---

## Output

A directly usable local Agent Skill project:

```text
<slug>-perspective/
├── .agents/
│   └── skills/
│       └── <slug>-perspective/
│           ├── SKILL.md
│           └── references/
│               ├── clusters/
│               ├── scope.md        # host-facing domain, period and attribution boundaries
│               ├── frameworks.md
│               └── voice.md
└── fidelity-ledger/
    ├── provenance.md
    └── episodic.md
```

Opening the outer directory as a project makes the persona discoverable without copying or
installing it. The inner skill-directory name must match `SKILL.md` frontmatter `name:` exactly.

- **`.agents/skills/<slug>-perspective>/SKILL.md`** — the core embodiment artifact, sized to the **computed budget** (typically
  3,000–6,000 tokens; floor 3,000, ceiling 4,000 / 6,000 / 7,500 by corpus), front-loaded (compaction
  truncates from the end, so highest-value fingerprints come first).
- **`.agents/skills/<slug>-perspective>/references/`** — modular files sized for on-demand loading, **all host-agent-facing** (this is
  what the persona loads at runtime; it never contains provenance, scores, fidelity results, or
  episodic material). Two are **standing, cross-corpus modules of equal status**: `frameworks.md`
  (§0–§7: how to use the file, method, epistemology, ontology, standing verdicts, argumentative
  moves, the personal scale, and an index of named constructs) and `voice.md` (§0–§11: the register
  families and their gradient, the cross-family gap table, no-pooling markers, guardrails, then
  favored and *avoided* constructions, modulation, lexical reach, openings and closings, anti-drift
  pairs, and the measurement provenance). The rest is per-source: one module per high-value source
  cluster. Sizes: cluster modules are **computed per cluster** by `scripts/cluster_budget.py` (floor
  1,800, hard ceiling 6,000; typically 2,000–4,500 — a cluster under the floor is folded into a
  sibling or demoted to `fidelity-ledger/episodic.md` rather than written thin); `frameworks.md` and
  `voice.md` are **also computed** rather than a flat ~4,000, from the constructs, verdicts, moves
  and register families actually routed to them, clamped to 2,000–7,000.
- **`fidelity-ledger/`** — **human-facing and outside `.agents/`**, never loaded by the host agent: `provenance.md`
  mapping each core element to its source, the computed budgets, and the gate/final fidelity
  results; and `episodic.md`, concrete attested one-off material — specific incidents, anecdotes,
  decision-record fragments — that did not clear a cluster module's floor. Both are attested but not
  reasoning material, so neither belongs in the host-agent-facing package. Uncapped, since it is an
  audit package and its completeness matters more than its size; `episodic.md` keeps its own soft
  ~4,000 guide so it stays a residual record rather than growing into a dumping ground.

Name the output directory with a user-supplied or auto-generated slug + `-perspective`
(e.g. `deneen-perspective`), and write it to the persona-out location resolved at the start of the
run. If a persona of that name already exists, offer incremental **fold-in** of the new corpus with
re-curation rather than a blind overwrite.

Then hand the user a short **coverage report** (this is where honesty lives): what the corpus
covered well, where it was thin, the fidelity-test scores, and any domains where the persona
should be trusted less. Keep this report *out* of the core `SKILL.md`.

---

## Scope, defaults, and judgment

- **Small or low-diversity corpus** → smaller core + explicit coverage report. Never hallucinate
  missing probes to hit a size target.
- **Heavily dialogue vs. heavily monologic corpus** → auto-raise the interactional pass weight for
  dialogue-rich corpora; lean harder on projectible-regularity extraction for monologic ones.
- **Stylistically split body of work** (career phases, genres, venues) → Pass A0 will find it; treat
  the families as the persona's real structure rather than noise to average out. Two or three is
  workable; more than three usually means the boundary is being drawn on topic rather than on voice,
  and the discrimination gate will say so.
- **Contradictory signals across time periods** → treat as documented evolution/tension *only if*
  projectibility stays high; otherwise drop the weaker signal rather than blending them into mush.
- **Narrow user focus** (e.g. "only decision style") → re-weight scoring toward the requested
  facet and prune off-focus probes.
- **Modes:** default is full distillation. If the user says "analyze only" or "let me review
  first", run Stages 1–3 and hand them the ranked extraction + scoring log, then stop. If they
  point you at an existing persona, run in fold-in/update mode.

This skill operates only on public material the user has the right to use, and produces a
perspective/thinking-style tool — for analysis, study, and ideation in the person's documented
frame. It is not for deceptive impersonation, forged attribution, or passing off invented
statements as the person's real words. If a request bends that way, say so and reshape it toward
legitimate perspective work.

## Suggested execution order for the engineer inside this skill
Because Stage 3 (scoring + elevation + deletion) and the tests encode the real value, get them
right first, before polishing extraction breadth. And note the control flow is a **loop, not a
straight line**: score → gate (projection + cost) → re-curate / re-weight → assemble → final
verify. Assembly is always downstream of passing the gates; if the gates fail, you go back to
curation, never forward to the template. The remaining stages can reuse familiar modular-skill
patterns (lean front-loaded core, on-demand reference files, tight token budgets).

## Reference files
- `references/acquisition.md` — before Stage 1: resolving remote source types, fetching, separating
  corpus from container, the attribution classification and its three hard rules, source
  independence, wiki chunking, and honest degradation when the host has no network.
- `references/pipeline.md` — Stage 1 & full-pipeline mechanics, extraction routing by file type,
  the coverage map schema.
- `references/extraction.md` — Stage 2: Pass A0 register discovery and per-family measurement, the
  expression-DNA taxonomy, the eight element classes with their class-prefixed ids and admission
  tests, projectible-regularity verification, and the cost-bearing / interactional catalogue.
- `references/scoring.md` — Stage 3: the five probes in depth, the core / cluster / standing-module
  budget formulas and their coefficients, worked scoring examples, the deletion rule, and the
  audit-log format.
- `references/output-template.md` — Stage 4: exact core `SKILL.md` template, the layered
  `frameworks.md` §0–§7 and `voice.md` §0–§11 specs, the Fidelity Ledger layout, and the
  negative-space rule for sections a corpus cannot fill.
- `references/release-evidence.md`: before Stage 1 and at release, grouped splits, isolated predictions, baselines and machine artifact contract.
- `references/fidelity-tests.md` — Stage 5: projection / cost / style-match / discrimination
  procedures, thresholds, the sampling-description rule, the re-test obligation, and reporting.
- `references/schemas/` — JSON Schema (draft 2020-12) for every intermediate artifact
  (`clusters/manifest.json`, `coverage_map.json`, `registers.json`, `extractions.json`,
  `scores.json`, `fidelity.json`, and the `passages.json` input to `holdout_split.py`). The snippets
  in the prose references are illustrative and some carry `//` comments; these schemas are
  authoritative and parseable. Consult one before writing the corresponding artifact. Two scripts
  write shapes that validate as-is — `register_discover.py` against `registers.schema.json` and
  `cluster_budget.py` against the `cluster_budgets` item shape — so a validation failure there means
  the script and the schema have diverged.

## Scripts
- `scripts/style_metrics.py` — computes countable expression features (sentence-length
  distribution, hedge/booster rates, punctuation rhythm, lexical diversity, person-reference
  ratios, top content terms/bigrams) for a text file or directory. Stdlib only; no install.
- `scripts/zh_metrics.py` — the same feature classes for a **Chinese** corpus, in the units
  Chinese prose is measured in: sentence length in 汉字, Chinese hedges/boosters, punctuation
  rhythm, person-reference ratios, character-n-gram fingerprint, and a discourse-scaffolding
  absence check that feeds `voice.md`'s avoid-list. `style_metrics.py` tokenises on `[A-Za-z]`
  and returns zeros on CJK, so reach for this one whenever the corpus is Chinese. Ships with no
  term list — pass the subject's own vocabulary via `--terms` rather than baking it in.
- `scripts/holdout_split.py` — grouped train/development/test split before extraction for
  the held-out projection test. Requires passage objects with `id` and work/episode `group`
  (see `references/schemas/passages.schema.json`), plus `--out`. Optional `--stratify` uses
  consistent group domains and reports thin strata with no evaluation coverage.
- `scripts/corpus_clean.py` — **Stage 1.** Extraction-damage census and repair: lost fi/fl/ff
  ligatures, words wrapped across lines by justified typesetting, and EPUB/markup residue. All three
  leave fluent, readable text that measures wrong, so nothing catches them by eye. Reports by
  default, writes only with `--fix`, and separates a confirmed problem from a mere screen signal.
  Run it before any metrics; a baseline taken over damaged text is not a baseline.
- `scripts/segment.py` — **Stage 1.** Cuts the corpus into clusters from a spec of line numbers or
  regex boundaries, strips repeating running headers, and writes a `clusters/manifest.json` that
  validates against the schema. Guards the two silent errors of hand-cutting: boundary drift, which
  makes one "cluster" average two registers, and editorial bleed, which counts introductions and
  endnotes as the subject's own words. `--dry-run` checks boundaries before writing.
- `scripts/kwic.py` — **Stage 2.** Keyword-in-context evidence retrieval. Extracted prose puts whole
  paragraphs on single lines, so `grep` returns the paragraph and misses matches straddling a break;
  this normalises whitespace and returns fixed-width windows, with `--json` writing straight into an
  element's `evidence` field. `--count` gives hits per cluster — the ≥2-cluster corroboration check.
  The pattern is a Python regex: `a|b`, never `a\|b`.
- `scripts/cluster_budget.py` — **Stage 4.** Sizes each `clusters/*.md` module from the constructs,
  moves and evidence routed to it, the number of sibling modules it must fence itself off from, and
  a damped corpus-mass term — the same supply→clamp shape the core budget uses, because a flat band
  is how a package silently ships at a third of its intended depth. Returns a verdict rather than a
  bare number: **OK**, **FLOOR** (this cluster has not earned a module — fold or demote, never pad),
  **RECUT** (the caps saturated across two topic domains, so it was mis-segmented and belongs back at
  `segment.py`), or **SPLIT_IN_MODULE** (saturated within one domain, so re-cutting would separate a
  subject from itself — declare an internal A/B register split instead). Pass `--registers` and
  `--shared-domain`, or `--coefficients` to override the defaults. `--json` writes the
  `cluster_budgets` array for `scores.json`.
- `scripts/discrimination_test.py` — **gate, Stage 3.5 / Stage 5; mandatory when `n_registers > 1`.**
  Blind register-separation test. Samples passages, hides the labels, scores your blind
  classification, and names the confused pairs. Answers a question the other three tests structurally
  cannot: not "does this sound like them" but "are these registers actually distinct". Use
  `--mask-names` — recognising a cast is not recognising a register.
- `scripts/register_discover.py` — **Stage 2, Pass A0.** Measures every cluster on one feature
  vector, builds the pairwise distance matrix, and proposes a register-family assignment with its
  separation statistics, writing `registers.json`. This is the pass that decides whether the corpus
  has one voice or three; without it, a pooled baseline over two registers is an average of two
  people that reads like an ordinary set of numbers. It measures only — naming the families,
  nominating a default, ordering the gradient, and flagging boundaries that cut across clusters are
  yours to add by hand, and the file is unfinished until they are there.
- `scripts/token_count.py` — **Stage 3 and Stage 5.** One explicit token estimator for every budget
  in the skill, declaring the model it used so `scores.json` can record it. Counts Han and kana
  characters separately from Latin words, because a word-based count understates a Chinese package by
  roughly half. `--calibrate` adjusts the per-character and per-word rates against a real tokenizer
  if you have one. Run it on the finished package and record realised size against budget — that
  comparison is the only calibration data the coefficients ever get.
- `scripts/validate_package.py` — **Stage 5.** Mechanical check of the produced project, including
  the `.agents/skills/<name>/SKILL.md` discovery layout: ledger
  material inside a runtime reference, a core load-list pointing at a module nobody wrote, a
  near-empty file that does not say why, implementation language in the core's description. Reports
  judgment calls as warnings instead of pretending they are settled; `--strict` promotes them.
  `--headings` supplies the required core heading anchors — omitted by default, deliberately, so the
  checker cannot impose English headings on a core written in the subject's language. It catches the
  one defect class careful reading cannot: the thing that is simply not there.
- `scripts/name_audit.py` — **Stage 5.** Back-checks every name the package uses against **literal
  corpus hits**, separating heading-like appearances from ordinary prose. A tidy label invented during
  distillation, or inherited from an editor's chapter heading, otherwise acquires the authority of the
  person's own coinage, and the persona ends up confidently using a term its subject never used.
  Without `--names` it harvests candidates from the package's own bold runs, quoted runs, title marks
  and headings — so it audits what you wrote, not what you remember writing.
