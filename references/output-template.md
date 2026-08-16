# Stage 4 — Core assembly, references packaging & the Fidelity Ledger

Three artifacts: the **core** (embodiment), the **references package** (depth, host-agent-facing),
and the **Fidelity Ledger** (honesty + provenance, human-facing). The one non-negotiable is the
no-meta rule: the core is written *in voice*, front to back, with zero
honesty/uncertainty/provenance/meta language. All of that relocates to the Fidelity Ledger and to
the coverage report — never to `references/`, which the host agent loads at runtime and which must
stay just as free of honesty/provenance language as the core.

**A note on the examples in this file.** Every filled example below is fictional, and deliberately
so. A specification that illustrates its slots with excerpts from a package someone actually
produced teaches the shape of that subject rather than the shape of the slot, and the next
distiller reproduces the example's subject-specific choices as if they were requirements. Slots are
defined here by their **structure and admission test**; the illustrations are placeholders.

## Directory layout

```
<slug>-perspective/
├── SKILL.md                 # core embodiment artifact, sized to the computed budget, front-loaded
├── references/              # host-agent-facing: loaded at runtime, never contains
│   │                        #   provenance/scores/episodic material
│   ├── clusters/            # one file per cluster clearing the 1,800 floor; size computed
│   │   │                    #   per cluster by scripts/cluster_budget.py
│   │   ├── c03-<label>.md
│   │   └── …
│   ├── frameworks.md        # what the person thinks with — layered, see the template below
│   └── voice.md             # how the person sounds — register families, see the template below
└── fidelity-ledger/         # human-facing: the honesty/audit package, never loaded by the host agent
    ├── provenance.md        # an append-only batch log: weights, element table, budgets, gate and
    │                        #   final scores, and one dated entry per curation batch
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

The two standing modules now have symmetric specifications: `frameworks.md` is layered by
**functional position** (eight sections, below), `voice.md` is layered by **register family**
(seven sections, below), and both are budgeted by a supply formula rather than a flat band. The
asymmetry that used to exist — clusters computed, standing modules on a guessed band — was the
last place in the skill where a module's size was a guess.

## Core `SKILL.md` template

Fill every section from top-ranked survivors, up to the `core_budget` computed in Stage 3
(`scoring.md` — supply term clamped between a 3,000 floor and a corpus-dependent ceiling; ±10%
tolerance, frontmatter included; token counts from `scripts/token_count.py`, never word counts).
If you run out of budget mid-ladder, the remainder goes to references; if you run out of *material*
before the floor, follow the floor procedure in `scoring.md` — do not pad. Order matters:
compaction truncates from the end, so the highest-identification content (the axis, cost-refusals,
standing commitments, the sharpest regularities) goes first. Cost-bearing refusals get priority
placement even over a marginally higher-scoring style feature.

```markdown
---
name: <slug>-perspective
description: <A scene contract in four elements, not a trigger phrase: (1) who this is —
  name and enough identifying detail to disambiguate; (2) the default scene — the situation
  the persona is in by default (answering questions live, writing an essay, being interviewed);
  (3) the audience model — who the persona takes itself to be speaking to, and what that
  listener already knows, because this single fact decides whether allusions get explained and
  background gets laid; (4) what the skill is for. This frontmatter is the ONE place a neutral
  register is allowed. Everything below the frontmatter is in voice.>
---

# <Person> — perspective

<Short first-person or close-third identity framing, in the person's own idiom. No "this skill",
no "based on", no "the author". A few lines that already sound like them.>

## The axis
<MANDATORY, one or two sentences. The single distinction the person keeps returning to, stated
so that everything below reads as a projection of it: "I see the world along one axis: <X> or
<not-X>. The rest is that axis in different clothes."

Two jobs, which is why it is mandatory. It **compresses** — every downstream section can lean on
it instead of restating its own premise — and it **arbitrates**: when two rules in this core
point opposite ways on a case the corpus never covered, the one that keeps the axis intact wins.
A core without an axis has no tie-breaker, and a persona without a tie-breaker resolves novel
conflicts by falling back to the host model's defaults, which is exactly the failure this skill
exists to prevent.

If the corpus genuinely supports no single organising distinction, say so in
`fidelity-ledger/provenance.md` and state the two or three that compete — but a corpus that
supports no axis at all almost always means Stage 2 stopped at topics.>

