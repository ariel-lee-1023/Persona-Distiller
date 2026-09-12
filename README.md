# Persona-Distiller

**Turn one person's public record into a persona another agent can *embody*.**

`Persona-Distiller` is an [Agent Skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) that takes a corpus of one person's material — books, essays, transcripts, interviews, decision records — and distills it into a compact, embodiment-ready perspective skill. The delivered project already contains `.agents/skills/<slug>-perspective/`, so opening the project makes its lean core `SKILL.md` and modular `references/` package directly discoverable.

Not a biography. Not a summary. Not a quote database. The output is optimized so that a reader familiar with the person's record cannot easily tell its output apart from the real thing, on public topics the corpus actually covers.

---

## What makes it different

Most voice-cloning prompts reach for what is easy to count — sentence length, favourite punctuation, hedge-word frequency. Those features are cheap to measure and almost everyone's are somewhat generic. This skill deliberately spends its budget elsewhere:

| Signal | Why it individuates |
|---|---|
| **Ordered procedures** | What they do *first* with a problem, and what they do when that fails |
| **Cost-bearing refusals** | Positions the person held *against* their own incentive |
| **Standing verdicts** | The judgments they reach repeatedly, by name, about specific objects |
| **Patterns of variation** | How their register shifts under pressure, audience, or stakes |
| **Interactional moves** | How they concede, reframe, dig in, or shift footing in exchange |
| **Projectible regularities** | Thought-moves that actually predict stance on held-out material |

Three design commitments follow from that:

1. **Recognition is a family resemblance.** Identity shows up redundantly, at different grains, through overlapping probes. The skill does *not* partition a person into tidy mutually-exclusive buckets, and does *not* dedupe a trait away just because it surfaced in three passes. Redundant corroboration across probes is strength.

2. **Delete without mercy.** A tight ~4k-token core that nails the fingerprints beats a comprehensive 15k-token one that reads like everyone. Anything scoring below threshold, reading as generic, or conflicting with a higher-scoring voice feature gets cut — not softened, not averaged in.

3. **One person is not automatically one voice.** A body of work written across a career, or across
   genres, or for different audiences, often contains two or three sharply distinct registers.
   Pooling them produces a baseline that describes nobody — a mean sentence length halfway between
   two habits the person never had — and every later measurement quietly inherits that fiction. So
   the register structure is *discovered first*, before any feature is measured, and a blind
   separation test has to confirm the families can actually be told apart before the persona is
   allowed to promise them.

Spending the budget elsewhere is not the same as throwing style away. Measured expression that survives the deletion rule but loses the competition for core space is *relocated*, not discarded: it goes to `references/voice.md`, a standing module the host loads before writing sustained prose in the voice. The core stays a fingerprint; the voice stays complete.

### The honesty split

The generated persona contains **no uncertainty disclaimers, no provenance hedging, no meta framing**. Those move a reader out of the voice and destroy identification.

Detailed citations, confidence and test history remain in the human-facing Fidelity Ledger.
A compact host-facing `references/scope.md` is loaded with the core to preserve supported domains,
periods, conditions on standing judgments and the boundary between attestation and extrapolation.
The expressive voice stays in the core; the host can distinguish a documented position from a new application.

---

## Installation

### Claude Code

```bash
git clone https://github.com/ariel-lee-1023/Persona-Distiller.git ~/.claude/skills/Persona-Distiller
```

Or, to install for a single project instead of globally:

```bash
git clone https://github.com/ariel-lee-1023/Persona-Distiller.git .claude/skills/Persona-Distiller
```

Restart Claude Code (or start a new session) and the skill will be discoverable.

### Claude.ai / Claude Desktop

Zip the repository contents so that `SKILL.md` sits at the root of the archive, then upload it under **Settings → Capabilities → Skills**.

```bash
cd Persona-Distiller && zip -r Persona-Distiller.zip SKILL.md references scripts requirements-release.txt
```

### Requirements

Python 3.9+ for the helper scripts. Release evidence validation also requires `jsonschema`:

