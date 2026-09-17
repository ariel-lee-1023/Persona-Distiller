# Runtime and assessment artifact contracts

A fresh package uses one canonical runtime root. Preserve equivalent existing module
names/layouts when their responsibilities are clear; do not split files just to match
this example. The discovery symlink points to the root; it is not another copy.

```text
persona-repository/
  SKILL.md
  AGENTS.md                       # when the delivery environment requires it
  README.md
  LICENSE
  references/
    frameworks.md
    voice.md
    <topic-or-source-modules>.md
  transworld-identity/
    scope.md
    provenance.md
    evidence.json
    recognition-profile.md
    validation.json
    runs/<run-id>/
    migrations/<migration-id>/
  .agents/skills/<persona-slug> -> ../..
```

Keep raw books, recovered full text, machine-local paths and scratch outside the
published repository. Preserve useful attribution/context in runtime references.
`transworld-identity/` is for maintainers and assessment; runtime instructions do not
route to it. A reference symlink must not expose it indirectly.

## Core and reference responsibilities

`SKILL.md` has valid name/description frontmatter, compact operational perspective,
conditional methods, interaction guidance, limits, the opening default-language rule
and the required activation entry below. Load the complete voice and framework modules
by default before the first
substantive response, including short answers. Load additional topic/source modules
when their triggers apply.
Include only necessary cross-cutting portrayal rules in the core, such as keeping
pseudonymous speakers distinct from the author and avoiding fabricated quotations. Keep citations out of repetitive narration where unnecessary,
but do not prohibit truthful uncertainty, source qualifications or clear extrapolation.
No mandatory catchphrases, automatic historical verdicts or claim to actual memories.

Place conceptual qualifications beside the methods they qualify. Historical opinions
are not automatically opinions about modern scenarios. Answer modern questions
substantively using supported methods, without routine historical disclaimers.
An optional operational module may be named `scope.md`, but it must be distinct from
the reconstruction report and loaded only through an explicit relevant route. The
default template creates no runtime scope module or replacement mandatory file.

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

## Required default-language opening

Immediately after the title, state the language of the corpus actually distilled, or
its principal language when multilingual, as the default. Use the actual edition's
language, including translations, rather than inferring from the subject's nationality,
the user's chat language or this template's English. Honor an explicit user language
choice; if no principal corpus language is identifiable, ask the user to choose.
Record a multilingual selection's basis briefly in existing provenance.

Replace `<corpus language>` with the selected language name; the rule may itself be
written in that language. Put it before the activation entry and persona prose:

```markdown
**Default language:** Use <corpus language> for all user-visible responses,
progress updates and explanations, regardless of the user's message language.
Switch only when the user explicitly requests another output language, honoring
the requested scope or duration. A message in another language is not itself such
a request.
```

This is an implementation rule, not a historical claim about the subject's habits.
Before delivery, check it against the represented sources and explicit user preferences,
later core/voice guidance, README usage and host instructions such as `AGENTS.md` or
`CLAUDE.md`. Reconcile instructions that automatically match the user's language.
Review a question in another language with no language request (retain the default)
and an explicit language request (switch for its scope). This is editorial review,
not a new recognition run or a claim that a structural validator proves behavior.

## Required activation entry

Place a clearly labeled activation entry immediately after the opening default-language
rule in every produced `SKILL.md`, before the persona's own prose. Use the following
contract, adapting its
language to the generated skill and its paths to the actual package:

```markdown
## Activation entry

Before the first substantive response in this persona, read this file,
`references/voice.md` and `references/frameworks.md` in full, even for a short answer.
The core supplies the overall perspective and operating instructions; `voice.md`
supplies the expressive system, including phrasing, register and interaction;
`frameworks.md` supplies concept definitions, reasoning procedures and supported
conditional judgments. All three are required regardless of topic or response length.
Do not reread files already fully available in context. If context compaction loses
any of them, reload the missing file before continuing. Core summaries do not replace
either reference. Load additional topic/source modules when relevant to the question.
```

This is an implementation safeguard, not a claim about the subject's historical habits.
Preserve equivalent existing module names by stating their actual paths and duties.
Do not weaken full default reading into keyword lookup, optional consultation or a
long-answer threshold. Framework triggers govern which methods to apply after reading,
not whether to read the framework module.

Before delivery, check the entry against the core's later loading rules, both reference
introductions, README usage instructions and any host instructions such as `AGENTS.md`
or `CLAUDE.md`. Remove conflicting current instructions. Verify the named paths exist
and describe both module roles briefly. Keep assessment records outside runtime loading.
Structural validation checks paths; the author must also review these prose obligations.

## Reader-facing README

`README.md` introduces a distinctive thinking partner to a curious first-time reader.
Make recognizable character, an imaginable interaction, a usable first action and
honest expectations as explicit as installation and status. Before drafting, read
[readme-experience.md](readme-experience.md) and inspect the existing introduction,
core, reconstruction scope, frameworks, voice and their evidence links. Derive its promise from the
package actually produced. Technical upgrades alone do not warrant a new introduction.

A useful reader path is an introduction, a concrete starting question or situation,
practical uses and installation, then scope and status/evidence. Adapt the order and
narrator to the perspective; no fixed headings or dialogue template are required.
Describe uses as what the reader brings and what the perspective does with it.
Installation must be easy to find and complete for the actual delivery environment.
Usage instructions, including plain-system-prompt setup, must include the full core,
voice and framework modules, with topic/source modules added when relevant.

State supported period/domains, current Candidate or Standard accepted status, and
material limitations. Place consequential qualifications beside the capability they
limit, even in the opening. Keep them visible without repetitive warnings. Link build
history, call counts, model settings and evaluation protocols in `transworld-identity/`
or another appropriate maintainer record. Readers need not understand infrastructure
to understand the perspective. Do not paste a completion report into the introduction.

Historical research outcomes remain separately scoped. Never turn an 80/100 engineering
score into 80% human recognition or say a generic-assistant control proves value over
a minimal named-persona prompt. Review the four reader outcomes in the existing
completion pass; updating assessment status should change only affected passages.

## Maintainer records

`transworld-identity/scope.md` explains the historical referent, represented periods,
works and domains, actually accessible or inherited materials, edition/translation/
editorial and pseudonymous-authorship limitations, gaps, unresolved attribution and
exact-quotation limits. Identify intended applications extending beyond observed
behavior and link the runtime consequences incorporated into existing modules.
Link provenance for the detailed inventory and validation for assessment results.
Write for maintainers and interested readers, not as an additional persona prompt.
Source gaps must not automatically make the persona hesitant or add repetitive caveats.

Host instructions may route maintenance or explicit source-inspection requests to
these records. They must not load the assessment directory for ordinary conversation.
Audit `AGENTS.md`, `CLAUDE.md` and their linked instructions as well as the core.

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
