---
name: transcript-and-speakers
description: Produce or repair a time-aligned source transcript with speaker attribution and audiovisual context for professional Hebrew localization. Use when dialogue must be transcribed, speakers identified, background speech classified, or ambiguous ASR corrected.
---

# Transcript and speakers

Generate the strongest possible source-language transcript before translation.

1. Use timestamped ASR when available, then verify low-confidence or semantically suspicious segments against the audio/video.
2. Assign stable speaker IDs. Prefer character names only when the narrative has established them; avoid spoilers from prematurely naming unknown speakers.
3. Record scene context that changes translation: visible addressee, gender cues, gestures, sarcasm, written text, interruptions, phone/radio/TV speech and off-screen speech.
4. Distinguish foreground dialogue, intentionally intelligible background speech, incidental chatter, songs and non-speech sounds.
5. Do not send every ASR segment directly to translation. Route audible speech through `dialogue-selection` and preserve its TRANSLATE, OMIT, or REVIEW-IN-CONTEXT decision.
6. For normal translated subtitles, do not clutter the file with unintelligible or irrelevant ambience. Include background speech only when viewers are meant to understand it or it matters to the story.
7. For SDH, preserve meaningful audible information according to the target specification.
8. Keep uncertainty markers in the working transcript until resolved. Never silently turn a guess into a fact.
9. Preserve raw ASR timestamps and their time domain. Produce corrected source word/phrase boundaries for local alignment across every translated event using `../../references/subtitle-synchronization.md`; segment bounds alone are provisional and VAD cannot identify the correct words or speaker. Flag uncertain timing and silence-associated segments instead of passing them downstream as verified sync.

Output time-coded transcript segments with speaker, confidence/uncertainty notes, speech-role classification, translation-selection state, and contextual annotations needed by the translator.
