---
name: continuity-bible
description: Build and maintain a Hebrew series localization bible for names, terminology, relationships, recurring jokes, titles, spelling, transliteration and character voice. Use for episodic work, franchises, or any project where consistency across scenes or episodes matters.
---

# Continuity bible

Create a living project glossary, not a flat word list.

Track source term, approved Hebrew form, transliteration/spelling, context, first occurrence, character/organization, alternatives rejected and rationale when useful.

## Names and titles as identities

Follow `../../references/names-and-titles.md`. For each programme, work, brand or other named entity, record its referent/type, source name and genuine aliases/abbreviations, approved Hebrew form, decision basis (user approval, verified established usage, or transliteration), compatible contexts, and rejected literal renderings. Do not label a user-approved spelling as an official name without evidence. Distinguish similarly worded titles, spin-offs and ordinary descriptive uses; translate a subtitle or suffix only according to the decision for that full title.

The user-approved programme-name example is `Britain's Got Talent` → `בריטניה גוט טאלנט`; `לבריטניה יש כישרון` is rejected when it identifies that programme. Apply the same choice to `BGT` only when context confirms the same referent, and do not apply it to an ordinary claim about talent in Britain. On a correction, inspect all affected speech and selected screen-text occurrences, retain their IDs/timecodes, and flag existing exported or burned deliverables that still contain the old form; do not silently rewrite or claim to repair an already encoded video.

Include character voice notes: formality, slang level, recurring expressions, how characters address one another, honorifics/ranks and taboo/profanity intensity.

Record recurring jokes and callbacks so later translations preserve the connection.

Before translating a new episode, load the existing bible and prior approved decisions. If a new scene proves an earlier choice wrong, update the bible and flag all affected prior occurrences for review.

Never force consistency when the source intentionally changes terminology; document the intentional change.

## User corrections and their scope

Record each user correction with source/context, the approved form, rationale or evidence, and scope: an explicitly confirmed personal preference, a series/project decision, or a local contextual choice. Apply it only within that scope and compatible contexts; do not turn a one-line correction into a universal rule. Ask about scope only when it materially changes future work. Explicit new user instructions take precedence over stored preferences.

Store project decisions in the existing bible. Save confirmed cross-project preferences through an available persistent preference store and state accurately what was saved; if none is available, retain them in the project record without claiming universal future recall. Load relevant saved decisions before later work. When a correction exposes an error, review affected prior occurrences, update the bible, and recheck changed passages rather than applying a blind global replacement.

## Persistent character and relationship records

Use `../../references/character-voice-and-address.md` for evidence-bearing voice cards, relationships/forms of address and scene-specific registers. Keep ordinary voice, quoted/written style and intentional deviations distinct. Link recurring wording and meaningful user corrections to affected cue/event IDs instead of replacing strings globally.

Persist these records in the explicit local job through `save_checkpoint` and carry the approved bible into later episode jobs. `get_job_state` detects recorded source changes; it does not establish universal future recall. Preserve source/media/version references, unknown identities, audience-disclosure constraints and unresolved evidence. Reopen affected cues after a correction or new revelation.

## Material contextual adaptations

Use `../../references/slang-and-free-translation.md` for material or recurring slang, idiom, pragmatic-sense and wordplay decisions. Reuse the existing record: source/context evidence, preserved act, approved Hebrew, linked dialogue/visual/reaction IDs, scope and unresolved questions. Keep exact user-approved wording where requested. The principle of contextual adaptation applies across jobs, while a specific sense or exact line remains scoped to compatible situations; do not build an unconditional phrase-replacement dictionary.
