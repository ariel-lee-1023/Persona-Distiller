# Pipeline mechanics — ingestion, segmentation, coverage map

Read this before running Stage 1 the first time. It covers how to get clean text out of mixed
formats, how to cut the corpus into clusters, and the internal artifacts the later stages depend on.

Before semantic extraction, follow [release-evidence.md](release-evidence.md): assign work/episode
groups using metadata, create `split.json`, and materialize separate train, development and test
collections. All construction steps below operate on train only. Coverage reports distinguish
training coverage from held-out coverage. Keep final targets sealed until final verification.

## Working directories

**Create the work directory before anything else.** Default to `persona_work/` under the current
working directory; use a host-provided scratch or temp location instead when one exists. Every
later stage reads and writes here, so resolve the path once and reuse it.

```
<work-dir>/                # default: ./persona_work/
├── raw/                   # extracted plain text, one file per source
├── clusters/              # segmented clusters, one file per cluster, with a manifest
├── coverage_map.json      # domains, dialogue ratio, decision density, temporal spread
├── registers.json         # Pass A0 output: register families, distance matrix, verdict
├── extractions.json       # Stage 2 output: every candidate element with evidence
├── scores.json            # Stage 3 output: class admission + within-class ranking + keep/cut reasons
└── fidelity.json          # gate results + Stage 5 results
```

Keep these artifacts for the whole run — do not clean up between stages. Three things depend on it:
the control flow is a **loop** (a failed gate sends you back to re-curate, which needs
`extractions.json` and the previous `scores.json`); the hard deletion rule is only defensible
because `scores.json` logs every keep/cut with its reason; and the honesty split relocates all
caveats into the coverage report and `fidelity-ledger/provenance.md`, which are built from
`coverage_map.json` and `fidelity.json`.

Only the finished persona directory is delivered to the user, at the persona-out location resolved
at the start of the run. The work dir is your scratchpad and stays behind.

**If the work dir sits inside a git repository, confirm it is ignored before writing.** `raw/` holds
the extracted full text of the source corpus; committing it would republish the sources.

Shapes for every JSON artifact above: [`schemas/`](schemas/) — authoritative and validatable. The
snippets in this file are illustrative and some carry `//` comments for readability, so they will
not parse if copied verbatim.

## Extraction routing by file type

**First, the corpus has to exist on disk.** If it was handed to you as a git URL, a file URL, or a
docs site or wiki, run the acquisition procedure in [`acquisition.md`](acquisition.md) before any of
this: fetch it, split the person's material from the container's own scaffolding and get the user to
confirm that split, and label every unit `firsthand` / `secondhand` / `mixed` / `unknown`. The
labels are load-bearing downstream — expression metrics run on firsthand text only — so they must be
attached before extraction, not reconstructed after.

Preserve structure — headings, speaker turns, timestamps — because segmentation and the
interactional pass depend on it.

Each row below gives a **preferred** route and a **fallback**. If your host offers a
document-reading tool or companion skill for a format, prefer it; otherwise take the fallback,
which needs only common libraries or a standard CLI. Never fail a run because a preferred tool is
absent — fall back and note any resulting quality loss in the coverage report.

| Format | Preferred | Fallback | Keep |
|---|---|---|---|
| TXT / MD | read directly | — | headings, lists, quotes |
| HTML | host HTML reader | strip tags, keep heading levels and blockquotes | headings, lists, quotes |
| PDF | host PDF-reading tool (essential for scanned or complex layouts) | `pdftotext -layout`, else `pypdf` | page breaks, headings |
| EPUB | `ebooklib` | unzip and read spine XHTML in document order | chapter boundaries |
| DOCX | host DOCX tool | `python-docx` | headings, styles |
| Transcripts | read directly | — | who-said-what, turn order |

Sanity-check every extraction: if a file yields near-empty or garbled text (common with scanned
PDFs), flag it and either OCR it or note it as unusable in the coverage report — do not silently
distill from noise.