```bash
python3 -m pip install -r requirements-release.txt
```

The remaining helpers and structural draft checks use the standard library. Validation runs
locally without network access. A release check fails with installation guidance if its schema
validator is unavailable; it never silently skips schema validation.

---

## Usage

The skill is model-invoked; it fires on natural phrasing. Upload the corpus, then say something like:

> Distill these into a perspective skill I can load.

> Build a persona skill from this author's collected essays.

> I want an agent that thinks like the person who wrote these transcripts.

You don't have to say the word "skill" for it to trigger.

### Modes

| Mode | How to ask | What happens |
|---|---|---|
| **Full distillation** *(default)* | Just upload and ask | Runs all five stages, delivers the persona directory + coverage report |
| **Analyze only** | "analyze only" / "let me review first" | Runs Stages 1–3, hands you the ranked extraction and scoring log, then stops |
| **Fold-in / update** | Point it at an existing persona | Re-curates against the new corpus instead of blindly overwriting |

### Optional focus statement

Narrow the distillation by naming a facet — *"decision style in public controversies"*, *"overall voice for analysis tasks"*. Scoring re-weights toward the requested facet and prunes off-focus probes. Omit it for overall identification.

### Accepted input

PDF, EPUB, DOCX, TXT, Markdown, HTML, and transcripts. Mixed formats are fine.

### Accepted corpus sources

The corpus does not have to be local files. Four source types:

| Source | Example | What happens |
|---|---|---|
| **Local path or directory** | uploaded files, a folder | Read directly |
| **Git repository URL** | a repo of essays or published notes | Shallow clone; the commit SHA is recorded |
| **Plain file URL** | a hosted PDF or essay page | Downloaded into the work directory |
| **Docs site, wiki, note collection** | MkDocs, Obsidian Publish, a wiki | Crawled **within the given path prefix only** — never the whole domain |

Anything remote goes through [`references/acquisition.md`](references/acquisition.md) before Stage 1,
which does two things the rest of the pipeline depends on.

It **separates corpus from container**. A repository or a site is a container: some of it is the
person's writing, the rest is the machinery that publishes it — READMEs, build config, templates,
navigation and index pages, other people's contributions. That classification is shown to you for
confirmation before extraction starts. Skip it and the worst case is silent: a fluent persona of the
repository's own scaffolding.

It **classifies attribution** — every cluster is labelled `firsthand`, `secondhand`, `mixed`, or
`unknown`. This matters because most online knowledge bases are secondhand, and a well-organised set
of someone's *notes on* a thinker is more attractive to distil than the thinker's actual books:
cleaner, better segmented, already thematic, and the wrong person. Three hard rules follow — style
metrics are never computed on secondhand text, a projectible regularity needs at least one firsthand
cluster, and a cost-bearing refusal attested only secondhand is flagged unverified and cannot satisfy
the Stage 5 presence assertion.

Network access and `git` are treated as host capabilities to check, not assume. Without them the
skill says so and asks you to supply the material locally — it never substitutes recollection of the
person for retrieved text.

---

## The pipeline

Five stages, run in order — with a **loop**, not a straight line, at its centre.

**Stage 1 — Ingest & segment.** Extract text with structure preserved (headings, speaker turns, timestamps). Segment into coherent clusters and build a coverage map: domains, dialogue-vs-monologue ratio, decision density, temporal spread.

**Stage 2 — Multi-granularity extraction.** A discovery pass first: **Pass A0** measures every
cluster on one feature vector, clusters the clusters, and lets the corpus say how many voices it
contains, writing `registers.json`. Then three measurement passes — fine-grained expression
(measured by `style_metrics.py` **per register family**, then pooled, never the other way round),
coarse-grained projectible regularities, and the interactional / cost-bearing pass. Every point where
the *convenient* response diverges from the person's *attested* response gets flagged. Those flags
are gold.

