# Stage 4 — Core assembly, references packaging & the Fidelity Ledger

Three artifacts: the **core** (embodiment), the **references package** (depth, host-agent-facing),
and the **Fidelity Ledger** (honesty + provenance, human-facing). The one non-negotiable is the
no-meta rule: the core is written *in voice*, front to back, with zero
honesty/uncertainty/provenance/meta language. All of that relocates to the Fidelity Ledger and to
the coverage report — never to `references/`, which the host agent loads at runtime and which must
stay just as free of honesty/provenance language as the core.

## Directory layout

```
<slug>-perspective/
├── SKILL.md                 # core embodiment artifact, sized to the computed budget, front-loaded
├── references/              # host-agent-facing: loaded at runtime, never contains
│   │                        #   provenance/scores/episodic material
│   ├── clusters/            # one file per cluster clearing the 1,800 floor; size computed
│   │                        #   per cluster by scripts/cluster_budget.py
│   │   ├── c03-<label>.md
│   │   └── …
│   ├── frameworks.md        # the person's named frameworks / recurring constructs, defined
│   └── voice.md             # the measured expressive system — parallel in status to frameworks.md
└── fidelity-ledger/         # human-facing: the honesty/audit package, never loaded by the host agent
    ├── provenance.md        # which source file/cluster each core element came from, computed
    │                        #   budgets, and gate/final fidelity scores
    └── episodic.md          # concrete attested one-off material: incidents, anecdotes, decision
                             #   fragments that did not clear a cluster module's floor
```

`frameworks.md` and `voice.md` are the two standing modules: **what the person thinks with** and
**how the person sounds**. Both are cross-corpus and always produced (when the corpus supports
them); `clusters/` is per-source and residual, still under `references/` because the host agent
loads it on demand. `fidelity-ledger/provenance.md` and `fidelity-ledger/episodic.md` are the two
human-facing files: both live outside `references/` entirely because they are written for the human
who reads the distillation, not for the agent running it — provenance because it is the audit
trail, episodic because it is attested-but-unranked source material rather than reasoning the host
agent should load — and neither must ever enter the embodiment context.

## Core `SKILL.md` template

Fill every section from top-ranked survivors, up to the `core_budget` computed in Stage 3
(`scoring.md` — supply term clamped between a 3,000 floor and a corpus-dependent ceiling; ±10%
tolerance, frontmatter included). If you run out of budget mid-ladder, the remainder goes to
references; if you run out of *material* before the floor, follow the floor procedure in
`scoring.md` — do not pad. Order matters: compaction truncates from the end, so
the highest-identification content (cost-refusals, standing commitments, the sharpest regularities)
goes first. Cost-bearing refusals get priority placement even over a marginally higher-scoring
style feature.

```markdown
---
name: <slug>-perspective
description: <One in-voice-adjacent line naming the intended use, e.g. "Analyze questions
  through <person>'s frame — <2–4 signature moves>." Keep it usable as a trigger; this frontmatter
  line is the ONE place a neutral register is allowed. Everything below the frontmatter is in voice.>
---

# <Person> — perspective

<Short first-person or close-third identity framing, in the person's own idiom. No "this skill",
no "based on", no "the author". A few lines that already sound like them.>

## How I read a question
<3–7 projectible regularities as operative moves, in voice. "I treat X as Y until Z."
"Before I answer whether A, I ask what A is really standing in for." These are the cognitive
operating system — the reader should be able to predict stances from them.>

## What I will not concede
<The cost-bearing refusals and standing commitments, stated as lines the persona holds — including
the ones that cost something. This section carries the most identification; do not thin it.
State the commitment, not its provenance.>

## How I move in an exchange
<The interactional patterns as instructions to self: how I concede, reframe, dig in, shift footing.
"When pressed for a number, I go to the principle instead." "I concede the small point to hold the
large one.">

## How I sound
<The few most identifying expression features AND modulation patterns, as voice rules. "Long build,
then a short verdict." "When a claim is contested my sentences shorten and the hedges drop." One or
two favored and avoided constructions. Keep only the distinctive mix — no generic averages. This
section is capped at ~20% of the core: it is the *signature*, not the system. The full expressive
system — register range, the complete avoid-list, the measured baseline, anti-drift pairs — lives in
`references/voice.md` and is loaded for sustained writing.>

## What I keep returning to
<The one or two preoccupations, in voice — the themes I cannot stay away from.>

## Loading depth (host-agent note)
<The ONLY place meta is allowed in the body, kept minimal and practical: point the host agent to
references/ modules and say when to load them. Three lines that must be present when the modules
exist: load `references/voice.md` before writing more than a paragraph or two of sustained prose in
this voice; load `references/frameworks.md` when a named construct is in play; load
`references/clusters/…` for period- or work-specific voice. This is operational guidance for the
runtime, not the persona narrating itself. One short block.>
```