**Run `scripts/corpus_clean.py` over `raw/` before anything reads it.** Wholesale garbling is easy
to see; the damage that actually costs you is not, because it leaves fluent, readable text that
measures wrong:

- **Ligature loss** — PDF and EPUB extraction drops fi/fl/ff/ffi, so *first* arrives as `rst` and
  *difference* as `dierence`. The prose still reads; the lexical fingerprint and the
  conspicuously-absent-words list are both corrupted, and quoted evidence is unusable.
- **Soft hyphenation** — justified columns wrap words across lines (`transporta- tion`), and every
  wrapped word is counted as two. Inflates word counts and sentence-length means by 1–2% and
  scatters fragments through the top-terms list.
- **Markup residue** — EPUB anchors and page-position tokens survive conversion and enter the
  corpus as high-frequency "content words".

The script reports by default and writes only with `--fix`. Read the census first: it separates a
confirmed ligature problem (suspect tokens per 10k words; damaged corpora run 50–100× a clean one)
from a mere screen signal (a low `f` rate, which false-positives on short files). Anything measured
before this ran has to be re-measured after it — a baseline taken over damaged text is not a
baseline, and every expressive-match score downstream inherits it.

## Segmentation into clusters

A **cluster** is a coherent unit that can carry independent evidence. Good cluster boundaries:

- **By work / chapter** for books and long essays.
- **By session** for interviews, talks, podcasts (one cluster per interview).
- **By decision** for decision records / project write-ups (one cluster per documented choice).
- **By time period** when you have a long span and want to track evolution (e.g. pre-2015 vs post).
- **By register** when the same person writes very differently in different venues (scholarly vs
  social) — split so the modulation is visible rather than averaged away.

The reason clusters matter: the projectibility probe requires a regularity to appear in **≥2
independent clusters**. If everything is one blob, nothing can be corroborated, and you will
over-trust one-off remarks. Err toward more clusters, but keep each large enough to be meaningful
(a two-sentence "cluster" corroborates nothing).

### The one boundary that is never allowed: the acquisition batch

**Hard rule: never cut clusters along the boundary of the batch in which the material arrived.**
Not as a default, not as a temporary measure, not "for now, to be merged later".

The pressure to do it is real, which is why the rule has to be explicit. Corpora arrive in
instalments — a second tranche of sources, a later download, a follow-up upload. Cutting the new
instalment into its own clusters is the path of least resistance: it needs no reading, it never
conflicts with the existing manifest, and the numbers all still add up. And it destroys the one
thing clusters exist for. The projectibility probe asks whether a regularity appears in ≥2
**independent** clusters. Two clusters cut from the same delivery are not independent evidence of a
regularity; they are one body of text with a line drawn through it for the distiller's filing
convenience. Worse, the failure inflates rather than deflates: a regularity attested only in the new
batch now clears the corroboration bar and is promoted, so batch-cut clusters manufacture
projectibility instead of testing it.

The correct move when a batch arrives:

1. **Read what topics the new material covers**, before deciding any boundary.
2. **Check each topic against the existing clusters.** `scripts/kwic.py` over `clusters/` with the
   topic's key terms is enough: it shows in one pass whether the topic is already attested and
   where.
3. **Where a topic already exists**, the new material either extends an existing cluster or forms a
   cluster whose boundary is drawn by *work, session, period, or register* — the same four criteria
   as any other cluster, applied to the merged corpus, ignoring which delivery each file came from.
4. **Where a topic is genuinely new**, a new cluster is correct — because the boundary is topical,
   not chronological-by-delivery. It coincides with the batch; it is not defined by it.
5. **Record the check.** The batch log in `fidelity-ledger/provenance.md` states which existing
   clusters the new material was tested against and what the overlap was. An unrecorded check is
   indistinguishable from no check.

The diagnostic, if you want one number: for every pair of clusters that share a topic domain, ask
whether they also share a delivery. If the answer is yes for most pairs, the manifest is a delivery
ledger wearing cluster labels, and every corroboration count computed from it is suspect.

Write a `clusters/manifest.json`:

```json
{
  "clusters": [
    {"id": "c01", "label": "Book: <title> ch.3", "source": "raw/book.txt",
     "kind": "monologue", "period": "2018", "tokens": 4200,
     "attribution": "firsthand"}
  ]
}
```

`kind` is one of `monologue | dialogue | decision_record`. It determines which class admission evidence Stage 3 can support.

`attribution` is required and one of `firsthand | secondhand | mixed | unknown` — see
[`acquisition.md`](acquisition.md) for how to assign it and the three hard rules that depend on it.
Remote clusters also carry `source_url`, `retrieved`, and (for git) `revision`.

**`scripts/segment.py` performs the cut and writes the manifest.** You give it a spec naming each
cluster and where it starts and stops — line numbers, or regexes matched against the source — and
it slices, strips the running headers that repeat on every page of a scanned book, counts words,
and emits a manifest that validates against the schema. Prefer regex boundaries: they survive
re-extraction of the same source, and line numbers do not.

It exists because cutting a multi-work volume by hand produces two errors that are invisible
afterwards. **Boundary drift** — a slice running past the end of one work into the next — gives you
a cluster that mixes two registers, and every per-cluster metric then averages across them.
**Editorial bleed** — front matter, historical introductions, translator's notes, endnotes and
indexes captured as the subject's own words — quietly inflates the firsthand ratio the whole run is
scored against. Use `--dry-run` to check the boundaries land where you think before writing
anything; it reports each cluster's line span and word count, flags any cluster too small to
corroborate, and computes the firsthand ratio that will set the core-budget ceiling.

## Coverage map

After segmentation, compute `coverage_map.json`. This is the backbone of the honest coverage
report and of the available class admission evidence.

```json
{
  "total_tokens": 128000,
  "n_clusters": 14,
  "firsthand_ratio": 0.82,           // firsthand tokens / total — set during acquisition
  "domains": ["political philosophy", "religion", "economics"],
  "dialogue_ratio": 0.35,            // dialogue+decision tokens / total
  "decision_density": 0.12,          // decision-record tokens / total
  "temporal_spread": {"earliest": "2006", "latest": "2024", "gaps": ["2011-2014"]},
  "thin_domains": ["foreign policy"],   // present but under-attested
  "n_registers": 3,                     // from registers.json (Pass A0); 1 = SINGLE_REGISTER
  "notes": "Heavy on monologic prose; little live dialogue."
}
```

Use it to:
- **Auto-weight** — high `dialogue_ratio` → raise the interactional pass and probe weight; low
  → lean on projectible-regularity extraction.
- **Set expectations** — `thin_domains` and `temporal gaps` become explicit caveats in the
  coverage report handed to the user (never in the persona).
- **Bound scope** — if `total_tokens` is very low or `domains` is one narrow slice, plan for a
  reduced-scope core up front.
- **Set the core's ceiling** — `total_tokens`, `n_clusters`, `firsthand_ratio`, and the number of
  periods in `temporal_spread` pick the ceiling row in the Stage 3 core-budget computation
  (`scoring.md`). Get these right here; Stage 3 does not recompute them.
- **Size the cluster-module budget** — `n_registers` enters the Stage 4 cluster formula, so a
  multi-register corpus is granted the room its extra voice work needs instead of being squeezed
  into a single-voice allowance. It is written by Pass A0, not guessed here.

## Handoff to Stage 2

Stage 2 reads `clusters/` + `coverage_map.json`, runs **Pass A0 register discovery first** (writing
`registers.json` and `n_registers`), and writes `extractions.json`. Every candidate element carries:
a class-prefixed `id`, its `type` (expression / modulation / projectible regularity / cost-refusal /
interactional move / preoccupation / **procedure** / **verdict**), the `clusters` it appears in, its
`register_family` where the element is family-specific, 1–3 short **example passages** (for evidence,
not for verbatim reproduction in the core), and any measured metrics from `style_metrics.py`. That
evidence is what Stage 3 scores and what Stage 5 tests against, so capture it faithfully now.
