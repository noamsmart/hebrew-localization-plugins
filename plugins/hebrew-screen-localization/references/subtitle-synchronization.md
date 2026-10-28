# Subtitle synchronization

This is a required alignment and verification stage for translated subtitles, including repairs of existing tracks. A subtitle file that parses, has no overlaps, or passes reading-speed checks has not thereby passed synchronization.

Apply word/speech alignment requirements to dialogue cues. For written-text-only cues, follow `../skills/dialogue-selection/SKILL.md` and `../skills/subtitle-authoring/SKILL.md`: verify first/last readable source frames, disclosure order and the exact final visual cue window. Record these visual boundaries separately in the timing report; never fabricate a speech association for a silent card. A mixed track must pass both kinds of applicable timing evidence.

## 1. Establish one time reference

Record the exact source asset, runtime, frame rate/time base, audio/video stream start times and presentation timestamps, the extraction command and selected audio track, and the relationship between extracted-audio zero and original-media zero. Distinguish a source track's metadata start time from an empirically observed audio/video delay; do not add both by habit.

Keep a transformation ledger from raw ASR/alignment timestamps to source-media time and exported/playback time. Record every constant offset, scale factor, trim, edit, frame-rate conversion, resample and mux timestamp change, with units, sign, input/output time domains and reason. Apply each conversion exactly once. Preserve raw times and store corrections separately. Re-importing already shifted subtitles must not apply the shift again.

## 2. Align the actual speech throughout the runtime

Use corrected source-language words and local word/phrase alignment to the selected source audio. Forced alignment is preferred where available; calibrated word timestamps plus speech activity and direct listening may provide the same evidence when reliable. VAD only shows likely speech activity and cannot identify which words or speaker a translated cue belongs to. ASR segment boundaries, decoder tokens and confidence values are candidates to verify, not ground truth.

For every dialogue cue, map the Hebrew meaning to its exact contiguous source word or phrase range. Find the first and last audible speech belonging to that cue, including interruptions, short utterances, overlaps and intentional pauses. Use local speech/word evidence to place both cue edges. Retain the word/phrase mapping and evidence confidence. Recheck low-confidence boundaries, music/crowd noise, silence-associated ASR segments, foreign-language inserts, very short fragments, speaker changes and manually merged/split events directly against picture and sound.

Cover every translated speech event from opening to ending across every processed chunk. Start/middle/end anchors are useful diagnostics, not substitutes for per-cue coverage. Check both sides of every extraction/chunk boundary, edit, recap, long silence, language change and inserted or restored line. Never attach a cue to the nearest unrelated speech region merely to reduce its timing error.

Keep text close to its associated speech. Do not show an entire sentence during silence before it begins, leave the previous line over the next speaker, or reveal a name, punchline or outcome before it is spoken. Where a line contains a deliberate pause, choose an audio-supported split instead of spreading text proportionally over the segment. Merged cues need a new local alignment; the union of their original ASR times is not a sync check.

## 3. Diagnose the timing error before changing it

Measure signed onset error as cue-in minus the first audible source word belonging to the cue; negative is early and positive is late. Measure cue-out minus the last audible word separately. Record any intentional reading tail or shot-change adjustment so it does not hide an unexplained delay.

- Constant shift: comparable measured early/late error at well-separated anchors and local checks throughout the program. A single offset is appropriate only when the evidence supports it.
- Drift: the error grows or shrinks with runtime. Check source-version mismatch, time-base/frame-rate conversion, extraction/edit changes and playback/mux transformations before using a verified affine or piecewise correction.
- Local errors: variable magnitude or alternating early/late behavior between cues, bad ASR segmentation, missing words, chunk joins or wrong speech association. Repair those cue boundaries locally; another global shift cannot fix them.

Measure after repair. Do not assume an offset that improves one scene fixes the rest. If the user reports some cues early and others late, treat synchronization as unresolved until the mixed local errors have been investigated and corrected.

## 4. Keep timing and readability distinct

Set onset/offset tolerances from the delivery profile and record them in the report. Without a supplied tolerance, use an internal review trigger of more than two source-video frames at cue-in or more than four frames at cue-out after any explicitly documented reading tail. These are review triggers, not claimed platform requirements or permission to automatically shift text.

CPS, line lengths, minimum/maximum duration and overlap rules remain required. Meet them by natural condensation, accurate speech-boundary splits/merges and justified reading tails, then recheck sync. Do not satisfy them by moving a cue into unrelated silence, blindly clipping a long ASR segment to its first or last seven seconds, truncating spoken content, or dividing time in proportion to character count. No-overlap and acceptable CPS must never be reported as proof of speech synchronization.

## 5. Verify the final playback artifact

Check the corrected subtitle timing against the original source media and against the exact final deliverable in its target player. For muxed media, verify the remuxed artifact's stream starts/time base and actual playback; a successful mux or preserved codec alone does not prove the subtitle clock matches. Check for accidental repeated offsets or playback delays. For sidecar delivery, verify the sidecar loaded against the source without a hidden player offset.

Compare beginning, middle, ending and all repaired regions in both original and final playback, then perform the actual continuous full-watch pass required by full-watch-qc. Recheck both early and late appearance, exits, speaker changes, silence, shot boundaries and revelation timing. Recheck every repaired region with surrounding context.

Synchronization PASS requires complete per-speech-cue alignment coverage, verified visual boundaries for written-text-only cues, no unresolved early/late or wrong-speech associations, and verification of the exact delivered version. FULL-WATCH PASS additionally requires real continuous beginning-to-end playback; automated alignment, screenshots and spot checks cannot satisfy it. If tools or access cannot support a check, mark the relevant gate PARTIAL or NOT VERIFIED and identify the unreviewed time ranges. Never label that result final, fully synchronized or full-watch checked.

## 6. Required timing report

Save a timing report with the exported track and link it in the delivery QC summary. Record:

- Source, extracted audio, subtitle and final media identifiers, versions/hashes where available; runtime, frame rate/time base and stream starts.
- Selected audio track, extraction details, all timestamp-domain transformations and where each was applied once.
- Cue type, alignment method/tool/model and version, source text basis, per-speech-cue source word/phrase association, confidence, and coverage counts/time ranges; for written-text-only cues, first/last readable source frames and verified visual cue windows.
- Chosen tolerances and documented reading-tail/shot-change exceptions; signed before/after onset and offset errors, early/late counts and maximum residual errors. Mark measurements unavailable instead of inventing them.
- Constant-shift, drift and local-error diagnosis, repaired cue IDs/timecodes, old/new times, evidence and reason; retained uncertainty and unresolved ranges.
- Original-source and final-artifact/player checks, including chunk joins and repaired regions; any player offset.
- Separate statuses for structural/readability checks, speech synchronization, original/final playback verification and actual continuous full-watch QC. Record reviewer/method and reviewed ranges.

A report must make an unverified or partial check visible even when all numeric file checks pass.