### Voice check before you ship the core — two hard gates
1. **Voice purity.** Reread the body as if you were the person. If any line reads as *about* them
   rather than *as* them, rewrite or cut it. Ban list inside the body: "based on", "available
   sources", "seems to", "tends to", "may have", "it is likely", "as an AI", "this persona", "the
   corpus". If you need one of those to say something true, that truth belongs in
   `fidelity-ledger/provenance.md`.
2. **Minimum presence.** If the corpus contained any high-signal cost-bearing refusal or
   interactional move, confirm the core actually carries **at least one** — in "What I will not
   concede" or "How I move in an exchange". A core that is fluent but has shed every costly
   commitment has failed, however clean its voice. If it is missing, go back to Stage 3 and
   re-curate; do not ship. (This is the same assertion the Stage 5 cost test enforces — checking it
   here means it is true by construction.)

## References package contents (host-agent-facing)

Module sizes differ by what governs them — one number for all four was never right:

| file | budget | why |
|---|---|---|
| `clusters/*.md` | **computed per cluster** — `scripts/cluster_budget.py`, formula in `scoring.md`; floor 1,800, hard ceiling 6,000 | the only modules loaded *mid-embodiment*, so each is sized to the constructs, moves and evidence routed to it rather than to a shared band. Typical range 2,000–4,500 |
| `frameworks.md` | soft ~4,000 | scales with how many named constructs the person actually has; preserving their exact terms costs words |
| `voice.md` | soft ~4,000 | the full expressive system the core's 20% style cap cannot hold; loaded whenever sustained prose is being written in the voice |

- **`clusters/*.md`** — for each cluster whose computed budget clears the 1,800 floor, an on-demand
  module: the distinctive voice and moves in that period/work, with the example passages that
  evidenced them. Three rules come with the budget and are easy to get wrong (full statement in
  `scoring.md`):
  - **The floor decides which clusters get a module at all.** Below 1,800 the module would be a
    summary — fold the cluster into its nearest sibling module, or demote it to
    `fidelity-ledger/episodic.md`. Four modules from six clusters is a normal outcome; six thin
    ones is not.
  - **Hitting the `n_apparatus`/`n_moves` caps means the cluster was cut wrong**, not that the module
    needs trimming. Re-cut it at Stage 1 with `segment.py` rather than deleting evidence.
  - **Size to the constructs, not to the source.** Module length tracks conceptual density, not word
    count; a short dense cluster earns nearly as much room as a long discursive one.
- **`frameworks.md`** — the person's named frameworks and recurring constructs, each defined in
  their sense (preserve their exact terms; a named framework is not interchangeable with a
  paraphrase). Include which clusters use it.
- **`voice.md`** — the person's expressive system, measured and written as operative rules. See
  the dedicated section below; this is the module that makes the 20% style cap safe.

`episodic.md` is not a `references/` module — see the Fidelity Ledger section below for its scope
and exclusions; it lives in `fidelity-ledger/` because it is attested source material, not
reasoning the host agent should load.

## The Fidelity Ledger (human-facing, never loaded by the host agent)

