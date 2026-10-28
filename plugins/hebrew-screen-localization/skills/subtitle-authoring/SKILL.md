---
name: subtitle-authoring
description: Turn a Hebrew localization into professionally timed RTL subtitles. Use for SRT, WebVTT, TTML/IMSC, forced narratives, reading-speed optimization, line breaking, overlap checks, subtitle-presence decisions, and subtitle timing polish.
---

# Subtitle authoring

Use platform-specific specifications when supplied; otherwise use `../../references/hebrew-standards.md` as the baseline.

Only author subtitle events for dialogue and on-screen text that passed `dialogue-selection` as TRANSLATE. Apply its separate on-screen text selection rules to forced narratives and other written events. Resolve REVIEW-IN-CONTEXT items before final delivery. OMIT events must not generate subtitles.

A good subtitle track also knows when to remain silent. Do not create subtitle events for incidental chatter, indistinct crowd voices, decorative background conversation, accidental pickup, or nonessential overlapping voices in standard interlingual subtitles. Do not fill gaps just to maintain subtitle density.

Time speech subtitles to speech and visual edit. Start speech cues close to the first audible frame unless a shot-change rule justifies adjustment. Avoid displaying punchlines or revelations before the source delivers them.

Before accepting speech-cue timing, complete the mandatory local speech/word alignment across the entire runtime in `../../references/subtitle-synchronization.md`. Map each speech cue's meaning to its exact spoken words, verify both audible edges, distinguish constant shift from drift and local errors, and apply each time-reference correction only once. ASR segment boundaries are provisional; no-overlap/CPS checks do not establish synchronization. Re-align manually split/merged cues and inspect low-confidence or silence-associated timestamps. Save the timing report, and verify both the original-media and final playback versions before a synchronization PASS.

Default constraints for professional Hebrew: maximum two lines and a 42-character-per-line benchmark. Treat reading speed as a measurable QA dimension, not a vague impression. When text is too dense, first rewrite more economically while preserving intent.

After shortening or adapting a cue, repeat the semantic gate in `../../references/quality-gates.md` against its source words and scene. Do not meet reading limits by dropping negation, a condition, uncertainty, an actor or a plot-relevant mistake. Recheck any split or merge for early disclosure of information.

Break lines at natural Hebrew syntactic boundaries. Keep strongly bound grammatical units together. Prefer an easily scanned shape over mechanical line balancing.

Handle two speakers unambiguously. Keep forced on-screen text separate from dialogue when the target specification requires it.

Time written-text-only cues to the first and last readable source frames, including fades and adjacent cuts; do not assign ASR/VAD or spoken-word boundaries to silent title cards. Preserve the original moment of revelation and punchlines. Start no earlier than the source becomes readable and use that readable interval as the default cue window; document and recheck any specification-approved readability adjustment that preserves disclosure order. Check cumulative reading load when text and dialogue appear together. Use a stable, specification-compatible position that avoids essential original text, faces and action. When preparing video-embedded or positionable subtitles, detect the active-picture bounds and any lower horizontal letterbox bar. If the bar can hold the full styled subtitle and safe clearance, place the Hebrew subtitle entirely inside it, just below the active picture boundary, never over the film image; keep placement stable and preserve timing. If no usable lower bar exists, use the bottom safe area of the active picture. A sidecar format with no position control cannot guarantee this placement. If simultaneous essential information cannot fit, resolve its presentation or flag it for review instead of silently dropping it.

Validate RTL behavior in the actual output format/player. For TTML/IMSC, set directionality explicitly as required by the target profile.

After timing, run automated checks for overlaps, negative/zero duration, illegal ordering, excessive line count, excessive line length, extreme CPS, suspiciously short events, and suspicious subtitle events attached to segments marked OMIT. Then send to `full-watch-qc`.

## Editorial rules and tools

Apply `../../references/subtitle-editorial-rules.md` for speaker markers, interruption/hesitation/continuation, syntax-led breaks, cumulative reading load, disclosure order and logical RTL. Use the actual declared profile/count method; invisible direction controls and styling do not count as visible reading text. Do not enforce a single character-count target as a universal platform rule.

Use `inspect_subtitles` for structural/readability findings, `export_subtitles` for implemented SRT/WebVTT exports and `build_review_workspace` for local source/target editing. Export to a new explicit version, retain source IDs/word mappings in the ledger and recheck exported rendering. The packaged exporter does not implement TTML/IMSC/ASS; use a genuinely available external exporter for those formats or report the missing capability. SRT cannot promise font or letterbox placement. Editor preview, CPS and parser success cannot establish synchronization or full-watch PASS.

## Natural wording after condensation

Use `../../references/slang-and-free-translation.md` when shortening an idiom, slang phrase, flirtatious question or colloquial reply. Retain its communicative act, emotional degree, participants, referent and meaningful literal anchor; removing redundancy is not permission to change the sense. Preserve an explicitly user-approved exact formulation within its scope, including requested pronouns. Recheck connected dialogue/writing and the payoff after a shortening or line-break change. Record any genuine specification-approved readability exception rather than silently rewriting protected wording or stretching unverified clocks.
