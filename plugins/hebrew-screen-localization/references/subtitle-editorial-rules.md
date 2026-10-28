# Subtitle editorial rules

Apply after dialogue/text selection and source-faithful Hebrew localization. Use `hebrew-standards.md`, `subtitle-synchronization.md` and `quality-gates.md`; preserve scoped user decisions. Rules requiring a capability must be carried out through available tools or manual inspection, not reported as newly implemented tools.

## Declare a delivery profile

Record target format/player, maximum lines and line length, reading-speed target/warning, duration/gap limits, counting method, speaker/continuation punctuation, supported styling/positioning and permitted exceptions. Use a verified target specification when supplied; otherwise retain the existing Hebrew defaults in `hebrew-standards.md` (two lines, 42-character benchmark and ordinary adult 20-CPS warning). These are defaults, not universal benchmarks for every platform, age group or subtitle type.

Define whether counts use code points, graphemes or the target's stated method, and how spaces, punctuation and combining marks count. Do not count styling tags or invisible direction controls as visible reading text; retain any separate target-mandated count. Reading-speed success does not establish synchronization.

## Speakers, punctuation and condensation

- Preserve speaker IDs and source-word mappings through every split, merge and condensation. In a shared cue, use a separate line for each speaker and the profile's marker; the ordinary default is a leading `- ` on each speaker's line, stored in logical text order and verified in RTL. Do not put two speakers on one line to meet length limits. Split by the actual turns when two readable lines cannot accommodate them.
- Do not add a speaker marker to every continuation of one person's speech, insert identifying labels into standard subtitles without a source/specification reason, or leave an earlier speaker's answer across a new turn without a justified timing decision. SDH attribution follows its accessibility profile.
- Distinguish interruption, hesitation, trailing off and ordinary continuation. Store `interrupted`, `hesitates`, `trails_off` or `continues` when the distinction matters; use the profile's punctuation. Do not add ellipses merely because a sentence crosses cues, complete interrupted speech, or apply a fixed dictionary/punctuation replacement to every pause. Retain meaningful repetitions and false starts; condense only source redundancy whose removal preserves intent and voice.
- After any shortening, recheck negation, condition, uncertainty, actor, tense, number, mistake, register and communicative act against the source. A formal written quotation must not make all surrounding speech formal, and a character's ordinary slang must not rewrite the quotation's style.

## Break by syntax and revelation

Keep tightly bound Hebrew units together where feasible: negation and its governed verb (`לא אוכל`), construct phrases (`בית המשפט`), full names (`קרלה דובאל`) and quantities with units (`8 מיליון דולר`). Prefer a clear syntactic boundary to equal line lengths. If a unit cannot fit, try a faithful condensation or different cue division; do not treat an example as an absolute rule that overrides meaning or the target profile.

For a cue split, identify the spoken/visible point at which a condition, name, answer or punchline becomes available. Character counts do not determine that time. Re-map and verify both pieces under the synchronization or visual-boundary rules as applicable.

## Reading windows and simultaneous information

Represent speech and written text separately in the work ledger even if one export cue combines them. Assess all selected text the viewer must read in the same window, including relevant original writing, rather than evaluating each cue alone. Redundancy and disclosure decisions use `written-text-and-character-response.md`.

For plain SRT, resolve simultaneous essentials through a readable combined event within the line limit or a source-supported sequence. Do not rely on overlapping SRT cues to guarantee two stable regions. Positionable formats may use distinct stable regions only when the target supports them and the actual output is checked. Preserve essential meaning; flag an unresolved collision instead of deleting information silently.

The readable interval is the default written-cue window. A persistent sign is not permission for an indefinitely long cue, repeated unnecessary cues, or exceeding the profile's maximum duration. A very brief reveal is not permission to anticipate the text, invent completion or show a later stage early.

Any permitted readability tail, short-event exception or other profile exception must record cue ID, source readable bounds, adjusted bounds, reason, target permission and exact-output review. Verify that it does not change disclosure order, conflict with new dialogue/reactions or misrepresent changing/deleted text. Reactions do not automatically end or extend readability. Try faithful condensation or staged presentation first; an unresolved essential event remains a flagged limitation, not a waived gate.

## Logical RTL and format limits

Store Hebrew in logical Unicode order; never reverse strings by hand. Test actual exported cues containing Latin names, times, amounts, parentheses, mixed scripts and two-speaker markers. Choose direction controls, tags, fonts and positioning only according to format/player support and verified rendering; no universal control character fixes every renderer. For TTML/IMSC use the required directionality metadata. Styled formats also require width/overflow checks in the chosen font.

SRT cannot guarantee fonts, regions, lower-bar placement or consistent styling. WebVTT, TTML/IMSC or ASS features require an implemented exporter and verified target support; mentioning a format does not establish availability. Follow an authorized no-reencoding request through sidecars or a suitable subtitle-track mux; do not convert formatting work into video burn-in without authorization.

Record structural, readability, speaker, semantic, RTL, speech-synchronization and visual-text checks separately. Recheck affected source/context and the exact export after an edit, and pass it to actual continuous full-watch QC; scripts, renders or samples alone do not pass that gate.
