---
name: full-watch-qc
description: Perform final beginning-to-end audiovisual quality control on Hebrew subtitles or a Hebrew dub. Use before delivery or when the user asks to verify an entire episode/film against picture and sound.
---

# Full-watch QC

This is a continuous playback pass, not a text review.

Watch/listen from program start to end with the finished Hebrew deliverable enabled. Check meaning, context, speaker assignment, gender, names, continuity, spelling, naturalness, subtitle timing, line breaks, reading load, shot-change behavior, on-screen text, songs when applicable and technical rendering.

Audit names and titles against `../../references/names-and-titles.md` and the continuity bible in both speech and selected screen text. Catch fluent but invented literal programme/brand names, including names shaped like sentences. Check ordinary descriptive uses and intentional wordplay separately, and log a wrong named-entity rendering as a semantic/continuity defect.

Explicitly audit subtitle presence and absence. For every scene, ask both: "Is anything important missing?" and "Is anything being translated that should have remained background?" Remove subtitles for incidental chatter, decorative voices, accidental pickup and other speech the source audience is not meant to follow. Add translation when a background/off-screen/TV/radio voice is actually necessary for story comprehension, character response, humor, or payoff.

Audit visual text independently of audio: check narrative cards, messages, documents, headlines and relevant signs, including silent scenes. Verify both needed translation and justified omission using `dialogue-selection`; check readable cue-in/cue-out, revelation order, positioning and reading load alongside dialogue. Log missed essential text, fabricated readings and unnecessary duplicate cues under WRONG-PRESENCE or the relevant semantic/timing category.

For dubbing, also inspect synchronization, performance fit, source-dialogue leakage, M&E/source-separation artifacts, music/effects continuity and level transitions. Clearly intelligible original-language foreground or background dialogue must not compete underneath the Hebrew dub unless explicitly required by the creative specification.

Log every defect with timecode, category, severity, current text/audio, proposed fix and verification status. Include a dedicated category for WRONG-PRESENCE: subtitle/dub included when it should be absent, or absent when it should be present.

Apply corrections, then recheck the corrected region with surrounding context.

During playback, verify the semantic gate against the source after all condensation and corrections: check certainty, conditions, negation, actors, disclosure order, language barriers, and meaningful mistakes with their corrections. Confirm that scoped user preferences and cultural adaptations have not changed the story or character relationships.

For subtitle synchronization, use `../../references/subtitle-synchronization.md`. During actual playback explicitly check both early and late speech-cue-in/cue-out against their spoken words throughout the program, including all chunk joins, silence/music transitions, languages and repaired regions. Verify the original source and exact final sidecar or muxed artifact; record their timing references and any player offset. A global offset or successful automated/structural checks do not establish local synchronization. Save the timing report and keep speech-alignment, final-playback and continuous full-watch statuses separate.

Only mark FULL-WATCH PASS when the entire runtime was actually reviewed. If access is partial, label the result PARTIAL QC and state exactly what was reviewed.

Use `../../references/quality-gates.md` for pass/fail criteria.

## Evidence and available playback

Use `../../references/local-tools.md`: `prepare_review_segment` returns inspectable frames/audio with time references; `play_review` opens bounded native playback with an explicit audio stream and subtitle track. Run playback only as part of an authorized review and only with an available interactive reviewer. Launch success or elapsed playback is not proof that anyone watched/listened. Inspect the actual image/audio through available sensory tools or a human reviewer and record method, ranges, findings and exact versions.

Use `build_review_queue` to order repairs, then retain the required continuous beginning-to-end review. Check entire conversations and linked written-text/read/reaction sequences, not just isolated cues. Check the exact final sidecar in its target player, including mixed-script RTL and speaker markers. Source/output edits invalidate affected review evidence. Neither an editor preview, extracted samples, alignment scores nor a saved checkpoint can grant FULL-WATCH PASS.

## Contextual idiom and free-translation audit

Apply `../../references/slang-and-free-translation.md` across the entire selected speech and meaningful written text during actual review. Check that ambiguous expressions chose the scene-supported sense; flirtation was not escalated to love, a polite refusal was not made an acceptance, and sarcasm or delighted disbelief was not turned into literal hostility. Verify writer/reader voices, scoped exact wording, visible props and linked joke setups/payoffs after all condensation. Text-only examples and fluent wording do not satisfy the audiovisual or full-watch gates.
