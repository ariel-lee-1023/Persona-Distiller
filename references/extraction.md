# Stage 2 — Multi-granularity extraction

Standard source authoring follows [situated-evidence.md](situated-evidence.md).
The catalogue below preserves useful detail about what to notice. Quantitative
register discovery and transfer/discrimination admission are research procedures;
they are not prerequisites for retaining supported conditional guidance in standard
mode. Apply source recovery only within the separate finite reading/OCR boundary.



Three passes, run over the segmented clusters. The output is `extractions.json`: a flat list of
candidate elements, each with evidence, ready for Stage 3 scoring. The central discipline of this
stage is to **spend effort in proportion to diagnostic value, not ease of measurement** — the easy
pass (fine-grained) is necessary but cheap; the two hard passes are where identification is won.

---

## Pass A — Fine-grained expression (every cluster)

### A0 — Register discovery, before any measurement is pooled

**Before new pooled measurements, use applicable register discovery evidence. Incremental
upgrades reuse unaffected results; unresolved discovery remains unresolved in standard mode.**

Until 3.0 this pass began by running the metrics script over the whole corpus, and the register
question was raised only later, optionally, as a discrimination test that fired "if the core claims
registers". Both halves of that were wrong. The claim was the distiller's discretion, so the check
never fired unless someone had already noticed; and the whole-corpus run had by then produced a
single averaged profile that gave nobody a reason to notice. A subject whose works differ sharply
in register — a spoken body and a written one, an early register and a late one, a vernacular and
an archaic one — came out of this pass as one voice that is the mean of two and the likeness of
neither, with no artifact anywhere in the pipeline recording that anything had been lost.

So: measure per unit, then decide whether pooling is allowed.

1. **Split the corpus into units** — one work, one genre, or one collection per unit. Units are not
   clusters; a cluster can straddle two units and that is one of the things this step detects.
2. **Run the discovery script.** It computes a 13-dimension feature vector per unit, standardises
   across units, builds a pairwise distance matrix, and clusters into families under a hard
   constraint: any pair that exceeds the ratio threshold on three or more dimensions is
   *incommensurable* and may never share a family.
3. **Read the verdict.**
   - `INSUFFICIENT_EVIDENCE` — keep the finding, narrow register claims and preserve supported
     reasoning. Do not automatically search more subsets or commission another evaluation round.
   - `MULTI_REGISTER` — the families are the organising unit for the rest of the pass, for
     `voice.md`, and for the cluster budgets. Every subsequent measurement is per family. The
     discrimination test in `fidelity-tests.md` is required for strict research qualification.
     Standard delivery records this evaluation as incomplete unless reusable evidence exists.
   - `SINGLE_REGISTER` — a finding, not a default. Copy the distance matrix into
     `transworld-identity/provenance.md` §4 as the evidence for it. A single-family package that cannot
     show the matrix has not established anything; it has merely not looked.
4. **Check the gradient report.** A family whose members line up monotonically along one axis is a
   *spectrum inside one family*, not several families. Do not split it. Record the ordering — it is
   directly useful in `voice.md` §1, and the regularity it exposes is often counter-intuitive,
   which makes it exactly the kind of thing a host agent will get wrong unaided.
5. **Check family boundaries against cluster boundaries.** Where a family cuts across a cluster,
   that cluster is carrying two registers and Stage 4 will have to choose between RECUT and
   SPLIT_IN_MODULE (`scoring.md`). Note it now, while the evidence is in front of you.

Write `registers.json` to the work directory. `n_registers` also goes into `coverage_map.json`.

### A1 — Per-family measurement

Countable style features **and their modulation**, measured **within each family** — never pooled
across families. Run `scripts/style_metrics.py` per unit and per cluster so you have real numbers,
then read the *shifts*, not just the averages. For a Chinese corpus run `scripts/zh_metrics.py`
instead — same feature classes, measured in 汉字, with Chinese hedge/booster sets; the
Latin-tokenising script reports zeros and will quietly cost you the entire expression pass. Track
the subject's own vocabulary with its `--terms` flag, and count **core terms and flagship terms
separately**: a family can be the densest in technical vocabulary while being the sparsest in the
quotable coinages a reader thinks of as the subject's signature, and collapsing the two into one
"term density" number hides the single most useful thing this measurement produces.

Measure:
- **Sentence-length distribution** — mean, median, spread, and the shape (does the person mix long
  periodic sentences with abrupt short ones? that mix is more individuating than any average).
- **Hedging vs. boosting** — rates of "perhaps/it seems/arguably" vs "obviously/clearly/in fact".
- **Punctuation rhythm** — em-dashes, semicolons, colons, parentheticals, rhetorical questions.
- **Lexical fingerprint** — high-frequency content words and bigrams; and, harder, **conspicuously
  absent** common words the person avoids (compute by comparing their content-word set against a
  generic baseline — an avoided word can be as diagnostic as a favored one).