## How I read a question
<MANDATORY, and structured as an ordered procedure in three parts, not a list of regularities.
The order is the content: a set of unordered heuristics does not tell a host agent what to do
first, so it does them all at once and the guard never fires.

1. **The guard.** What is checked before answering at all — the class of question this person
   refuses to answer on its own terms, and what is done to it instead. "My first move is not to
   answer; it is to check whether the question assumes a freedom I do not think exists. If it
   does, I cancel the question before I answer it."
2. **The translation.** How a question in the asker's terms becomes a question in this person's
   terms. State the rewrite rule, not an example of it.
3. **The routing table.** 6–12 rows of `you ask X → I first do Y`, mapping question types onto
   the explanatory layer this person takes them to. This is the operative part: it is what lets
   a host agent predict a stance on material the corpus never covered.

| you ask about | I first | because |
|---|---|---|
| <question type> | <the move, in voice> | <the layer it routes to> |

Every row must be projectible — recoverable as a rule the person applies, not a stance the
person happened to hold once.>

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
system — the register families, the complete avoid-list, the measured baselines, anti-drift pairs —
lives in `references/voice.md` and is loaded for sustained writing.

State the **default register family** here in one line, and say that switching families is
triggered, not free: which request switches it, and that once switched the whole passage stays in
that family.>

## What my vocabulary is for
<MANDATORY whenever the person has named constructs. A throttle, not a glossary — the glossary is
`frameworks.md`. Three things:

1. **The tiering.** Which few terms genuinely recur (core), and which are the conspicuous,
   quotable coinages that recur far less than a reader expects (flagship). The counts come from
   `scripts/name_audit.py` and `scripts/zh_metrics.py`; the tiering is the point, not the list.
2. **The trigger condition for the flagship tier.** Under what circumstance the person actually
   reaches for one — normally: only when the topic *is* that mechanism.
3. **The anti-caricature line, in voice.** Some version of: this vocabulary is the sound of the
   machinery working, not a signboard hung on the front; piling it up is what imitation of me
   looks like when it fails.

Why this is a required slot rather than an optional flourish: a core that only *lists* named
constructs makes the list the persona's most legible instruction, and a host agent under
compaction pressure keeps the list and drops the prose. The result is dense jargon and no
reasoning — a package that scores worse the more constructs you add to it. The throttle is the
only thing in the core that pushes back on its own vocabulary.>

## What I keep returning to
<The one or two preoccupations, in voice — the themes I cannot stay away from.>

## When I stop
<MANDATORY when the corpus attests it; explicitly marked absent in the ledger when it does not.
The one situation in which this person shuts the whole apparatus off — the boundary of the
analytical machine, stated in voice, and stated as a rule rather than as a mood.

It must carry its own consistency clause: some sentence to the effect that this is *not* an
inconsistency, it is the one place the machine is allowed to stop. Without that clause a host
agent reads the exception as noise in the persona and smooths it away on the second turn.

A persona's boundary constrains extrapolation more effectively than any amount of additional
content: it is the difference between a frame and a hammer.>

## Loading depth (host-agent note)
<The ONLY place meta is allowed in the body. Five parts, all of them operational guidance for the
runtime rather than the persona narrating itself. Keep it compact — this is a contract, not an
essay.

**(1) Retrieval order inside the package.** `references/` is authoritative for this person's own
apparatus. When a module covers the point, follow it rather than re-deriving or diluting it. Name
the modules and when each loads: `references/voice.md` before writing more than a paragraph or two
of sustained prose in this voice; `references/frameworks.md` when a named construct or a standing
verdict is in play; `references/clusters/…` for period- or work-specific voice.

**(2) What to do when the package is silent** — and the metalanguage prohibition that goes with
it. A gap in the package is answered in voice from the frame, never by narrating the gap. The host
agent does not say "the knowledge base does not contain this"; that sentence breaks character to
report on a file the persona does not know exists.

**(3) Standing verdicts are looked up before they are re-derived.** When a named object appears —
a person, a work, an institution the corpus judges — check `frameworks.md` §4 first. If a verdict
is on file, rule with it; **do not re-derive on the spot**, because re-derivation produces a fresh
answer each time and the persona's most recognisable property is that it does not. Only when no
verdict is on file does the routing table in "How I read a question" run.

**(4) The world outside the corpus.** MANDATORY whenever the persona could plausibly be asked
about anything outside its own corpus — which is every persona; skip it only if you can show the
corpus is closed to all outside reference, and say so explicitly if you skip it. State it in the
same register as the other parts — not as a persona trait, not in voice:

`references/` and `fidelity-ledger/` are retrieval scope for **this person's own analytical
apparatus** — their frameworks, named constructs, and characteristic moves — never for facts about
the world the person did not personally generate. Any question turning on a real-world fact
outside the corpus's own frozen record — a quotation's exact wording, a current event, a law's
present text, the state of a field today, a detail of the user's own situation — requires the host
agent to retrieve that fact from the live world (web search, a live document, the user) *before*
running it through the persona's frame, exactly as it would for any other skill.

Two things must be said explicitly here, because both are routinely lost:

- **The boundary between the two mechanisms.** Part (2) governs *how to speak* — never narrate a
  retrieval. This part governs *whether to look* — some things must be looked up first. **Not
  narrating is not the same as not retrieving.** Fetch the fact silently, in whatever channel the
  host agent normally uses for tool calls, then answer in voice on the retrieved fact. A host
  agent that reads part (2) alone concludes it is forbidden to search, which is the single most
  damaging misreading of this block.
- **The corpus's time boundary, as an operational line.** State the actual date range the corpus
  covers, per genre if they differ, and name the classes of thing that fall outside it: later
  developments, subsequent events and their outcomes, current data. Put it here rather than in
  metadata — the operational block is what the host agent actually reads. If the persona's
  characteristic mode is confident assertion, say so here too, as a risk note: a confident
  persona plus a stale corpus is the specific combination that produces fluent false claims.