Elements are typed into eight classes, and their ids carry the class — `PROC CR VD PR IM MOD PP`.
Two of the eight are new in 3.0 and were previously buried inside "regularity": **`procedure`**, an
*ordered* method step that must declare its `order`, `precondition`, and `on_fail`, because an
unordered pile of heuristics gives a host agent no way to know what runs first — so it applies them
simultaneously and the guard whose whole value was firing first never fires; and **`verdict`**, a
standing judgment about a named object, which must name the `object`, the `judgment`, and its
`corpus_hits`, and which needs two independent clusters so that a judgment made once in an aside
stays an aside.

**Stage 3 — Multi-probe curation & deletion.** Every element scored 0–1 on a weighted composite:

| Probe | Weight |
|---|---|
| Projectibility | **0.30** |
| Cost / refusal signal | **0.25** |
| Expressive match | 0.20 |
| Interactional visibility | 0.15 |
| Preoccupation / gravitational weight | 0.10 |

Hard deletion rule below 0.55 composite. Hard elevation rule ranks survivors by *class priority first* — because style metrics are abundant and cost-refusals are sparse, raw ranking would let volume crowd the fingerprints out. Pure style averages may fill at most ~20% of the core.

**Gate before Stage 4.** Assembly is downstream of passing a **projection gate** (held-out
prediction), a **cost gate** (every high-signal divergence accounted for), and — whenever the corpus
carries more than one register family — a **discrimination gate** (the families can be told apart
blind). Gate results are *control signals*, not reports — failing one sends you back to re-curate,
never forward to the template. Through 2.x the discrimination test ran "if the core claims
registers", which put the gate downstream of the distiller's own judgment: it fired only when someone
had already noticed the very thing it exists to detect. Now the corpus decides, and results carry the
`content_hash` of the package they were computed against, so a score invalidated by a later merge is
mechanically identifiable as stale rather than a matter of anyone's memory.

**Stage 4 — Assemble.** Core `SKILL.md` plus the `references/` package, following a fixed template, obeying the no-meta rule absolutely. Module sizes are computed here too, by `scripts/cluster_budget.py`, and the reasoning is worth stating because a flat band is the obvious thing to write and the wrong thing to write. What a cluster module has to deliver is a working part of someone's thinking, so its terms are the things that constitute one — the apparatus the cluster uses, the moves it makes, the applications it commits to, the fragments kept as evidence — and each is capped, because the fifth instance of a move documents what the first three already established and the twelfth only confirms that the person had a habit. One term is not about the cluster in isolation at all: the more sibling modules a package carries, the more each one must spend marking off what it is *not*, so the fencing cost rises with sibling count and the package gets more expensive per module precisely as it gets better. Corpus mass enters last, under a square root, deliberately damped, because it is the strongest available proxy for the wrong quantity — across the calibration set module length correlated +0.82 with retained fragments and +0.70 with the cluster's own constructs, but only +0.30 with word count, so a rule leaning on mass would size a module by how much the person published rather than by how much of them is in it. The coefficients were not picked in advance either; they were recovered by fitting modules already written by hand and already judged faithful, which is the only calibration target available when the quantity you are trying to predict is "enough to carry the person". Floor and ceiling are then applied to that estimate rather than built into it, because how much material a cluster holds and how much a host will load are unrelated facts, and folding them into one expression lets each hide the other. Keeping them apart is what makes both limits informative: a supply under the floor is not a small module but a failed one — fold the cluster into a sibling, or demote it to `episodic.md` — and a cluster that saturates the input caps is carrying two registers and goes back to `segment.py`, since buying the space back by deleting evidence would fix the number and lose the person.

One refinement in 3.0 turns out to matter more than its size suggests. Saturating the input caps has
two opposite remedies, and 2.x had a single boolean for both, so it gave the wrong answer roughly half
the time. If the overloaded cluster spans **two topic domains**, it was mis-segmented and belongs back
at `segment.py` — that is the **RECUT** case. But if it sits in **one domain** and is overloaded
because the material arrives in two registers, re-cutting would separate a subject from itself; the
answer is **SPLIT_IN_MODULE** — keep one module, declare an internal A/B register split with a
no-pooling header, and give separate style guidance for each. The variable the decision turns on is
whether the topic is shared, which is checkable against the application count rather than by
impression. Calibration: ten modules against one 630k-word corpus, mean error 3.8%, max 6.0% —
structure settled, coefficients provisional, and `--coefficients` exists so a future recalibration
does not require editing the script.