- **Person reference** — first / second / third-person ratios; do they address the reader?
- **Analogy / metaphor density** and their source domains (nautical? legal? biological?).
- **Rhythm markers** — anaphora, tricolon, sentence-initial conjunctions, one-line paragraphs.

**Modulation is the point.** For each feature, note how it moves across `kind` (dialogue vs
monologue), audience (expert vs lay), and stakes (calm exposition vs contested point). Record e.g.
"sentence length halves and boosters spike when challenged" — that *pattern of variation* is a
high-value element, whereas the bare average is low-value and probably generic.

**The cross-family gaps are the identification.** Within a family, the means are mostly generic —
they describe the genre as much as the person. What is hard to fake, and what no other writer will
reproduce by accident, is the *size and direction of the shift* between one family and the next: a
second-person rate that falls by two orders of magnitude, a connective rate that goes to zero, a
hedge rate that thirds. Emit each large cross-family gap as its own candidate element, with both
endpoints and the ratio. These score high on expressive match precisely because a bare average
scores low.

Emit each stable feature, each modulation pattern, and each cross-family gap as separate candidate
elements.

Where a metric is known to misreport inside a family — a person-reference ratio computed by a
script whose pronoun list does not fit an archaic register, say — record the artefact next to the
number rather than dropping the cell. An artefact that is written down is a correction for the next
reader; one that is silently removed is a hole, and one that is left unremarked is a trap.

Run this pass on **firsthand clusters only**. Secondhand paraphrase carries the paraphraser's
sentence rhythm, not the subject's, and averaging the two produces a voice belonging to neither.

> Caution: it is tempting to fill the persona with this pass because it is easy and produces tidy
> numbers. Resist. Most raw style metrics score low on identification once you account for how
> generic they are. Keep the *distinctive mix* and the *modulation*; discard the rest.

What survives this pass has two destinations, and the split happens in Stage 3: the few most
identifying features go to the core's "How I sound" (capped at ~20% of it), and everything else
that survived the deletion rule goes to **`references/voice.md`** — the standing expressive-system
module. So extract the full picture here rather than pre-trimming to what a core could hold; in
particular, the **conspicuously absent** words and the per-register numbers have a home now, and
they are among the most useful things this pass produces.

---

## Pass B — Coarse-grained projectible regularities (across clusters)

These are the person's recurring **thought-moves** and **decision heuristics** — the cognitive
operating system. A candidate is only recorded if it passes all three gates (adapted from the
triple-verification standard):

1. **Cross-cluster recurrence** — appears in **≥2 independent clusters**, not a one-off line.
2. **Predictive power** — from the remaining evidence you can infer the person's stance on a
   question they did *not* explicitly address in the masked passage. If it can only reproduce known
   statements, it is a quote, not a regularity.
3. **Exclusivity** — not something any thoughtful person would say. If it is generic wisdom, it does
   not individuate and does not belong. ("Think before you act" fails; a specific characteristic
   inversion they habitually perform passes.)

Write each as an operative rule in the person's own logic — "When facing X, reframes it as Y
before evaluating", "Treats institutional claims as suspect until Z" — with the clusters it appears
in and 1–2 example passages. State it as a *move the persona makes*, not as a description of the
person ("does X when Y", never "the author tends to").

**Use `scripts/kwic.py` to pull the evidence and to test gate 1.** `grep` is the wrong instrument
here: extracted prose arrives with paragraphs on single lines thousands of characters long, so a
match returns the entire paragraph, and a match straddling a line break is missed altogether. The
script normalises whitespace first and returns a fixed-width window around each hit — the shape
evidence actually needs — and `--json` writes straight into an element's `evidence` field.

`--count` is the cross-cluster recurrence check made cheap: it reports hits per cluster, so you can
see at a glance whether a candidate clears the ≥2-independent-clusters bar or is a one-off you were
about to promote. It says so explicitly when only one cluster contains the pattern.

One trap, because it costs an hour every time: **the pattern is a Python regex, not a shell one.**
Alternation is `a|b`. Writing `a\|b` — the habit from grep and sed — matches a literal pipe and
returns nothing, which is indistinguishable from a corpus that genuinely lacks the passage. The
script warns when it sees `\|`, but the general rule holds: an empty result on a term you are
confident about is a tooling failure until proven otherwise, never a finding about the corpus.

Adversarial / critical sources, if present in the corpus, are especially useful here: the places
where critics push back reveal where the person's real decision boundaries are. Distilling only
flattering material yields hagiography, not a decision architecture.

---

## Pass C — Interactional & cost-bearing (prioritize dialogue + decision records)

