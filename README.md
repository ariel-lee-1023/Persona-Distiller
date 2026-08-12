# persona-distiller

**Turn one person's public record into a persona another agent can *embody*.**

`persona-distiller` is an [Agent Skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) that takes a corpus of one person's material — books, essays, transcripts, interviews, decision records — and distills it into a compact, embodiment-ready perspective skill: a lean core `SKILL.md` plus a modular `references/` package.

Not a biography. Not a summary. Not a quote database. The output is optimized so that a reader familiar with the person's record cannot easily tell its output apart from the real thing, on public topics the corpus actually covers.

---

## What makes it different

Most voice-cloning prompts reach for what is easy to count — sentence length, favourite punctuation, hedge-word frequency. Those features are cheap to measure and almost everyone's are somewhat generic. This skill deliberately spends its budget elsewhere:

| Signal | Why it individuates |
|---|---|
| **Cost-bearing refusals** | Positions the person held *against* their own incentive |
| **Patterns of variation** | How their register shifts under pressure, audience, or stakes |
| **Interactional moves** | How they concede, reframe, dig in, or shift footing in exchange |
| **Projectible regularities** | Thought-moves that actually predict stance on held-out material |

Two design commitments follow from that:

1. **Recognition is a family resemblance.** Identity shows up redundantly, at different grains, through overlapping probes. The skill does *not* partition a person into tidy mutually-exclusive buckets, and does *not* dedupe a trait away just because it surfaced in three passes. Redundant corroboration across probes is strength.

2. **Delete without mercy.** A tight ~4k-token core that nails the fingerprints beats a comprehensive 15k-token one that reads like everyone. Anything scoring below threshold, reading as generic, or conflicting with a higher-scoring voice feature gets cut — not softened, not averaged in.

Spending the budget elsewhere is not the same as throwing style away. Measured expression that survives the deletion rule but loses the competition for core space is *relocated*, not discarded: it goes to `references/voice.md`, a standing module the host loads before writing sustained prose in the voice. The core stays a fingerprint; the voice stays complete.

### The honesty split

The generated persona contains **no uncertainty disclaimers, no provenance hedging, no meta framing**. Those move a reader out of the voice and destroy identification.

Honesty does not disappear — it **relocates**. Coverage gaps, source citations, confidence levels, and limitations live in the **Fidelity Ledger** — a human-facing audit package, separate from the `references/` package the host agent loads — and in a coverage report handed to the user, never inside the embodiment artifact and never inside `references/`. You keep full auditability; the persona keeps its voice. This split is the whole trick.

---

## Installation

### Claude Code

```bash
git clone https://github.com/ariel-lee-1023/persona-distiller.git ~/.claude/skills/persona-distiller
```

Or, to install for a single project instead of globally:

```bash
git clone https://github.com/ariel-lee-1023/persona-distiller.git .claude/skills/persona-distiller
```

Restart Claude Code (or start a new session) and the skill will be discoverable.

### Claude.ai / Claude Desktop

Zip the repository contents so that `SKILL.md` sits at the root of the archive, then upload it under **Settings → Capabilities → Skills**.

```bash
cd persona-distiller && zip -r persona-distiller.zip SKILL.md references scripts
```

### Requirements

Python 3.8+ for the two helper scripts. **No third-party dependencies** — both are standard library only.

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

**Stage 2 — Multi-granularity extraction.** Three passes: fine-grained expression (measured by `style_metrics.py`, not guessed), coarse-grained projectible regularities, and the interactional / cost-bearing pass. Every point where the *convenient* response diverges from the person's *attested* response gets flagged. Those flags are gold.

**Stage 3 — Multi-probe curation & deletion.** Every element scored 0–1 on a weighted composite:

| Probe | Weight |
|---|---|
| Projectibility | **0.30** |
| Cost / refusal signal | **0.25** |
| Expressive match | 0.20 |
| Interactional visibility | 0.15 |
| Preoccupation / gravitational weight | 0.10 |

