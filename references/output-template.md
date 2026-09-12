# Runtime and assessment artifact contracts

A fresh package uses one canonical runtime root. Preserve equivalent existing module
names/layouts when their responsibilities are clear; do not split files just to match
this example. The discovery symlink points to the root; it is not another copy.

```text
persona-repository/
  SKILL.md
  AGENTS.md                       # when the delivery environment requires it
  README.md
  references/
    scope.md
    frameworks.md
    voice.md
    <topic-or-source-modules>.md
  transworld-identity/
    provenance.md
    evidence.json
    recognition-profile.md
    validation.json
    runs/<run-id>/
  .agents/skills/<persona-slug> -> ../..
```

Keep raw books, recovered full text, machine-local paths and scratch outside the
published repository. Preserve useful attribution/context in runtime references.
`transworld-identity/` is for maintainers and assessment; runtime instructions do not
route to it. A reference symlink must not expose it indirectly.

## Core and reference responsibilities

`SKILL.md` has valid name/description frontmatter, compact operational perspective,
conditional methods, interaction guidance, limits and meaningful reference-loading
triggers. Load scope with the core, relevant topic methods for their triggers and voice
before sustained prose. Keep citations out of repetitive narration where unnecessary,
but do not prohibit truthful uncertainty, source qualifications or clear extrapolation.
No mandatory catchphrases, automatic historical verdicts or claim to actual memories.

`scope.md` identifies the historical anchor, supported period/domains, fixed facts,
permitted changes, extrapolation rules and unsupported territory. Historical opinions
are not automatically opinions about modern scenarios.

`frameworks.md` gives methods with triggers, steps, conditions, failure handling,
exceptions and characteristic tradeoffs. Where useful, distinguish how evidence is
handled, causal categories, dated object-level judgments, argumentative moves and
personal-scale applications. Named constructs need literal source support; editorial
labels must remain labeled as editorial. Use `name_audit.py` when naming is uncertain.

`voice.md` retains supported expressive range. Include sentence construction,
explanation habits, humor, concrete phrasing, openings/closings, vocabulary choices,
what prompts a concession or challenge, and trigger-to-register shifts by audience,
period or stakes. Compare attested alternatives. Absence from a small corpus is not
an absolute prohibition. Measurements may describe inspected material; they are not
universal quotas or certification. Preserve useful anti-drift examples and register
nuance without requiring expensive measured family separation.

Topic/source modules retain situated evidence, examples, conditions, counterexamples
and locators. Preserve supported modules and avoid repetitive biography or raw dumps.

## Maintainer records

`provenance.md` records build contract, finite source-processing boundary and actual
coverage, source inventory, baseline/revision, lineage, editorial decisions and
limitations. Describe source review honestly, including machine assistance. It is not
an independent historical audit. Do not require a particular first heading or numerical
admission weights. Optional legacy episode files may remain when useful.

`evidence.json` has stable IDs, attribution, context, support relationships and curation
reasons. `recognition-profile.md` contains the source-backed diagnostic expectations,
acceptable variations, contradictions and scoring anchors. The frozen structured
profile is generated from the same production evidence, not copied from the persona
prompt as supposedly independent evidence.

`validation.json` records the exact assessed inputs, separate gates, calls/tokens,
interruptions, reuse lineage and current limitations. Previous reports and frozen runs
remain immutable historical evidence; changed input hashes invalidate affected claims.

`README.md` explains installation/use, supported period/domains, current Candidate or
Standard accepted status and material limitations. It may separately list historical
research outcomes. Never turn an 80/100 engineering score into 80% human recognition
or say a generic-assistant control proves value over a minimal named-persona prompt.