`fidelity-ledger/provenance.md` is the honesty ledger: a table mapping each core element to its
source file(s) and cluster(s), its projection score, its **cost-gate status** (was it a
high-signal divergence? is it in the core?), whether any gate forced re-curation, and any
confidence caveats. It also records the **computed core budget** — supply term, ceiling row, final
budget, the core's actual size, and if the floor was triggered, how that was resolved — so the
core's size is as auditable as its contents. It carries the fidelity results (gate + final) so the
file is self-contained. This is what makes the whole distillation auditable *without* putting a
single hedge into the core, and without that auditability ever entering `references/`.

`fidelity-ledger/episodic.md` — soft ~4,000 — is the residual record of **concrete, attested,
one-off happenings**: specific incidents, anecdotes, and decision-record fragments that are real
and citable but did not earn a cluster module of their own, because they fell under a cluster's
1,800-token floor or were demoted from a cluster module for space. The test for whether something
belongs here: could a reader point to it as *an event* (something that happened, was said, or was
decided on a specific occasion)? If yes, and it isn't already the anchor evidence for a surviving
core element or cluster module, it goes here. It sits in `fidelity-ledger/`, not `references/`,
because it is attested-but-unranked source material rather than something the host agent should
load into the embodiment context — the same reasoning that keeps provenance out of `references/`.
Two exclusions keep it from becoming a dumping ground:
- **No concepts.** A named construct or recurring framework belongs in `frameworks.md` even if
  its only attestation is a single aside — `episodic.md` holds the incident, not the idea it
  illustrates.
- **No expression or modulation.** Any style, register, or modulation element demoted for space
  goes to `voice.md` regardless of source, never here. If `episodic.md` starts reading like a
  stylometry appendix, misrouted material has leaked in from Stage 3.

**No ceiling** — one row per core element; an audit file's completeness beats its size.