This pass extracts the single highest-value class of signal. Two overlapping catalogues:

### Cost-bearing refusals & standing commitments
Hunt for every place where the person's **characteristic** response **diverges from the convenient
or generic** one — where they paid, or risked, something to hold a line:
- positions maintained against their own audience, tribe, or interest;
- questions they refuse to answer, or reframe rather than accept;
- concessions they will not make even under pressure;
- lines that recur as non-negotiable across clusters.

For each, record **both** sides explicitly: the convenient/expected move *and* the attested
characteristic move. That divergence pair is what the Stage 5 cost test checks, and it is the
fingerprint most responsible for expert-level identification. Flag these prominently.

### Interactional moves
In any exchange (interview, debate, Q&A, correspondence), catalogue *how* the person handles a
turn — the repeated shape of their engagement:
- **concede** — what they give ground on, and how gracefully;
- **reframe** — how they redraw the question before answering;
- **dig in** — where and how they refuse to move;
- **shift footing** — changing register, stance, or level (e.g. from particular to principle) mid-exchange.

Record the *pattern* ("when asked for a concrete prediction, shifts to the principle at stake
rather than naming a number"), the clusters, and an example. These moves are invisible in
monologic summary but decisive for embodiment, which is why dialogue-rich corpora get up-weighted.

---

## Output of Stage 2

`extractions.json` — a flat list; each element:

```json
{
  "id": "CR1",
  "type": "cost_refusal",          // expression | modulation | regularity | cost_refusal |
                                   //   interactional | preoccupation | procedure | verdict
  "statement": "Holds that <line> even when <audience> expects the opposite.",
  "convenient_move": "…",           // required for cost_refusal; optional for interactional
  "clusters": ["c03", "c09", "c11"],
  "register_family": "R1",          // from registers.json, when the element is family-specific
  "evidence": ["short passage 1", "short passage 2"],
  "metrics": {}                     // for expression/modulation, from style_metrics.py
}
```

**IDs carry a class prefix** — `PROC` procedure, `CR` cost-refusal, `VD` verdict, `PR` projectible,
`IM` interactional, `MOD` modulation/expression, `PP` preoccupation. A flat `e017` tells a reader
nothing; a prefixed ID makes the class distribution readable by scanning, which is what the
minimum-presence assertion and the elevation rules both need. Renumbering within a class is cheap;
reclassifying an element means changing its ID, which is correct, because it is a different
element.

### The two classes added in 3.0

**`procedure`** — an ordered step in how the person handles a question, rather than a position they
hold. The three shapes are a **guard** (what is checked before answering at all, and what is done
to a question that fails the check), a **translation rule** (how a question in the asker's terms
becomes one in the person's terms), and a **routing row** (a question type mapped to the
explanatory layer this person takes it to). Emitting these separately from `regularity` matters
because a procedure has a *position in a sequence* and a regularity does not: a set of unordered
heuristics gives a host agent no way to know what runs first, so it applies them simultaneously
and the guard — the step whose entire value is that it fires before everything else — never fires
at all.

```json
{
  "id": "PROC1",
  "type": "procedure",
  "order": 1,
  "precondition": "any question phrased as a choice among options",
  "statement": "Checks whether the question assumes a freedom that does not exist; if it does, cancels the question before answering it.",
  "on_fail": "answer the question as asked",
  "clusters": ["c02", "c05", "c09"],
  "evidence": ["…"]
}
```

Admission test: you must be able to write it as "first …, then …, and if not, …". If you cannot, it
is a `regularity`.

**`verdict`** — a stable judgment on a **named object**: a person, work, institution, or event the
corpus settles rather than reopens. Verdicts were previously homeless. A judgment on a proper name
is not projectible in the ordinary sense — it predicts nothing beyond its own object — so the
Stage 3 rubric scored it low and the deletion rule removed it, which is why distilled packages kept
losing exactly the judgments a reader would recognise fastest. Worse, with no store of settled
cases the host agent re-derives one on every turn from the frame, producing a slightly different
verdict each time: fluent, plausible, and the most detectable failure mode a persona has.

```json
{
  "id": "VD3",
  "type": "verdict",
  "object": "<proper name>",
  "judgment": "<the settled judgment, in the person's own terms>",
  "corpus_hits": 11,
  "clusters": ["c01", "c04", "c06", "c08"],
  "evidence": ["…"]
}
```

Admission test: the subject of the sentence is a proper name, the judgment is consistent across
≥2 clusters, and `corpus_hits` comes from an actual run of `scripts/name_audit.py` — not from
memory. A judgment attested once, in an aside, is an aside; it goes to `episodic.md`.

Keep evidence passages short and treat them as *evidence*, not as text to paste into the core —
the core is written in the persona's voice from these regularities, not stitched from quotations.
Hand the full list to Stage 3.
