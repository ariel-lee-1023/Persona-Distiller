# Situated evidence and conditional authoring

Retain each useful observation before turning it into an instruction. Standard builds
use `transworld-identity/evidence.json`, with schema version 1 and a `records` array.
The [evidence schema](schemas/evidence.schema.json) specifies the fields.

Each record has a stable ID, source identity, locator, attribution and episode/source
group ID; situation, audience, available information and constraints; an observed
statement, action or choice; conditions, exceptions and conflicting evidence IDs;
claim type (`observed_event`, `recurring_pattern`, `editorial_synthesis`, or
`new_application`); runtime instruction links and a curation decision with its reason.
Use an empty exceptions/conflicts array only when none were found in the inspected
material. It does not assert that none exist. Keep useful short excerpts or faithful
summaries and distinguish subject speech from a translator/editor's wording.

Procedures include triggers, ordered steps, preconditions and what happens on failure.
Costly refusals include the convenient alternative, incentives, stakes and actual choice.
Verdicts include the object, date, information then available and applicability conditions.
Interaction includes what prompted a concession, challenge, joke, silence or reframing.
Variation records audience, period and circumstances, with supported alternatives.
Preoccupations need diagnostic content beyond a universally desirable virtue.

Resolve apparent conflicts by checking changes in evidence, period, audience, domain
and constraints. If unresolved, preserve both observations, record the uncertainty,
and weaken the instruction. Never resolve source conflict by class priority or ID order.
An observed episode can be retained without being elevated into a recurring rule.
Repeated tellings of that episode count as one support group.

For an upgrade classify claims as preserve, contextualize, correct/remove, or unresolved.
Add content only to fill a concrete gap, using accessible supplied records first. Search
or OCR only the needed passages within the source budget, then update the smallest
module. An old summary is not newly checked primary evidence. Missing evaluation
neither establishes a bad persona nor warrants a full rebuild.

The detailed extraction catalogue in [extraction.md](extraction.md) remains useful for
what to notice. Its measured register discovery and transfer/discrimination admission
steps apply only when separately commissioned as research. Standard extraction does
not require test metrics before retaining source-supported conditional guidance.