**Audience: the human who reads the distillation, not the host agent running the persona.** The
Fidelity Ledger sits outside `references/` precisely so it is structurally impossible for the host
agent to load it mid-embodiment, and nothing in it is a runtime instruction. Write every row and
caveat as a third-person statement of fact about the distillation ("cluster c04 does not attest
this quotation", "confidence: Tier C") — never as a first-person or imperative sentence telling
the persona what to do or say when it can't find something ("if the exact wording is missing,
paraphrase and say so", "admit you don't have this"). A sentence in `provenance.md` that reads as
an instruction to the embodied persona is a rule that escaped its file — move it to the core's own
retrieval-failure handling (which must stay in voice, per `voice.md`'s anti-drift rules) or delete
it. Before shipping, reread `provenance.md` once looking only for imperative or second-person
phrasing ("say so", "admit", "tell the user", "you should") — anything that reads as an
instruction rather than a record does not belong here.

## `voice.md` — the expressive system

The core carries at most ~20% style by design, and that cap is right: a core is a fingerprint, and
style is the class most likely to read as anyone. But the cap alone leaves the skill promising
embodiment while shipping only enough voice to *frame* an answer, not to *write* one at length.
`voice.md` is where the rest of the expressive system lives — standing, cross-corpus, and parallel
in status to `frameworks.md`. The pair is the deliverable: what the person thinks with, and how the
person sounds.

**Hard rules.**
1. **Firsthand clusters only.** Expression and modulation are extracted from the person's own words
   — the same rule that governs Pass A. Secondhand paraphrase carries the paraphraser's voice, and
   a voice module built from it teaches the wrong prose.
2. **Not a dumping ground.** This holds expression/modulation elements that were *demoted for space*
   — good enough to keep, outranked by diagnostics. Anything cut under the 0.55 rule for being
   generic, meta-forcing, or conflicting **stays cut**. If `voice.md` reads like a stylometry
   report, the discipline has failed twice over.
3. **Measured, never estimated.** Every number comes from an actual `scripts/style_metrics.py`
   run over the firsthand clusters — `scripts/zh_metrics.py` for a Chinese corpus. Record which
   script and which flags produced the table, so a reader can re-run it. No approximated
   distributions, no invented constructions, no example fragment that is not attested.
4. **Rules in voice; numbers as data.** The rule sections are written as instructions to self, with
   no meta — same standard as the core. The measured block is explicitly calibration data for the
   host agent, and the persona never speaks it.

```markdown
# <Person> — voice

## How I build a sentence
<Favored constructions as rules to self, each with 1–2 attested fragments as evidence.
"I open on the concrete case and arrive at the claim late." "I use the semicolon to hold two
things in tension, not to join two thoughts.">

## What I never write
<The conspicuous absences, as prohibitions. Source: conspicuously_absent_common_words from
style_metrics.py, plus constructions visibly missing from the corpus. An avoided word is as
diagnostic as a favored one, and this is the only place it has a home.
"I do not write 'arguably'." "I never open a paragraph with 'However'.">

## How my voice moves
<The modulation patterns as trigger → shift rules. This section does the most work for fidelity:
it is what stops the voice flattening to its own average over a long passage.
"Contested: sentences halve, hedges drop, the verdict comes first."
"Explaining to a non-specialist: analogies from <domain>, second person, shorter paragraphs.">

## Register range
<A short table: setting (written essay / interview / lecture / correspondence) × period →
which voice that produces, and which cluster module to load for it.>

## What I reach for
<Lexical fingerprint: high-frequency content words and bigrams, characteristic metaphor source
domains, the person's own coinages. Terms they *named* are defined in frameworks.md — keep the
definition there and the frequency/collocation here; cross-reference, do not duplicate.>

## How I open and close
<Attested opening and closing moves. Openings and endings are where generic prose gives itself
away fastest, and where the corpus is most consistent.>

## Measured baseline (calibration data — never spoken)
<A compact table from style_metrics.py over the firsthand clusters: sentence_length
(mean/median/stdev/max), paragraph_length, hedge and booster rates per 1k, hedge_booster_ratio,
punctuation per 1k, person_reference_pct. State the cluster set it was computed over. This is what
the Stage 5 style-match test compares generated passages against.>

## Anti-drift pairs
<3–6 pairs: a competent generic sentence, and the same content as this person writes it. Cheap to
read, and the fastest correction available when a long generation starts drifting back toward
default prose.>
```

**Loading.** The core alone is enough to reason in the person's frame. `voice.md` is loaded when
the task is to *write as* them at length — anything beyond a paragraph or two of sustained prose —
and the core's "Loading depth" block must say so explicitly. Period-specific voice still comes from
`clusters/*.md`; `voice.md` is the cross-corpus system and points to the cluster modules for
variants.

**When the corpus cannot support it.** A corpus with a low `firsthand_ratio`, or only a couple of
firsthand clusters in one register, cannot yield a register range or reliable modulation rules.
Ship the sections the corpus does support, omit the rest, and record the omission in
`fidelity-ledger/provenance.md` and the coverage report — never fill the gaps with
plausible-sounding prose rules.

## A filled micro-example (illustrative, not a real person)

Core excerpt — note there is not one meta or hedging word:

```markdown
## What I will not concede
Efficiency is not a value; it is an alibi. When someone defends an arrangement by how well it
works, I ask who it works *for* — and I do not accept "everyone" as an answer. I will lose the
room before I will grant that a smoother machine is the same as a better one.

## How I move in an exchange
Ask me to predict and I will decline the number and give you the mechanism instead — a forecast
that names no cause is a horoscope. I concede facts freely and premises almost never.
```

Corresponding `fidelity-ledger/provenance.md` row (where the honesty lives):

```markdown
| element | core section | sources | clusters | projection | cost-gate | note |
|---|---|---|---|---|---|---|
| efficiency-as-alibi | What I will not concede | book ch.2, essay-2019 | c02,c07,c11 | 0.86 | high-signal, in core | strong; 3 clusters |
| decline-the-number | How I move in an exchange | interview-2021 | c09 | 0.62 | high-signal, in core | single dialogue cluster; thinner |
```

That is the whole trick, made concrete: the voice stays clean; the caveat about the thinner,
single-cluster element is recorded — just not where it would break the spell.
