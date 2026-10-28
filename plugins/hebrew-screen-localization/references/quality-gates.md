# Quality gates

A deliverable is not final until all applicable gates pass.

## Semantic gate
- No mistranslated plot facts, relationships, negation, tense, modality, numbers or names.
- Every selected programme/work/brand reference, in speech or screen text, identifies the correct named entity through its approved form; sentence-shaped names are not replaced by invented literal translations. Apply `names-and-titles.md`.
- Name-versus-description and deliberate title wordplay are resolved from context. Ordinary descriptive speech is not converted into a title, and unrelated titles/spin-offs are not merged. Unsupported claims of an official/established Hebrew name do not pass.
- Jokes, irony, threats, euphemisms and emotional intent survive in Hebrew.
- Ambiguous lines are checked against the scene, not guessed from text alone.

- Every condensation, adaptation and correction is checked directly against the source for negation/scope, conditions/exceptions, quantities, certainty, tense and who does what to whom; fluent phrasing or back-translation alone is not a pass.
- Identity, gender, relationships and other intentionally withheld information are not disclosed before the source; information already conveyed is not artificially hidden.
- Plot-relevant language barriers and the distinction between audience and character understanding remain intact.
- Meaningful mistakes and their corrections still support the intended joke or plot point; character claims are not rewritten to match facts learned later.
- Cultural adaptations preserve the source world's identifiable places, brands and people rather than substituting unrelated local equivalents.

## Selection gate
- Every translated speech event is one the viewer is intended to understand or needs for narrative comprehension.
- Incidental chatter, decorative voices, accidental pickup and irrelevant background speech are absent from standard interlingual subtitles.
- Plot-relevant off-screen, TV/radio, announcement or background speech is not omitted merely because it is not foreground dialogue.
- No unresolved REVIEW-IN-CONTEXT speech or meaningful on-screen text remains in the final deliverable.
- Narrative time/place/event cards and other relevant visual writing have been inspected and translated, including silent cards; incidental or redundant text is omitted only according to the on-screen text selection rules.
- Every meaningful visual-text event has a recorded selection decision and readable source interval; unreadable wording is not fabricated.
- Silence and nonessential ambience are allowed to remain untranslated; subtitle density is never a quality target by itself.

## Hebrew gate
- Hebrew sounds written for humans, not translated by a machine.
- Grammar, gender, agreement, punctuation and spelling are consistent, except for documented intentional deviations required by characterization, humor or plot.
- Character voices remain distinct.
- A naturalness pass has reviewed all selected dialogue for slang, idioms, playful nicknames and overly literal calques, rather than only the supplied example or sampled lines. Freer adaptations retain source meaning, intent, humor and register, and do not introduce unsupported information or unmotivated slang.

## Subtitle gate
- No unintended overlaps.
- Timing follows speech for dialogue cues and readable visual intervals for written-text-only cues; neither reveals punchlines or plot information early.
- Reading speed is acceptable.
- Maximum line count and line-length limits are respected for the target profile.
- Line breaks preserve syntactic units.
- RTL renders correctly in a real player or validator.
- No subtitle event exists solely because ASR detected a voice that was classified OMIT.
- Written-text-only cues use verified visual readability boundaries rather than speech alignment; disclosure order, positioning and cumulative reading load with dialogue are checked.

## Synchronization gate
- Follow `subtitle-synchronization.md` for every translated speech cue across the entire runtime, including all chunk joins and inserted/restored dialogue.
- Every speech cue is associated with the correct source words/phrase and verified local audible start/end; ASR segments, VAD proximity, no overlaps and acceptable CPS alone cannot satisfy this gate.
- Constant shift, drift and local errors are diagnosed separately. Mixed early/late cues require local repairs; every time-domain transformation is applied exactly once and documented.
- Signed early/late onset and offset errors, tolerances, intentional tails, repaired IDs and unresolved ranges are recorded in a timing report.
- The corrected track is verified against original media and the exact delivered sidecar/mux in the intended player, with no unexplained player delay or repeated offset.
- No unresolved timing errors or wrong-speech associations remain. Missing evidence or incomplete coverage is PARTIAL/NOT VERIFIED, never PASS.

## Continuity gate
- Names, places, organizations, ranks, technical terms and recurring jokes match the series bible.
- A separate identity pass covers all selected spoken and written title/name occurrences, including genuine aliases and abbreviations, against the scoped decisions; no blind source-string replacement is used.
- Deliberate changes are documented rather than silently drifting.

- User corrections have recorded scope and are applied only in compatible contexts; relevant affected prior occurrences have been reviewed.

## Full-watch gate
- The entire translated program has been watched with the finished subtitles or dubbed mix from beginning to end.
- Flash frames, late subtitles, missed signs, mismatched speakers, awkward phrasing, scene-context errors, missing necessary translation, and unnecessary background translation are corrected.
- A full-watch gate may only be marked PASS after actual continuous media review.

## Dubbing gate
- Source dialogue is not audibly competing under the Hebrew dialogue unless creatively intended.
- Clearly intelligible source-language background dialogue does not remain distractingly present; meaningful background dialogue is recreated/adapted as required by the creative brief.
- M&E or separated background audio is inspected for dialogue leakage and artifacts.
- Hebrew phrasing fits performance timing and emotional beats.

## Evidence, coverage and revision acceptance

- Maintain an audiovisually established source-event ledger: selected events map to delivered target cues, omitted events have reasons and uncertain events remain flagged. Check split/merged text across the complete output window. A source-ledger audit cannot detect source events absent from the ledger.
- Check agreement by actual speaker/addressee/referent/quoted speaker; allow evidenced character/register changes and preserve complete conversational intent. Follow `character-voice-and-address.md`.
- Check written/reading/reaction links and separate audience/reader/other-participant knowledge. Preserve misreadings, staged text and disclosure order; follow `written-text-and-character-response.md`.
- Record the separate source/context review with its reviewer, method, ranges and exact versions. Automated metadata completeness, fluent back-translation, OCR confidence and alignment scores are not semantic acceptance.
- No saved checkpoint, elapsed playback, empty review queue, numeric warning count or local tool status grants an editorial or full-watch PASS. Carry only evidence actually obtained; source/output/context changes invalidate affected gates and trigger dependent-scene rechecks.
- Keep format/profile, counting method, interruption/speaker policy and any specification-approved readability exception explicit. Check real output rendering; no universal RLM or file extension proves RTL correctness.

## Contextual slang and free-translation acceptance

- Follow `slang-and-free-translation.md` for all selected speech and meaningful writing, including ordinary ambiguous conversational phrases. The chosen sense and communicative act must fit the source exchange and available audiovisual context.
- Free wording and subtitle/dubbing condensation preserve participants, negation, conditions, quantities, certainty, emotional degree and disclosure. Naturalness cannot justify invented information, added profanity, softened intensity, or replacing a title/name with a descriptive phrase.
- Recheck written author versus reader voice, linked choices/reactions, visible props and joke setup/payoff. Preserve intentional errors and the timing of their corrections.
- Apply scoped user-approved exact wording, including requested pronouns, in the actual export. Record and inspect affected dependent turns; do not treat examples as universal replacements.
- Record uncertainty and the review method honestly. This acceptance check supplements the existing semantic, timing and full-watch gates; it cannot grant PASS through text fluency or metadata alone.