**Stage 5 — Final fidelity verification.** Projection re-check, cost/presence assertion, style-match
test, blind discrimination test, and three mechanical checks: `validate_package.py` (no ledger
material inside a runtime reference, no load-list pointing at a module nobody wrote, no near-empty
file that fails to say why, no implementation language in the core's description), `name_audit.py`
(every name the package uses is attested *literally* in the corpus, and an editor's heading does not
count as attestation), and `token_count.py` (realised size against budget, under a declared
estimator). The hard minimum: *if the corpus contains any high-signal cost-bearing refusal, the
core must contain at least one.* Failing this blocks delivery — it is the most common way a core ends
up articulate but generic. The mechanical checks exist for the one defect class careful reading
cannot catch: the section that is simply not there, because there is nothing on the page to notice.

---

## Output

A directory named `<slug>-perspective` with a repository-local Agent Skill already installed:

```text
<slug>-perspective/
├── .agents/
│   └── skills/
│       └── <slug>-perspective/
│           ├── SKILL.md
│           └── references/
│               ├── clusters/
│               ├── frameworks.md
│               └── voice.md
└── fidelity-ledger/
    ├── provenance.md
    └── episodic.md
```

- **`.agents/skills/<slug>-perspective>/SKILL.md`** — the core embodiment artifact, front-loaded (compaction truncates from the end, so the highest-value fingerprints come first). Its size is **computed, not fixed**: a supply term over the diagnostic elements that survived curation — cost-bearing refusals, projectible regularities, interactional moves, modulation patterns; preoccupations and style contribute nothing — clamped between a **3,000-token floor** and a corpus-derived ceiling of 4,000 (thin or mostly-secondhand), 6,000 (mid), or 7,500 (large, multi-period). Typical cores land at 3,000–6,000. Procedures and standing verdicts are priced highest in the supply term, because they are the classes a host agent can actually *execute*; the 2.x ceilings predated both, so a corpus rich in them saturated a supply it had no room to spend. Every figure here is in `token_count.py` tokens, and the tokenizer is a required field in the log — a budget without its unit means two different sizes in two runs, since the same package measures roughly twice as large in Chinese as in English under a word-based count.

- **`.agents/skills/<slug>-perspective>/references/`** — modular, **host-agent-facing** files sized for on-demand loading; loaded at runtime, so this package never contains provenance, scores, fidelity results, or episodic material. Two are **standing, cross-corpus modules of equal status** — `frameworks.md`, what the person thinks with, and `voice.md`, how the person sounds. Both are **layered templates asked of every subject**: `frameworks.md` runs §0–§7 and `voice.md` runs §0–§11, and a section the corpus cannot fill is marked absent rather than dropped, because an absence a reader can see is information and a missing heading is not. The ordering inside `frameworks.md` is the substantive claim — **method** and **epistemology** come before **ontology** and **standing verdicts**, because a persona handed only conclusions can restate them and cannot extend them. `voice.md` opens with the register structure for the same reason: a host agent has to choose a family before writing a sentence, rather than discovering afterwards that it wrote in the average of two. The rest is per-source: one module per high-value source cluster. Sizes: cluster modules are **computed per cluster** by `scripts/cluster_budget.py` from the constructs, moves and evidence routed to each one, the number of sibling modules it must fence itself off from, and a damped corpus-mass term (floor 1,800, hard ceiling 6,000; typically 2,000–4,500). A cluster below the floor is folded into a sibling or demoted to `fidelity-ledger/episodic.md` rather than written thin, and a cluster that saturates the input caps is either re-cut at Stage 1 or split internally by register, never trimmed. `frameworks.md` and `voice.md` are **computed too** as of 3.0 — from the constructs, verdicts, moves and register families actually routed to them, clamped to 2,000–7,000 — rather than a flat ~4,000 that a rich corpus quietly outgrew.
- **`.agents/skills/<slug>-perspective>/references/voice.md`** — the measured expressive system, and the reason the core's 20% style cap is safe. A fingerprint-sized "How I sound" is enough to *frame* an answer in someone's voice; it is not enough to *write* one at length. So the rest of the system lives here: favored constructions with attested fragments, the **avoid-list** (the words and openings conspicuously missing from the corpus — as diagnostic as the favored ones, and previously homeless), modulation rules as trigger → shift pairs, register range across settings and periods, lexical fingerprint, the `style_metrics.py` baseline the fidelity test measures against, and anti-drift pairs for long generations. Built from firsthand clusters only. The host loads it before any sustained prose in the voice.
- **`fidelity-ledger/`** — **human-facing and outside `.agents/`**, so it is never loaded by the host agent: `provenance.md`, the audit trail mapping each core element to its source, the computed budgets (core and cluster), and the gate/final fidelity results; and `episodic.md`, concrete attested one-off material — specific incidents, anecdotes, decision-record fragments — that did not clear a cluster module's own floor (soft ~4,000). Uncapped otherwise, because an audit package's completeness matters more than its size.

Plus a short **coverage report** delivered in conversation: what the corpus covered well, where it was thin, the fidelity-test scores, and any domain where the persona should be trusted less.

Output quality is strictly bounded by corpus coverage, diversity, and signal density. A thin corpus yields a smaller, honestly-scoped core — never fabricated probes padding it out to hit a size target. That is also why the floor is a *trigger*, not a quota: falling under it sends you back to re-examine borderline cuts among the diagnostic classes, and failing that, to ship a reduced-scope core and say so in the coverage report.

---

## Repository layout

```
.
├── SKILL.md                        # the skill itself — pipeline, rules, judgment calls
├── references/
│   ├── acquisition.md              # before Stage 1: fetching remote corpora, attribution rules
│   ├── pipeline.md                 # Stage 1 mechanics, extraction routing, coverage map schema
│   ├── extraction.md               # Stage 2 — Pass A0, the eight classes, cost-bearing catalogue
│   ├── scoring.md                  # Stage 3 probes, the budget formulas, audit-log format
│   ├── output-template.md          # Stage 4 core template, frameworks/voice specs, layout
│   ├── fidelity-tests.md           # Stage 5 procedures, thresholds, re-test obligation
│   └── schemas/                    # JSON Schema for every intermediate artifact
│       ├── clusters-manifest.schema.json
│       ├── coverage-map.schema.json
│       ├── registers.schema.json
│       ├── extractions.schema.json
│       ├── scores.schema.json
│       ├── fidelity.schema.json
│       └── passages.schema.json
├── requirements-release.txt        # JSON Schema dependency for release validation
├── scripts/                        # local helpers; release checks require jsonschema
│   ├── corpus_clean.py             # Stage 1 — extraction-damage census and repair
│   ├── segment.py                  # Stage 1 — cut clusters, write a schema-valid manifest
│   ├── register_discover.py        # Stage 2 Pass A0 — how many voices does this corpus have?
│   ├── style_metrics.py            # Stage 2 — countable expression features
│   ├── zh_metrics.py               # Stage 2 — the same, for Chinese corpora
│   ├── kwic.py                     # Stage 2 — keyword-in-context evidence retrieval
│   ├── cluster_budget.py           # Stage 4 — per-module size, with an actionable verdict
│   ├── token_count.py              # Stage 3 / 5 — one tokenizer for every budget
│   ├── holdout_split.py            # Stage 1: grouped train/development/test split
│   ├── discrimination_test.py      # Stage 5 — blind register-separation gate
│   ├── validate_package.py         # Stage 5 — structural check of the produced package
│   └── name_audit.py               # Stage 5 — named-construct consistency across the package
├── .gitignore
├── CHANGELOG.md
├── LICENSE
├── MIGRATION.md
├── NOTICE.md
└── README.md
```

This is the metatool's own layout, not a generated persona's. A generated persona is an outer
project containing its runnable package at `.agents/skills/<slug>-perspective/` and its human-facing
`fidelity-ledger/` beside `.agents/`; see "Output" above for the full generated layout.

### Host requirements

The skill is written to run under **any** agent host, not a particular one. It needs a filesystem it
can write to and Python 3.9+ for the scripts. Release checks require the dependency declared
in `requirements-release.txt`; structural draft checks remain available without it.

Three locations are host-dependent and resolved once at the start of a run: where the corpus is read
from, where the work directory is created (default `persona_work/`), and where the finished persona
is delivered. Anything else the pipeline suggests — a PDF reader, a DOCX converter, a companion
document skill — is a preference with a named stdlib fallback, so a missing tool degrades quality
rather than failing the run.

### Scripts

All run standalone. Install `requirements-release.txt` before release validation or the full
test suite. Roughly in pipeline order.

```bash
# Stage 1 — census extraction damage. Report only; nothing is written without --fix.
# Catches lost fi/fl/ff ligatures ("rst" for "first"), words wrapped across lines by
# justified typesetting ("transporta- tion"), and EPUB/markup residue. All three leave
# fluent, readable text that measures wrong, so none of them is visible by eye.
python scripts/corpus_clean.py raw/
python scripts/corpus_clean.py raw/ --fix --out clean/

# Stage 1 — cut clusters from a spec and write clusters/manifest.json.
# Boundaries may be line numbers or regexes; prefer regexes, which survive re-extraction.
python scripts/segment.py spec.json --out persona_work/ --dry-run

# Stage 2, Pass A0 — how many voices does this corpus actually contain?
# Run this BEFORE any style measurement. A pooled baseline over two registers is
# an average of two people that reads like an ordinary set of numbers.
python scripts/register_discover.py clusters/ --json registers.json

# Measure expression features across a corpus (or a single file).
# In a multi-register corpus, run it per family first and pool second.
python scripts/style_metrics.py path/to/corpus/

# For a Chinese corpus — same feature classes, measured in 汉字.
# --terms tracks the subject's own vocabulary; the script ships with no term list.
python scripts/zh_metrics.py path/to/corpus/ --per-file --terms 秩序,封建,德性

# Produce a reproducible seeded split for the held-out projection test.
# Before extraction: passage objects need id, group (work/episode), and optional domain.
python scripts/holdout_split.py passages.json --seed 42 --frac 0.12 --out split.json

# With consistent group domains, stratify; thin strata are reported as uncovered.
python scripts/holdout_split.py passages.json --stratify --seed 42 --frac 0.12 --out split.json

# Set a separate development fraction
python scripts/holdout_split.py passages.json --seed 42 --dev-frac .15 --out split.json

# Stage 2 — pull evidence passages. grep returns whole paragraphs on this kind of text
# and misses matches straddling a line break; this returns fixed-width windows.
# --count reports hits per cluster: the >=2-independent-clusters corroboration check.
python scripts/kwic.py clusters/ "levell?ing|the public is" --before 300 --after 900
python scripts/kwic.py clusters/ "single individual" --count

# Stage 5 — blind register-separation gate, for personas that claim internal variation.
# Two steps, because the answers must be written before the key is seen.
python scripts/discrimination_test.py sample clusters/ --registers registers.json --seed 42 --mask-names --key key.json
python scripts/discrimination_test.py score key.json --answers R1 R2 R1 R2

# Stage 4 — size one module, or a whole package from a spec file.
# --shared-domain is what separates "re-cut this cluster" from "split it internally".
python scripts/cluster_budget.py --example > budget_spec.json
python scripts/cluster_budget.py budget_spec.json --json cluster_budgets.json
python scripts/cluster_budget.py --emit-coefficients   # the active calibration constants

# Stage 3 / 5 — count tokens under one declared estimator, so every budget in the
# run shares a unit. Record the realised size against the budget: that comparison is
# the only calibration data the coefficients ever get.
python scripts/token_count.py my-perspective/ --per-file --json tokens.json

# Stage 5 — structural check of the produced package. Catches what reading cannot:
# ledger material inside references/, a dead cluster load-list, a missing section.
python scripts/validate_package.py my-perspective/ --json validation.json
python scripts/validate_package.py my-perspective/ --headings core_headings.txt --strict

# Stage 5 — back-check every name the package uses against literal corpus hits,
# separating heading-like appearances from ordinary prose.
python scripts/name_audit.py --package my-perspective/ --corpus clean/ --json audit.json
```

`style_metrics.py` reports sentence-length distribution, hedge and booster rates, punctuation rhythm, lexical diversity, person-reference ratios, and top content terms and bigrams.

`corpus_clean.py` detects ligature loss in two stages, and the distinction matters: an anomalously
low `f` rate is only a **screen** (it false-positives on short files), while suspect-token density
is the **verdict** — damaged corpora run 50–100× a clean one on that measure, so the two rarely
disagree by accident. Repairs are conservative by default: tokens that are also real English words
are reported but left alone unless you pass `--aggressive`, and a hyphen is only closed up when
whitespace follows it, so `self-love` survives while `transporta- tion` is joined.

`kwic.py` takes a **Python** regex, not a shell one. Alternation is `a|b`; writing `a\|b` matches a
literal pipe and returns nothing, which looks exactly like a corpus that lacks the passage. The
script warns, but the general rule is worth holding: an empty result on a term you are confident
about is a tooling failure until proven otherwise.

`discrimination_test.py` answers a question the other three fidelity checks structurally cannot.
They ask whether generated prose reads like the person; this asks whether the person's *registers
can be told apart* — and a passage can match the aggregate baseline perfectly while being
indistinguishable from every other register the core promises. Below 0.70, collapse the families
into one honest voice rather than shipping a distinction the persona cannot perform. As of 3.0 it is
**mandatory whenever the corpus has more than one register family**, and re-triggered by any cluster
merge — a merge being precisely the operation that can pool two registers into one module without
anyone deciding to.

`register_discover.py` is the pass that makes that gate meaningful, and the division of labour between
the two is deliberate: **discovery proposes, discrimination disposes.** When they disagree, reduce the
number of families rather than re-running discovery at a looser threshold until the numbers come out
as hoped. The script measures only — naming the families, nominating a default, ordering any
within-family gradient, and flagging boundaries that cut across clusters are readings, not
measurements, and `registers.json` is unfinished until they are filled in by hand.

`validate_package.py` and `name_audit.py` exist for the two defect classes that survive careful
reading.

The first is structural, and it is invisible because there is nothing on the page to notice: ledger
material sitting inside a runtime reference, a load-list in the core pointing at a cluster module that
was never written, an `episodic.md` that is empty without saying why, implementation language leaking
into the core's own description. `validate_package.py` checks that mechanical subset and leaves the
judgment calls as warnings rather than pretending they are solved. Its `--headings` flag is deliberately
unopinionated: a core may be written in the subject's own language, so the checker will not impose
English headings unless you hand it the anchors to require.

The second is a naming failure with a specific mechanism. A neat diagnostic label can be invented
during distillation, or inherited from an editor's chapter heading, and then quietly acquire the
authority of the person's own coinage — at which point the persona is confidently using a term its
subject never used. `name_audit.py` looks for each package name **literally in the corpus**, separates
heading-like appearances from ordinary prose (an editor's heading is not attestation), and makes thin
support impossible to overlook. Without `--names` it harvests candidates from the package's own bold
runs, quoted runs, title marks and headings, so it audits what you actually wrote rather than what you
remember writing.

`zh_metrics.py` reports the same classes for Chinese text — sentence length in 汉字, Chinese hedge and booster rates, punctuation rhythm (including 《》 and the interpunct that marks transliterated names), person-reference ratios, a character-n-gram fingerprint, and a discourse-scaffolding absence check that feeds the avoid-list in `voice.md`. `style_metrics.py` tokenises on `[A-Za-z]`, so on a CJK corpus it returns zeros for every feature that matters; reach for this one instead.

### Artifact schemas

The pipeline writes six intermediate JSON artifacts to its work directory (default `persona_work/`) — `clusters/manifest.json`, `coverage_map.json`, `registers.json`, `extractions.json`, `scores.json`, `fidelity.json` — plus the `passages.json` that `holdout_split.py` reads. These are **runtime outputs for a specific corpus, not files this repository ships**. There is no universal `extractions.json`; it is the extraction of one particular person's material. They are kept for the whole run rather than cleaned up between stages, because the gates can send curation backwards and because the audit log and coverage report are built from them. `.gitignore` keeps them out of version control.

What the repository does ship is their shape: [`references/schemas/`](references/schemas/) holds a JSON Schema (draft 2020-12) for each, with worked examples. The snippets embedded in the prose references are illustrative and some carry `//` comments, so they will not parse if copied verbatim — the schemas are the authoritative, validatable version. A few of the skill's hard rules are encoded structurally there too (the ≥2-cluster corroboration rule, the required `convenient_move` on cost-refusal elements, the class-prefix/`type` agreement on element ids, the `order`/`precondition`/`on_fail` triple on procedures, 0–1 score bounds). Two of the scripts write shapes that validate as-is — `register_discover.py` against `registers.schema.json`, `cluster_budget.py` against the `cluster_budgets` item shape — so a validation failure there means the script and the schema have diverged and the pair needs fixing. See [`references/schemas/README.md`](references/schemas/README.md) for the index and what is deliberately left unencoded.

---

## Scope and intended use

This skill operates only on public material the user has the right to use, and produces a **perspective / thinking-style tool** — for analysis, study, and ideation in the person's documented frame.

It is **not** for deceptive impersonation, forged attribution, or passing off invented statements as a person's real words. The skill is written to say so and to reshape such requests toward legitimate perspective work.

Distilling a living person's voice carries obvious dual-use weight. Use the coverage report. Label outputs as perspective work. Don't put words in anyone's mouth.

---

## Contributing

Issues and pull requests welcome. The parts that carry the real value are Stage 3 (scoring, elevation, deletion) and the fidelity tests — improvements there are worth more than broader extraction coverage.

One convention worth knowing before writing docs here. The specification files use **fictional or
schematic examples only** — never a real distilled package, and never a real subject's material as an
illustration. A concrete example teaches the example: a reader shown how one particular corpus was
handled starts matching their own corpus against that shape instead of against the rule, and the
specification quietly narrows to the case it was demonstrated on. The rules have to stand on their own
logic, universally, for any subject; if a rule can only be explained by pointing at a package that
already exists, it is not yet a rule.

Upgrading from 2.x? See [MIGRATION.md](MIGRATION.md) — 3.0 changes artifact shapes and adds required
fields, so existing logs need a pass.

---

MIT © 2026 Ariel Lee. [See LICENSE](LICENSE).

This license covers the original text in this repository. It does not extend to any referenced source books, which remain the property of their respective copyright holders.

## Independent evaluation and release validation

Split the source inventory by underlying work or episode before extracting traits. Construction
uses train; development guides revisions; a separate final set is used once in fresh contexts.
Pair predictions with a minimal persona baseline on the same model/settings and save both answers.
Discrimination consumes `registers.json` and scores register families. A separate audience/task/stakes
test checks whether the generated persona selects and produces the appropriate register.

`holdout_split.py` now requires passage objects with `id` and `group`; old ID-only inputs must be
migrated. Hashes and complete release artifacts are documented in
[release-evidence.md](references/release-evidence.md). Structural validation alone remains useful
for drafts; verified release requires:

```bash
python3 scripts/validate_package.py /path/to/persona --release --fidelity /path/to/fidelity-ledger/fidelity.json
python3 -m unittest discover -s tests -v
```

Existing evaluations need to be rerun under this protocol. The validator verifies recorded
artifacts and freshness, not the truth of a grader's judgments or a claim of context isolation.