Hard deletion rule below 0.55 composite. Hard elevation rule ranks survivors by *class priority first* — because style metrics are abundant and cost-refusals are sparse, raw ranking would let volume crowd the fingerprints out. Pure style averages may fill at most ~20% of the core.

**Gate before Stage 4.** Assembly is downstream of passing two gates: a **projection gate** (held-out prediction) and a **cost gate** (every high-signal divergence accounted for). Gate results are *control signals*, not reports — failing one sends you back to re-curate, never forward to the template.

**Stage 4 — Assemble.** Core `SKILL.md` plus the `references/` package, following a fixed template, obeying the no-meta rule absolutely. Module sizes are computed here too, by `scripts/cluster_budget.py`, and the reasoning is worth stating because a flat band is the obvious thing to write and the wrong thing to write. What a cluster module has to deliver is a working part of someone's thinking, so its terms are the things that constitute one — the apparatus the cluster uses, the moves it makes, the applications it commits to, the fragments kept as evidence — and each is capped, because the fifth instance of a move documents what the first three already established and the twelfth only confirms that the person had a habit. One term is not about the cluster in isolation at all: the more sibling modules a package carries, the more each one must spend marking off what it is *not*, so the fencing cost rises with sibling count and the package gets more expensive per module precisely as it gets better. Corpus mass enters last, under a square root, deliberately damped, because it is the strongest available proxy for the wrong quantity — across the calibration set module length correlated +0.82 with retained fragments and +0.70 with the cluster's own constructs, but only +0.30 with word count, so a rule leaning on mass would size a module by how much the person published rather than by how much of them is in it. The coefficients were not picked in advance either; they were recovered by fitting modules already written by hand and already judged faithful, which is the only calibration target available when the quantity you are trying to predict is "enough to carry the person". Floor and ceiling are then applied to that estimate rather than built into it, because how much material a cluster holds and how much a host will load are unrelated facts, and folding them into one expression lets each hide the other. Keeping them apart is what makes both limits informative: a supply under the floor is not a small module but a failed one — fold the cluster into a sibling, or demote it to `episodic.md` — and a cluster that saturates the input caps is carrying two registers and goes back to `segment.py`, since buying the space back by deleting evidence would fix the number and lose the person. Calibration: ten modules against one 630k-word corpus, mean error 3.8%, max 6.0% — structure settled, coefficients provisional.

**Stage 5 — Final fidelity verification.** Projection re-check, cost/presence assertion, and style-match test. The hard minimum: *if the corpus contains any high-signal cost-bearing refusal, the core must contain at least one.* Failing this blocks delivery — it is the most common way a core ends up articulate but generic.

---

## Output

A directory named `<slug>-perspective` containing:

- **`SKILL.md`** — the core embodiment artifact, front-loaded (compaction truncates from the end, so the highest-value fingerprints come first). Its size is **computed, not fixed**: a supply term over the diagnostic elements that survived curation — cost-bearing refusals, projectible regularities, interactional moves, modulation patterns; preoccupations and style contribute nothing — clamped between a **3,000-token floor** and a corpus-derived ceiling of 4,000 (thin or mostly-secondhand), 5,500 (mid), or 6,500 (large, multi-period). Typical cores land at 3,000–5,500.
- **`references/`** — modular, **host-agent-facing** files sized for on-demand loading; loaded at runtime, so this package never contains provenance, scores, or fidelity results. Two are **standing, cross-corpus modules of equal status** — `frameworks.md`, what the person thinks with, and `voice.md`, how the person sounds. The rest are per-source or residual: one module per high-value source cluster, and `episodic.md` for concrete, attested one-off material — specific incidents, anecdotes, decision-record fragments — that did not clear a cluster module's own floor. Sizes: cluster modules are **computed per cluster** by `scripts/cluster_budget.py` from the constructs, moves and evidence routed to each one, the number of sibling modules it must fence itself off from, and a damped corpus-mass term (floor 1,800, hard ceiling 6,000; typically 2,000–4,500). A cluster below the floor is folded into a sibling or demoted to `episodic.md` rather than written thin, and a cluster that saturates the input caps is re-cut at Stage 1 rather than trimmed. `frameworks.md` / `voice.md` / `episodic.md` soft ~4,000.
- **`references/voice.md`** — the measured expressive system, and the reason the core's 20% style cap is safe. A fingerprint-sized "How I sound" is enough to *frame* an answer in someone's voice; it is not enough to *write* one at length. So the rest of the system lives here: favored constructions with attested fragments, the **avoid-list** (the words and openings conspicuously missing from the corpus — as diagnostic as the favored ones, and previously homeless), modulation rules as trigger → shift pairs, register range across settings and periods, lexical fingerprint, the `style_metrics.py` baseline the fidelity test measures against, and anti-drift pairs for long generations. Built from firsthand clusters only. The host loads it before any sustained prose in the voice.
- **`fidelity-ledger/`** — **human-facing**, and never loaded by the host agent: `provenance.md`, the audit trail mapping each core element to its source, the computed budgets (core and cluster), and the gate/final fidelity results. Uncapped, because an audit package's completeness matters more than its size. It sits outside `references/` on purpose, so it is structurally impossible for the host agent to pull it into the embodiment context.

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
│   ├── extraction.md               # Stage 2 taxonomy and cost-bearing catalogue
│   ├── scoring.md                  # Stage 3 probes, worked examples, audit-log format
│   ├── output-template.md          # Stage 4 core template, voice.md spec, package layout
│   ├── fidelity-tests.md           # Stage 5 procedures, thresholds, reporting
│   └── schemas/                    # JSON Schema for every intermediate artifact
│       ├── clusters-manifest.schema.json
│       ├── coverage-map.schema.json
│       ├── extractions.schema.json
│       ├── scores.schema.json
│       ├── fidelity.schema.json
│       └── passages.schema.json
├── scripts/                        # all stdlib-only, no install step
│   ├── corpus_clean.py             # Stage 1 — extraction-damage census and repair
│   ├── segment.py                  # Stage 1 — cut clusters, write a schema-valid manifest
│   ├── style_metrics.py            # Stage 2 — countable expression features
│   ├── zh_metrics.py               # Stage 2 — the same, for Chinese corpora
│   ├── kwic.py                     # Stage 2 — keyword-in-context evidence retrieval
│   ├── holdout_split.py            # Stage 5 — reproducible seeded keep/masked split
│   └── discrimination_test.py      # Stage 5 — blind register-separation gate (conditional)
├── .gitignore
├── CHANGELOG.md
├── LICENSE
├── NOTICE.md
└── README.md
```

This is the skill's own layout, not a generated persona's. A *generated* `<slug>-perspective/`
directory additionally ships `references/episodic.md` (host-agent-facing, concrete attested
one-off material) and a sibling `fidelity-ledger/provenance.md` (human-facing audit trail, kept
outside `references/` on purpose) — see "Output" above for the full generated layout.

### Host requirements

The skill is written to run under **any** agent host, not a particular one. It needs a filesystem it
can write to and Python 3 for the scripts; all three are standard-library-only, with no install step.

Three locations are host-dependent and resolved once at the start of a run: where the corpus is read
from, where the work directory is created (default `persona_work/`), and where the finished persona
is delivered. Anything else the pipeline suggests — a PDF reader, a DOCX converter, a companion
document skill — is a preference with a named stdlib fallback, so a missing tool degrades quality
rather than failing the run.

### Scripts

All run standalone, no install required. Roughly in pipeline order.

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

# Measure expression features across a corpus (or a single file)
python scripts/style_metrics.py path/to/corpus/

# For a Chinese corpus — same feature classes, measured in 汉字.
# --terms tracks the subject's own vocabulary; the script ships with no term list.
python scripts/zh_metrics.py path/to/corpus/ --per-file --terms 秩序,封建,德性

# Produce a reproducible seeded split for the held-out projection test.
# Takes a JSON list of passage IDs — {"passages": ["p001", ...]} or a bare array — not a corpus path.
python scripts/holdout_split.py passages.json --seed 42 --frac 0.12 --out split.json

# …or pass the IDs inline
python scripts/holdout_split.py --ids p001 p002 p003 p004 --seed 42

# Stage 2 — pull evidence passages. grep returns whole paragraphs on this kind of text
# and misses matches straddling a line break; this returns fixed-width windows.
# --count reports hits per cluster: the >=2-independent-clusters corroboration check.
python scripts/kwic.py clusters/ "levell?ing|the public is" --before 300 --after 900
python scripts/kwic.py clusters/ "single individual" --count

# Stage 5 — blind register-separation gate, for personas that claim internal variation.
# Two steps, because the answers must be written before the key is seen.
python scripts/discrimination_test.py sample clusters/ --seed 42 --mask-names --key key.json
python scripts/discrimination_test.py score key.json --answers c09 c05 c02 c06
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
indistinguishable from every other register the core promises. Below 0.70, collapse the registers
into one honest voice rather than shipping a distinction the persona cannot perform.

`zh_metrics.py` reports the same classes for Chinese text — sentence length in 汉字, Chinese hedge and booster rates, punctuation rhythm (including 《》 and the interpunct that marks transliterated names), person-reference ratios, a character-n-gram fingerprint, and a discourse-scaffolding absence check that feeds the avoid-list in `voice.md`. `style_metrics.py` tokenises on `[A-Za-z]`, so on a CJK corpus it returns zeros for every feature that matters; reach for this one instead.

### Artifact schemas

The pipeline writes five intermediate JSON artifacts to its work directory (default `persona_work/`) — `clusters/manifest.json`, `coverage_map.json`, `extractions.json`, `scores.json`, `fidelity.json` — plus the `passages.json` that `holdout_split.py` reads. These are **runtime outputs for a specific corpus, not files this repository ships**. There is no universal `extractions.json`; it is the extraction of one particular person's material. They are kept for the whole run rather than cleaned up between stages, because the gates can send curation backwards and because the audit log and coverage report are built from them. `.gitignore` keeps them out of version control.

What the repository does ship is their shape: [`references/schemas/`](references/schemas/) holds a JSON Schema (draft 2020-12) for each, with worked examples. The snippets embedded in the prose references are illustrative and some carry `//` comments, so they will not parse if copied verbatim — the schemas are the authoritative, validatable version. A few of the skill's hard rules are encoded structurally there too (the ≥2-cluster corroboration rule, the required `convenient_move` on cost-refusal elements, 0–1 score bounds). See [`references/schemas/README.md`](references/schemas/README.md) for the index and what is deliberately left unencoded.

---

## Scope and intended use

This skill operates only on public material the user has the right to use, and produces a **perspective / thinking-style tool** — for analysis, study, and ideation in the person's documented frame.

It is **not** for deceptive impersonation, forged attribution, or passing off invented statements as a person's real words. The skill is written to say so and to reshape such requests toward legitimate perspective work.

Distilling a living person's voice carries obvious dual-use weight. Use the coverage report. Label outputs as perspective work. Don't put words in anyone's mouth.

---

## Contributing

Issues and pull requests welcome. The parts that carry the real value are Stage 3 (scoring, elevation, deletion) and the fidelity tests — improvements there are worth more than broader extraction coverage.

---

MIT © 2026 Ariel Lee. [See LICENSE](LICENSE).

This license covers the original text in this repository. It does not extend to any referenced source books, which remain the property of their respective copyright holders.
