# Written text, reading and character response

Use with `../skills/dialogue-selection/SKILL.md`, `character-voice-and-address.md`, `subtitle-editorial-rules.md` and `quality-gates.md`. Inspect writing independently of audio. These rules prescribe records and review; they do not claim OCR, playback or reaction-analysis tools are connected.

## Linked event record

For meaningful written events, retain:

- `visual_event_id`, scene ID, exact readable source wording, selection state/reason, evidence frames and first/last readable source times.
- `stages`: significant text changes, the wording actually readable at each stage and its first readable frame. Keep uncertain or incomplete text explicit.
- Linked speech cue IDs and `relation`: exact reading, paraphrase, partial reading, misreading, quotation, reference, concealment or performed claim. Record the spoken wording separately from the written wording.
- Linked character/reaction IDs, time ranges and evidence for looking, reading, understanding, responding or acting. Appearance in the same frame does not establish understanding or causation.
- For a meaningful disclosure: what the audience can know, what the reader knows and what another participant knows at that moment, with `known`, `unknown` or `unproven` where appropriate. Record deliberate language barriers and any difference between the displayed information and a character's belief.
- Exported cue IDs, presentation/duplication decision, reading-load check and review status.

Example: text says `8pm sharp`; a later stage says `Location to follow.` Store two reveal times and do not show the second message with the first. A character reading “nine” while the displayed message says “eight” creates a `misreading` link: preserve the spoken error, and select the written information according to the audience's intended understanding. The spoken and written records must not overwrite each other.

## Operational rules

1. Inspect the scene before, during and after the writing. Separate what the audience can read from what a character sees or understands. Do not delay an already readable, selected message automatically until the character looks at it, or infer that the character knows it merely because the audience does.
2. Preserve pointing and reference naturally: “this”, “that”, “what he wrote” or “you mean this?” may depend on an object, message or previous turn. Do not replace them with an explicit name or explanation that reveals unsupported information. Check the reference and its linked reaction together.
3. Preserve meaningful differences among exact reading, selective quotation, paraphrase, mistaken reading and deception. Translate the written text faithfully and the speech as spoken, including supported mistakes or performed claims. Keep the character's speaking voice and the text author's writing style distinct.
4. Group staged writing into a small number of meaningful, readable reveals; do not generate an event per keystroke. Never complete a clipped word, deleted draft or unfinished message from prediction, later context, OCR or a source subtitle alone. If the visible final stage is `I want to see y`, retain only supported meaning and incompleteness; an exact Hebrew form requires scene review.
5. Omit an extra visual-text cue as redundant only when its linked speech transfers the same required information at the right moment without losing a clue, mistake, joke, ambiguity or disclosure order. A character's reaction alone does not replace essential written information.
6. Time written cues from readable visual evidence; time speech from its spoken words. Reactions help explain the scene but do not replace either boundary. Check cumulative reading load and visibility with the exact export. Follow the controlled readability exceptions in `subtitle-editorial-rules.md`; do not reveal text early to cure density.
7. A change to writing, a stage boundary, a reading, an interpretation or a reaction must trigger recheck of linked cues and the surrounding reveal/payoff. Material differences receive independent source/context review. Unproven essential wording or interpretation remains REVIEW-IN-CONTEXT; missing access is reported honestly.

Keep semantic, visual-coverage, visual-timing, combined-reading-load and exact-output review statuses separate. Speech alignment does not verify silent writing, and sampled frames do not establish full-watch PASS.

## Slang and conversational meaning in writing

Follow `slang-and-free-translation.md` for notes, cards, messages and other selected writing as well as speech. Interpret the writer's communicative act and relationship, rather than translating every component literally or using the speaking character's register for the author. A flirtatious girl-authored "Do you like me?" may be "אני מוצאת חן בעיניך?"; it does not automatically mean a stronger "אתה אוהב אותי?". In the approved Gravity Falls card retain the exact first-person wording. Translate its revealed answer options and linked reaction as one group, without revealing later choices early or making a reader know unseen writing.
