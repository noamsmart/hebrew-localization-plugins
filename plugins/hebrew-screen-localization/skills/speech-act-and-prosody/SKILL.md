---
name: speech-act-and-prosody
description: Mandatory contextual review of question versus statement, genuine versus rhetorical questions, implied requests, sarcasm, tone of voice, emphasis, interruptions and conversational intent in Hebrew localization of film, TV, subtitles, dialogue, or meaningful on-screen messages.
---

# Speech act and performed-tone review

Use for **every** Hebrew dialogue localization or QC project, including revisions of an existing subtitle track. Read `../../references/speech-act-and-prosody.md` and apply it to selected dialogue and meaningful written exchanges. This is an editorial/audiovisual process, not an automatic guarantee that an audio classifier exists.

1. Establish reliable source words, speaker and addressee. When dialogue is disputed, review actual audio/video if available; never trust punctuation from speech recognition alone.
2. Use the complete exchange and context. Independently determine the line's **grammatical form**, **communicative act** (genuine query, confirmation, rhetorical question, indirect request, accusation, threat, joke, evasion, etc.) and **performed manner** (sincere, sarcastic, surprised, fearful, hesitant, angry, deadpan, whispered, etc.). Consider rhythm, stress, pitch, pauses, gesture, responses and speaker relationships, with uncertainty recorded.
3. Distinguish a question from a statement and a statement functioning as a question. Preserve the original speech act even when source ASR/subtitle punctuation suggests otherwise. Do not force rising intonation into a literal question or infer irony solely from a short transcript.
4. Render natural Hebrew punctuation, wording, modality, register and forms of address. Keep the tone's emotional strength without inventing motives, profanity or intimacy. Preserve questions and responses across cue boundaries and do not reveal punchlines or plot facts early.
5. For meaningful written questions, use visible text and sender/reader/reaction, not nonexistent spoken prosody. Keep quoted, misread and staged words separate. Preserve intentional ambiguity and the audience's knowledge at each point.
6. When a materially ambiguous act has insufficient audio/visual evidence, flag the cue/timecode for review with two plausible interpretations. Do not claim a confident tone determination or full QC from a transcript-only pass.
7. Perform a separate scene-by-scene question/statement/tone pass after Hebrew drafting and after substantive shortening. Recheck linked setup, answer, reaction and the actual rendered subtitles. Save evidence and `PRAGMATICS_PASS` or `PARTIAL / UNVERIFIED_AUDIO` independently of other gates.

Contrast-check at least genuine and rhetorical questions; non-question declaratives with/without questioning delivery; polite indirect requests versus literal ability questions; sincere versus sarcastic positive words; false starts, interruptions, quote boundaries, teasing and character-specific register. The examples in the reference are **not** fixed phrase mappings.

Route naturalness/source fidelity to `../hebrew-dialogue-localization/SKILL.md`, speaker and gender decisions to `../character-voice-review/SKILL.md`, text/reaction scenes to `../written-text-context/SKILL.md`, subtitle punctuation/timing to `../subtitle-authoring/SKILL.md`, and final continuous playback to `../full-watch-qc/SKILL.md`. Follow the job's approved context-scoped user choices and existing quality gates. Never invent having inspected audio, watched an entire episode or used a tool that is unavailable.