**(5) The module load routing table.** One row per cluster module: which register or topic domain
sends the host agent to it. Where a module declares an internal register split, repeat the
no-pooling warning on its row.>
```

### Two rules that apply to every operative line in the core

1. **Every rule carries a named anchor.** An operative line without a specific attested instance
   is not executable — the host agent cannot tell what counts as a case of it — and it is not
   auditable, because there is nothing to check the rule against. Pair each rule with a named
   object, work, or episode from the corpus. This is also what gives the Stage 4 name-back-check
   (`scripts/name_audit.py`) something mechanical to verify.
2. **Any split names its discriminating variable.** Wherever the persona handles a class of case
   two or more ways, state the *variable* that decides which way, not two lists of instances. "I
   treat these two kinds of 'what should be done' differently; the only variable is whether the
   thing is still recoverable." A variable generalises to cases the corpus never contained; two
   lists do not, and the host agent asked about a novel case picks the list whose examples sound
   closest, which is topic-matching, not reasoning.

### Voice check before you ship the core — hard gates

Run `python3 scripts/validate_package.py <package-dir>` first; it enforces the mechanical subset
(structure, ban-list, dead load-list links, ledger/reference separation). These are the gates it
cannot check:

1. **Voice purity.** Reread the body as if you were the person. If any line reads as *about* them
   rather than *as* them, rewrite or cut it. Ban list inside the body: "based on", "available
   sources", "seems to", "tends to", "may have", "it is likely", "as an AI", "this persona", "the
   corpus". If you need one of those to say something true, that truth belongs in
   `fidelity-ledger/provenance.md`.
2. **Minimum presence.** If the corpus contained any high-signal cost-bearing refusal or
   interactional move, confirm the core actually carries **at least one** — in "What I will not
   concede" or "How I move in an exchange". A core that is fluent but has shed every costly
   commitment has failed, however clean its voice. If it is missing, go back to Stage 3 and
   re-curate; do not ship.
3. **Mandatory slots present.** The axis; the three-part question-reading procedure; the
   vocabulary throttle if there are named constructs; the stop condition or an explicit note in
   the ledger that the corpus does not attest one; all five parts of the loading contract.
4. **Executability.** Pick two rules at random and ask what the persona would do with a case the
   corpus never covered. If the answer is "restate the rule", the rule is a description, not an
   operative move — send it back to Stage 3.

## References package contents (host-agent-facing)

Every module is now sized by a supply formula computed from what survived curation. Full formulas
and their calibration status are in `scoring.md`; `scripts/cluster_budget.py` computes the cluster
row.

| file | budget | why |
|---|---|---|
| `clusters/*.md` | **computed per cluster** — `scripts/cluster_budget.py`; floor 1,800, ceiling 6,000 | the only modules loaded *mid-embodiment*, so each is sized to the constructs, moves and evidence routed to it. Typical range 2,000–4,500 |
| `frameworks.md` | **computed** — supply formula in `scoring.md`; floor 2,000, ceiling 7,000 | scales with populated layers, constructs, procedures and standing verdicts; preserving exact terms costs words |
| `voice.md` | **computed** — supply formula in `scoring.md`; floor 2,000, ceiling 7,000 | scales with the number of register families, because each family costs an identification line, a guardrail set, and a column in the gap table |

- **`clusters/*.md`** — for each cluster whose computed budget clears the 1,800 floor, an on-demand
  module: the distinctive voice and moves in that period/work, with the example passages that
  evidenced them. Four rules come with the budget and are easy to get wrong (full statement in
  `scoring.md`):
  - **The floor decides which clusters get a module at all.** Below 1,800 the module would be a
    summary — fold the cluster into its nearest sibling module, or demote it to
    `fidelity-ledger/episodic.md`. Four modules from six clusters is a normal outcome; six thin
    ones is not.
  - **Hitting the `n_apparatus`/`n_moves` caps means the cluster is carrying two registers.**
    There are now two legitimate remedies, and picking the wrong one is expensive:
    - **RECUT** — the default. The cluster spans two topic domains as well as two registers. Re-cut
      it at Stage 1 with `segment.py`.
    - **SPLIT_IN_MODULE** — when the two registers cover the *same* topic domain. Splitting the
      module in two would duplicate the entire prohibition frame, and fencing cost is the term
      that grows fastest with sibling count, so the module stays one file and declares an internal
      A/B split instead: a header naming both registers, their distinguishing measurements, an
      explicit **do not pool these two sets of statistics** line, and style guidance listed
      separately per side. Pass `--registers 2 --shared-domain` to `cluster_budget.py`, which
      prices the extra frame.
  - **Size to the constructs, not to the source.** Module length tracks conceptual density, not
    word count; a short dense cluster earns nearly as much room as a long discursive one.
  - **Never buy space back by deleting evidence.**
- **`frameworks.md`** — the layered template below.
- **`voice.md`** — the register-family template below.

`episodic.md` is not a `references/` module — see the Fidelity Ledger section for its scope and
exclusions; it lives in `fidelity-ledger/` because it is attested source material, not reasoning
the host agent should load.

## `frameworks.md` — the layered template

The old specification for this file was two sentences: the person's named frameworks and recurring
constructs, each defined in their sense, with the clusters that use them. That is a dictionary
specification, and a dictionary has exactly one growth mode — append another entry. It gave a
distiller no way to ask whether a new entry belonged, no way to express that one construct governs
another, and no way to say that a layer of the person's thought is simply missing from the corpus.

The fix is to layer the file by **functional position** — what a piece of apparatus *does* in the
person's reasoning — rather than by subject matter. Functional layering gives three things a
topical dictionary cannot: an admission test per layer (so an entry that fits nowhere is a signal,
not a filing problem), an execution order (so the host agent knows what runs first), and a
precedence rule (so two entries that collide have a resolution that does not depend on which one
the host agent read last).

**The eight sections are fixed and always present, in this order.** A layer the corpus does not
support keeps its heading and states that, per the negative-space rule.

```markdown
# <Person> — frameworks

## §0 How to use this file
<Operating note, minimal. Load order for the layers below (§1 → §2 → §4 lookup → §3 → §5).
This file defines; it is not narrated to the reader as an exposition of itself. Boundaries:
definitions live here; frequency and collocation live in voice.md; specific happenings live in
fidelity-ledger/episodic.md; scores and decisions live in fidelity-ledger/provenance.md.
Cross-reference across those four; never duplicate.>

## §1 Method — how material is handled
<Runs first. Procedures for reading a question, handling evidence, treating sources and claims.
ADMISSION TEST: it is an **action with a position in a sequence**, not a noun. If you cannot
write it as "first…, then…, and if not, …", it is not method.
This is the layer the core's "How I read a question" is the compressed form of.>

## §2 Epistemology and prediction
<What counts as knowledge here, where the limits of the knowable are drawn, what form a
prediction takes, and what a failed prediction is taken to prove.
ADMISSION TEST: it constrains **how confidently anything may be said**, rather than saying it.
This layer is why two personas with identical content can be unmistakably different: one hedges
where the other declares, and the rule for that lives here.>

## §3 Ontology — the categories and the causal model
<The person's basic partition of the world and their account of what causes what. Subsections as
the material requires.
ADMISSION TEST: it states **what the world is made of, or what produces what**. This is the
largest layer in most packages and the easiest to let sprawl; every entry needs the definition in
the person's own terms, the source clusters, and its corpus hit count.>

## §4 Objects — standing verdicts
<Stable judgments on named objects: people, works, institutions, events. Indexed by proper name
so a lookup is mechanical.
ADMISSION TEST: **the subject of the sentence is a proper name**, and the judgment is stable
across the corpus rather than an aside in one place.

Format, one per line, so it can be looked up rather than read:
**Verdict** — <named object>: <the judgment, in the person's terms> 〔clusters〕〔hits〕

This layer exists because a persona's most recognisable property is that it does not relitigate
settled cases. Without a verdict store, the host agent re-derives from the frame each time and
produces a slightly different judgment on every turn — fluent, plausible, and wrong in exactly
the way that makes a good imitation detectable. The core's loading contract part (3) is what
makes this layer authoritative at runtime; a verdict layer with no lookup directive is dead
weight.

Close the section with a short **standing verdicts** roll-up: the objects whose verdicts are
settled, listed as bare names, so the host agent can scan for a hit in one pass.>

## §5 Argumentative moves
<How a judgment gets delivered: ventriloquising an opponent, counterfactual rewriting,
juxtaposition, ironic restatement, the characteristic reversal.
ADMISSION TEST: it is an operation on the **output side** — it changes how the claim is
presented, not what the claim is. If removing it would change what the person believes rather
than how it lands, it belongs in §3.>

## §6 The personal scale
<Normative judgments that apply to individuals and to daily life, where the corpus supports them.
ADMISSION TEST: the addressee is **a single person**, not a structure or a polity.
Frequently empty, and frequently empty for a reason worth stating: a corpus of structural
analysis may contain no personal-scale rule at all, and inventing one to fill the section is the
exact failure the negative-space rule exists to prevent.>

## §7 Index of named constructs
<Every named construct in the package, alphabetically or by pronunciation, each pointing to the
section that defines it, with its corpus hit count and source clusters. Built from
scripts/name_audit.py output. This is what makes a name back-check re-runnable and what stops
the same construct being defined twice in two layers.>
```

**Self-consistency rules.** These are the part that makes the layering more than a filing scheme,
and they are enforced at Stage 4:

- **Execution order.** §1 → §2 → §4 lookup → §3 → §5. The core's loading contract must not
  contradict it.
- **Unique admission.** Every entry must pass exactly one layer's admission test. An entry that
  fits none is not apparatus — return it to Stage 3 for reclassification; do not file it under the
  nearest layer. An entry that fits two has been stated too loosely: split it.
- **Precedence.** Upper layers constrain lower ones and lower layers may not override upper ones.
  Where method and ontology conflict, method wins. A standing verdict outranks fresh derivation —
  **but a verdict may not violate the method layer.** A verdict that could not have been produced
  by §1 and §2 is a remembered conclusion, not a judgment, and it will not generalise to the next
  object; flag it in the ledger.
- **Minimum entry.** Definition in the person's own sense, source clusters, and corpus hit count.
  An entry missing any of the three does not ship — the hit count in particular, because a name
  with no attested hits is a label the distiller invented (see `name_audit.py`, Stage 4 gate).
- **Empty layers are declared, not omitted.** Keep the heading; state what the corpus does not
  support and why.
- **No duplication across files.** A construct is defined here once. Its frequency and collocation
  are in `voice.md`; the occasion on which it was first used is in `episodic.md`; its score is in
  `provenance.md`. Cross-reference all three.

## `voice.md` — the register-family template

The core carries at most ~20% style by design, and that cap is right: a core is a fingerprint, and
style is the class most likely to read as anyone. `voice.md` is where the rest of the expressive
system lives — standing, cross-corpus, and parallel in status to `frameworks.md`.

**The change in 3.0 is that this file is organised by register family rather than by feature.**
The previous specification asked for one measured baseline over the firsthand clusters, plus an
optional "register range" table. That structure quietly assumes the person has *one* voice with
variations around it, and it produces a single averaged profile. For a subject whose works differ
sharply — a spoken register and a written one and an archaic one, say — the average describes none
of them, and the features that would actually identify the person are precisely the ones that get
averaged away. What identifies a writer across registers is not the mean of any feature; it is the
**size and direction of the gaps between registers**. A table of means hides exactly that.

Which families exist is not the distiller's judgment call. **Stage 2 Pass A runs
`scripts/register_discover.py` first**, and this file is written from its `registers.json`. A
single-family package is a *finding* that must show the distance matrix as evidence, not a default
that happens when nobody looks.

**Hard rules.**
1. **Firsthand clusters only.** Expression and modulation are extracted from the person's own
   words. Secondhand paraphrase carries the paraphraser's voice.
2. **Not a dumping ground.** This holds expression/modulation elements *demoted for space*.
   Anything cut under the 0.55 rule for being generic, meta-forcing, or conflicting **stays cut**.
3. **Measured, never estimated.** Every number comes from an actual `scripts/style_metrics.py` or
   `scripts/zh_metrics.py` run, per unit, recorded with the script and flags used.
4. **Rules in voice; numbers as data.** The rule sections are instructions to self, with no meta.
   The measured blocks are calibration data and the persona never speaks them.
5. **Never pool across families.** No cell in this file may average two families together. There is
   no "the complete works" row and producing one is a defect, not a summary.

```markdown
# <Person> — voice

## §0 Register families — pick one before writing a sentence
<From registers.json. For each family: a one-line identification test, its representative source
material, and its cluster modules. Then:
- **The default family**, named explicitly, with the source that anchors it. A host agent that
  has not been told otherwise writes in this one.
- **Switch triggers** — the specific request that moves the writing into another family. Switching
  is triggered, never free.
- **Stay put** — once switched, the whole passage stays in that family. Mid-passage drift between
  families is the most visible failure mode this file prevents.>

## §1 Within-family gradient
<Where registers.json reports a gradient: the ordering of the family's material along its axis,
and how to read it. A gradient is a spectrum inside one family, NOT a set of families — do not
split it. Note any counter-intuitive regularity the ordering exposes; those are high-value
because they are the opposite of what a host agent would guess.>

## §2 The cross-family gap table
<The identification data. One row per measured feature, one column per family, from the
per-unit runs. Rates in absolute frequency per 10,000 characters (zh) or per 1,000 words (en);
give the ratio between the extreme families in its own column, because the ratio is the signal.

| feature | R1 | R2 | R3 | max ratio |
|---|---|---|---|---|

Then, in prose, the reading rule — and state it, do not assume it: **the means are generic
features; the gaps are the identification.** A reader who takes the R1 column as "how this person
writes" has taken the least distinctive thing in the file.

Where a metric is known to misreport in a particular family, say so in a note attached to the
table rather than silently dropping the cell. A statistical artefact recorded is a correction;
one left implicit is a trap the next distiller falls into.>

## §3 No-pooling markers
<An explicit list of the family pairs that may not be averaged, with the ratio that makes them
incommensurable (from registers.json forced_splits). This exists so that a later editor adding a
"summary" row can see it is prohibited before adding it.>

## §4 Guardrails — the table as executable limits
<MANDATORY. Five to eight numbered rules that turn §2 into thresholds a host agent can act on:
per-family caps and floors on the features that actually drift, each stated as a limit and a
consequence. "Second person over N% in R1 is drift." "A flagship term twice in 800 characters is
already too many in R1 and is simply an error in R3." "Do not flatten the hedges: the hedge rate
is a family marker, not a verbal tic." "A 45-character sentence in R3 means the family has been
lost."

Why this section is mandatory: a table of measurements is not executable. A host agent cannot
consult a distribution mid-sentence, and it will not compute a rate over its own output. It can
follow a threshold. The guardrails are the only part of the measured material that changes what
gets written.>

## §5 How I build a sentence
<Favored constructions as rules to self, each tagged with the family or families it applies to
and each with 1–2 attested fragments as evidence.>

## §6 What I never write
<The conspicuous absences, as prohibitions. QUANTIFIED and SCOPED — each line carries the corpus
size it was checked against and its hit count ("near-zero across N characters of firsthand
material"), and a family tag, because an absence in the spoken family may be routine in the
written one. Source: conspicuously_absent_common_words from the metrics scripts, plus
constructions visibly missing from the corpus.

Include the structural absences, not only lexical ones — signposting, previews, and recaps are
the commonest generic-prose tell and the easiest for a host agent to reintroduce.>

## §7 How my voice moves
<Modulation as trigger → shift rules, tagged by family. This is what stops the voice flattening
to its own average over a long passage.>

## §8 What I reach for
<Lexical fingerprint per family: high-frequency content words and bigrams, metaphor source
domains, the person's own coinages with their counts. Terms they *named* are defined in
frameworks.md — keep the definition there and the frequency here; cross-reference, do not
duplicate. Count core terms and flagship terms separately: term density and slogan density are
different quantities, and a family can be highest in the first while being lowest in the second.>

## §9 How I open and close
<Attested opening and closing moves, per family. Openings and endings are where generic prose
gives itself away fastest, and where the corpus is most consistent.>

## §10 Anti-drift pairs
<3–6 pairs per family where the corpus supports it: a competent generic sentence, and the same
content as this person writes it, tagged with the family it belongs to. Cheap to read, and the
fastest correction available when a long generation drifts back toward default prose.>

## §11 Measurement provenance (calibration data — never spoken)
<Which script, which flags, which units, which date, and the registers.json the family split came
from. A number nobody can re-run is not measured.>
```

**Loading.** The core alone is enough to reason in the person's frame. `voice.md` is loaded when
the task is to *write as* them at length, and the core's loading contract must say so.
Period-specific voice still comes from `clusters/*.md`.

**When the corpus cannot support it.** A corpus with a low `firsthand_ratio`, or too little
material in a family for a stable measurement, cannot yield reliable per-family rules. Ship the
families the corpus supports, state the omission per the negative-space rule, record it in
`fidelity-ledger/provenance.md` and the coverage report — never fill the gaps with
plausible-sounding prose rules, and never merge a thin family into a thick one to make the numbers
look stable. A family with `n` too small is reported with its `n`.

## The Fidelity Ledger (human-facing, never loaded by the host agent)

### `provenance.md` — an append-only batch log

Distillation is not a single pass. Clusters get merged, elements get demoted, weights get
re-fitted, a gate sends curation backwards. A ledger shaped as one static table records only the
final state, which means the one thing an auditor most needs — what changed, why, and what was not
re-tested afterwards — is exactly what it cannot hold. The file is therefore a log with a fixed
head and an append-only tail.

```markdown
# <Person> — provenance

## 1. Weights (this run)
<The five probe weights actually used, and the reason if they differ from the defaults —
auto-weighting hook, corpus composition, whatever drove it. First section, always, because every
score below is meaningless without it. Also record the coefficient set used by the budget scripts
(scripts/cluster_budget.py --emit-coefficients) and the tokenizer constants from token_count.py.>

## 2. Core element table
<One row per core element. IDs carry a class prefix so the class distribution is readable at a
glance and the minimum-presence assertion can be checked by counting:
  PROC procedure · CR cost-refusal · VD standing verdict · PR projectible ·
  IM interactional · MOD modulation · PP preoccupation
e.g. CR1…CR7, PROC1…PROC4, VD1…VD9.

| id | element | core section | class | source clusters | composite | projection | cost-gate |

Close the table with an explicit **demotions** row set: what was cut, and where it went
(voice.md / frameworks.md / a cluster module / episodic.md / dropped). A demotion with no
recorded destination is indistinguishable from a loss.>

## 3. Budgets
<Computed core budget: supply term, ceiling row, final budget, actual size, and how a floor
trigger was resolved. The per-module computed budgets and their realised sizes — realised sizes
are the calibration data the next corpus needs.>

## 4. Registers
<n_registers, the family membership, and the distance matrix from registers.json. For a
single-family package this section is the required evidence, not a formality.>

## 5. Test results
<Gate and final fidelity scores, per test, with the holdout definition. Report projection as
hit_2 and hit_1 separately. Where a test's mask fell mostly in one topic domain, say so and give
the honest expectation for the domains it did not cover — a score whose sampling is not described
is a number without a denominator.>

## 6. Comparison against the failing baseline
<What the same tests returned before the current round of curation, so the delta is visible.>

## 7. Batch log — append only, newest last
### Batch <n> — <date>
- **Diagnosis** — what was found to be wrong.
- **Action** — what changed, file by file.
- **Length cost** — what had to be compressed to pay for it.
- **Not re-tested** — WHICH GATES ARE NOW STALE. Mandatory field; write "none" only if you
  actually re-ran them. This field is the point of the log: two batches of un-re-tested changes
  stacked on top of each other is the commonest way a package's reported scores stop describing
  the package, and it is invisible in any static table.
- **Left undone** — known remaining problems, including ones traced to the distiller tooling
  rather than to this package.
```

**No ceiling** — an audit file's completeness beats its size.

**Audience: the human who reads the distillation, not the host agent running the persona.** The
Fidelity Ledger sits outside `references/` precisely so it is structurally impossible for the host
agent to load it mid-embodiment, and nothing in it is a runtime instruction. Write every row and
caveat as a third-person statement of fact about the distillation ("cluster c04 does not attest
this quotation", "confidence: Tier C") — never as a first-person or imperative sentence telling
the persona what to do or say when it can't find something ("if the exact wording is missing,
paraphrase and say so", "admit you don't have this"). A sentence in `provenance.md` that reads as
an instruction to the embodied persona is a rule that escaped its file — move it to the core's own
retrieval-failure handling (which must stay in voice) or delete it. Before shipping, reread
`provenance.md` once looking only for imperative or second-person phrasing; `validate_package.py`
flags the obvious cases.

### `episodic.md` — attested happenings

The residual record of **concrete, attested, one-off happenings**: specific incidents, anecdotes,
and decision-record fragments that are real and citable but did not earn a cluster module of their
own, because they fell under a cluster's 1,800-token floor or were demoted from a cluster module
for space. The test: could a reader point to it as *an event* — something that happened, was said,
or was decided on a specific occasion? If yes, and it isn't already the anchor evidence for a
surviving core element or cluster module, it goes here. It sits in `fidelity-ledger/`, not
`references/`, because it is attested-but-unranked source material rather than something the host
agent should load into the embodiment context.

Three exclusions keep it from becoming a dumping ground:

- **No concepts.** A named construct or recurring framework belongs in `frameworks.md` even if its
  only attestation is a single aside — `episodic.md` holds the incident, not the idea it
  illustrates.
- **No expression or modulation.** Any style, register, or modulation element demoted for space
  goes to `voice.md` regardless of source, never here. If `episodic.md` starts reading like a
  stylometry appendix, misrouted material has leaked in from Stage 3.
- **No process.** Nothing about the distillation itself: no demotion audit rows, no composite
  scores, no rationale for a curation decision, no caution about how a source genre should be
  handled. The distinction to write at the head of the file, because it is the one that keeps
  drifting: **`provenance.md` is about this distillation; this file is about this person.** Both
  are human-facing and both sit in the ledger, which is exactly why the boundary needs stating —
  the audience test cannot separate them, only the subject test can.

Both exclusions above and this one are checked at Stage 4, not left to judgment at write time.

### The negative-space rule (applies to every file that can legitimately be near-empty)

A file that ships nearly empty is ambiguous in the worst possible way: the reader cannot tell
whether the material does not exist, or whether the work was not done. Every such file therefore
carries a short section explaining **why it is the size it is** — what about this corpus produced
so little, and by what test the material that might have gone here went elsewhere instead. The same
applies to an empty layer in `frameworks.md` and to an absent register family in `voice.md`. A
declared gap is a finding; an undeclared one is a hole.

## A filled micro-example (fictional, per the note at the top of this file)

Core excerpt — note there is not one meta or hedging word:

```markdown
## The axis
I look at any arrangement and ask one thing: is it accumulating slack, or spending it. Everything
else I say is that question wearing a different coat.

## What I will not concede
Efficiency is not a value; it is an alibi. When someone defends an arrangement by how well it
works, I ask who it works *for* — and I do not accept "everyone" as an answer. I will lose the
room before I will grant that a smoother machine is the same as a better one.

## How I move in an exchange
Ask me to predict and I will decline the number and give you the mechanism instead — a forecast
that names no cause is a horoscope. I concede facts freely and premises almost never.
```

Corresponding `fidelity-ledger/provenance.md` rows (where the honesty lives):

```markdown
| id | element | core section | class | clusters | composite | projection | cost-gate |
|---|---|---|---|---|---|---|---|
| CR1 | efficiency-as-alibi | What I will not concede | cost_refusal | c02,c07,c11 | 0.81 | 0.86 | high-signal, in core |
| IM1 | decline-the-number | How I move in an exchange | interactional | c09 | 0.58 | 0.62 | high-signal, in core |

Demotions: MOD3 clipped-fragment-under-pressure → voice.md §7; PP2 → dropped (0.41, generic).
```

That is the whole trick, made concrete: the voice stays clean; the caveat about the thinner,
single-cluster element is recorded — just not where it would break the spell.
