---
name: dialogue-selection
description: Decide whether each audible speech event in a film or episode should receive Hebrew translation. Use after transcription and before subtitle or dubbing authoring, especially for background chatter, overlapping voices, TV/radio speech, crowd voices, announcements, songs, or ambiguous off-screen dialogue. Also use for narrative cards, messages, documents, signs and other on-screen text.
---

# Dialogue selection

Treat translation presence as an editorial decision, not an automatic consequence of speech detection.

For every audible speech event, assign one of these working states:
- TRANSLATE: the viewer is expected to understand it and it contributes meaning, characterization, humor, action, atmosphere with narrative purpose, or a later reaction.
- OMIT: incidental or decorative speech that the viewer is not expected to parse, including indistinct crowd chatter, nonessential overlapping voices, accidental pickup, repeated babble, and background conversation with no narrative function.
- REVIEW-IN-CONTEXT: intelligible speech whose importance cannot be decided from audio/text alone. Inspect the surrounding scene, camera attention, character reaction, edit, mix prominence, and later payoff before deciding.

Use these evidence signals when deciding:
1. Narrative relevance: does the line change what the viewer knows, expects, feels, or understands?
2. Directorial attention: is the speaker framed, foregrounded, isolated in the mix, or otherwise intentionally presented?
3. Character response: does another character hear, react to, answer, or act because of it?
4. Plot payoff: is the line referenced later or needed to understand subsequent action?
5. Intelligibility and prominence: is the source audience realistically expected to understand it without extraordinary effort?
6. Redundancy: is the same information already conveyed clearly by foreground dialogue or image?

Do not subtitle silence simply because the ASR produced text. Do not subtitle a voice merely because it is technically intelligible.

When languages switch, assess the audience's intended comprehension separately from each character's comprehension. Translate relevant speech meant for the audience even when a character cannot understand it; preserve deliberate opacity when the audience is not meant to understand. Record plot-relevant language barriers and partial understanding so localization can preserve the resulting misunderstanding.

For standard interlingual subtitles, omit nonessential background voices by default. For SDH/CC, use the target accessibility specification instead; meaningful speech and sound cues may need inclusion even when ordinary subtitles would omit them.

For dubbing, meaningful background dialogue that the audience is intended to understand must be adapted into Hebrew or recreated appropriately. Incidental source-language chatter should not remain distractingly intelligible in the final mix. Never leave clearly intelligible original-language dialogue underneath the Hebrew dub unless the creative specification explicitly requires it.

Record the decision and reason for any borderline event so full-watch QC can re-evaluate it in scene context.

## On-screen text selection

Inspect visible writing separately from speech; do not rely on ASR or an existing subtitle track to detect it. Assign TRANSLATE, OMIT or REVIEW-IN-CONTEXT to meaningful visual text events and record the decision with its reason, exact visible wording where readable, readable source interval and relevant scene context.

Translate narrative time, place and event cards, plus written information needed to understand action, relationships, clues or jokes, even when nobody reads it aloud. For example, "30 MINUTES LATER" becomes "כעבור 30 דקות". Translate the relevant content of messages, documents, headlines, signs and interfaces rather than mechanically transcribing every visible word.

Omit incidental decoration, unrelated logos, ordinary production credits and interface clutter by default, unless they convey a narrative meaning or the user/target specification requires them. Dedications, explanatory cards and plot-relevant credits are not automatically incidental. Do not duplicate already readable Hebrew. Omit an additional text cue as redundant only if dialogue or existing Hebrew subtitles convey the same relevant information at the right moment without losing a clue, ambiguity, joke or disclosure order. Existing burned-in text in another language does not replace needed Hebrew translation.

Inspect uncertain text at suitable resolution and with the surrounding scene. Keep unresolved meaningful writing in REVIEW-IN-CONTEXT; never invent illegible words, infer a whole document from a fragment or omit an essential card because the audio is silent. Distinguish the written message from any character's spoken misreading or mistaken interpretation.

## Linked written events and responses

Apply `../../references/written-text-and-character-response.md` and `../written-text-context/SKILL.md` when speech refers to, reads, misreads or responds to writing. Record both source wording and actual speech, staged reveals, character/audience knowledge and the reason for duplication or omission. A reaction does not replace essential written information or prove that the character understood it. OCR candidates require frame/context verification; do not invent clipped words or future message stages.
