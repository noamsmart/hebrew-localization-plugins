# Speech act, question-vs-statement and performed tone

This policy is required in every Hebrew localization job for **selected spoken dialogue** and, as appropriate, written dialogue. Its purpose is to translate the **action a line performs** and the manner of delivery, not merely a transcript string. Pair it with `slang-and-free-translation.md`, `character-voice-and-address.md`, `written-text-and-character-response.md`, `subtitle-editorial-rules.md`, and `quality-gates.md`. It supplements rather than replaces their constraints.

## Distinguish sentence form, actual intent and manner

Three independent questions must be answered when they can affect the Hebrew:

1. **Grammatical form:** interrogative (polar, wh-, tag), declarative, imperative, exclamation, fragment, quoted/written utterance, or intentionally unfinished utterance. A string ending with `?` does not prove that it is a genuine request for information; a rising voice does not necessarily make a sentence a question.
2. **Communicative act:** asking for information, checking/confirming, rhetorical question, indirect polite request, warning, accusation, challenge, teasing, flirting, disbelief, mock surprise, refusal, command, reassurance, evasion, persuasion, threat, ironic praise, performed agreement, or another evidenced function. An interrogative can be an order, and a declarative can function as a question or challenge.
3. **Manner/delivery:** sincerity, sarcasm, irony, dry/deadpan humor, contempt, tenderness, urgency, fear, anger, disbelief, shame, hesitation, whispering, shouting, nervous laughter, emphasis, trailing off, interruption, and local changes of register. Avoid over-classifying: a character can be quiet but furious or loud without being angry.

Do **not** collapse these fields into a single emotion label. Distinguish the source speaker's intended act from what the listener believes, the literal words from deliberate subtext, and audience knowledge from character knowledge. The Hebrew must retain the supported degree of intensity and politeness rather than add unspoken motives.

## Evidence hierarchy and uncertainty

For ambiguous lines use, in order of relevance, recoverable original words; actual audio performance (pitch contour, final rise/fall, word stress, speed, rhythm, loudness, tremor, hesitation and pause); visible gesture, gaze and facial expression; previous/next turns and reactions; speaker and addressee; narrative situation and disclosed information; verified written text; existing transcript punctuation. Evidence is **context-specific**: prosodic rise alone is not proof of a question, loudness alone is not proof of anger, and facial expression alone is not proof of speaker identity.

- Original-language transcripts and ASR punctuation are hints, not authority. They may miss tag questions, sarcasm, disfluency, interruptions and simultaneous speakers. Recheck a disputed word or prosodic boundary against audio when it is available.
- For **written text**, use sentence structure, displayed punctuation, sender/writer, surrounding context and reader/reaction. A silent note has no audible prosody; do not claim to have heard its tone. Distinguish what is written from what a character reads aloud, misreads or sarcastically paraphrases.
- If only subtitle/transcript text is supplied, classify what can be grounded linguistically and by surrounding lines, but tag delivery-dependent interpretations as `UNVERIFIED_AUDIO`. Do not claim an acoustic inspection or confidently label sarcasm from bare words.
- Record `confidence: high | medium | low | unresolved`, plus `evidence_type`, supporting source cue IDs/timecodes and alternatives when the choice would change speech act or narrative meaning. Escalate low-confidence **material** cases for targeted audiovisual review. Where source ambiguity is intentional, retain it naturally in Hebrew instead of inventing a definite intention.

## Hebrew rendering rules

- **Genuine question:** produce a natural Hebrew question and appropriate question mark. Retain the subject/addressee, negation, modality, uncertainty and whether the question is open, yes/no, confirmation or a request. Respect direct and indirect forms, including short conversational questions and question tags.
- **Rhetorical question:** preserve its rhetorical challenge, surprise, humor or accusation. Do not convert it automatically to a matter-of-fact answer or statement. Use Hebrew rhetoric if it maintains the effect and source disclosure.
- **Indirect question/request:** translate the intended action, not a literal question about ability. “Can you pass that?” can be “אפשר להעביר לי את זה?” or “תעביר לי את זה, בבקשה?” as scene, relationship and level of politeness support. Do not turn a sincere ability question into an order.
- **Declarative uttered as a question:** when audiovisual/scene evidence confirms actual questioning, use a question in Hebrew even if ASR inserted a period. If it is rising **uptalk** but functions as an assertion, do not mechanically replace it with a question.
- **Sarcasm, irony, teasing and dry humor:** preserve the pragmatic reversal and implied target without adding explanatory dialogue. A literal positive word (“Great”) may be sincere or bitterly ironic. Prefer phrasing the Hebrew actor could naturally say; do not force explicit “בציניות” into ordinary interlingual subtitles.
- **Reassurance, threat, panic, anger and intimacy:** preserve speaker power, hesitation, politeness, emotional degree and relationship. Do not add profanity, shouting marks, pet names or romantic certainty that the source lacks; do not sanitize source intensity automatically.
- **Questions within quotations or written material:** keep the quoted speaker/writer and addressee distinct from the surrounding speaker. Preserve quotation boundaries and intentional discrepancies between message and spoken reaction.
- **Interrupted vs trailing-off vs hesitant vs completed:** preserve the narrative purpose of cutoffs, delayed answers, self-corrections and silence. Follow the target's editorial punctuation profile. Do not complete unfinished source syntax or insert ellipses for every cue split.
- **Punctuation:** choose `?`, `!`, period, ellipsis and interruption marks based on the utterance and subtitle style guide, not just source file symbols. Avoid decorative combinations and multiple exclamation marks unless artistically necessary. A question spread across cues gets its terminal question mark at the real end, without introducing premature punchlines. Mixed-direction punctuation must render correctly in the exported player.
- **Condensation:** preserve question polarity, who is being asked, sincerity/doubt, genuine versus rhetorical function, and the emotional turn even after splitting/shortening. A terse answer cannot be rewritten as agreement if the source is dismissive or reluctant. Keep dependent setup, question, answer and reaction jointly intelligible.
- **Nonverbal audio and SDH:** laughs, sighs, gasps, stutters and delivery labels belong in interlingual captions only when their semantic function requires them; accessibility captions follow the agreed SDH/CC profile. Do not write performance directions into regular subtitles simply to explain tone.
- **Genre and period:** preserve historical speech, child's voice, comedy rhythm, formal register, multilingual barriers and culturally specific terms without indiscriminate modern Israeli slang, forced formal Hebrew or American syntax.

## Per-cue evidence record for material cases

Record under the existing job event/continuity ledger rather than creating a conflicting database:

```
cue_id; scene_id; source_time_range; speaker_id; addressee_ids
source_text; source_form; communicative_act; delivery_tone
supports_question: yes/no/ambiguous; punctuation_choice
supporting_evidence: [{type: audio|picture|turns|writing|transcript, locator, observation}]
confidence: high|medium|low|unresolved; unresolved_alternatives
linked_setup_answer_reaction_ids; approved_hebrew; reviewer; status
```

Populate for consequential decisions such as a question mistaken for a statement, genuine versus rhetorical question, sarcastic versus literal acceptance, indirect command/request, character-switch, or meaningful pause/interruption. Do **not** demand manual metadata for every mundane phrase, and do not fabricate acoustic observations. User-approved scoped wording outranks a generic example but still requires source/context fidelity.

## Contrastive calibration cases (illustrative, not automatic replacements)

| English and evidenced performance | Hebrew possibility | Typical defect to reject |
| --- | --- | --- |
| “You're leaving.”, a certain observation | “אתה הולך.” | Wrongly turning a fact into a question |
| “You're leaving?”, seeking confirmation | “אתה הולך?” | Treating it as a certain assertion |
| “You did what?!”, incredulous request to repeat | “מה עשית?!” | Neutralizing shock or inventing a different accusation |
| “Are you serious?”, rhetorical disbelief | “אתה רציני?” / “מה, אתה רציני?” | Treating it as a clinical information request |
| “Can you help me?”, asking a favor | “תוכל לעזור לי?” / “את יכולה לעזור לי?” | “האם יש לך יכולת לעזור לי?” |
| “Fine.”, resigned agreement | “בסדר.” / “נו, שיהיה.” | Confident enthusiasm unsupported by delivery |
| “Fine.”, angry dismissal | “טוב, עזוב.” when context supports it | Unjustified warm acceptance |
| “Great.”, genuine appreciation | “מעולה.” | Invented sarcasm |
| “Great.”, dry sarcastic reaction | “יופי.” / “נהדר.”, dependent on delivery | Stating explicit anger or joy not present |
| “Why don't you stay?”, a friendly invitation | “למה שלא תישאר?” | Rendering as a hostile demand for an explanation |
| “Why don't you leave?”, a hostile dismissal | “למה שלא תלך כבר?” only if intensity supports `כבר` | Converting into a warm suggestion |
| “Thanks a lot.”, bitter reproach | “ממש תודה לך.” if natural in context | Translating as sincere gratitude |
| “Really?”, playful disbelief | “באמת?” / “די, נו!” only if intended effect fits | Treating it as a plain assertion |
| “He might be here”, tentative | “יכול להיות שהוא כאן.” | “הוא כאן.” (false certainty) |

All Hebrew choices are **scene-dependent examples**, not global string substitutions. The default should often be simple natural phrasing; maintain interpretive restraint when the audio is neutral or ambiguous.

## Review gates and invariants

- During drafting, inspect the linked exchange and classify material ambiguous utterances **before** choosing Hebrew punctuation or register. After editing, recheck the source against the final line and linked response/reveal.
- Run a dedicated **question/statement and tone pass** over selected dialogue and meaningful written questions. Test interrogatives, rhetorical questions, declaratives delivered interrogatively, tag questions, indirect requests and ironic assertions; verify the output maintains the supported act and intensity.
- Mark `PRAGMATICS_PASS` only for reviewed scenes with actual source/context evidence. If missing performance audio matters, record `PARTIAL / UNVERIFIED_AUDIO`, not PASS. This does not mark synchronization, RTL or continuous full-watch as complete.
- QA must inspect both wrong punctuation and wrong **force** even when punctuation is superficially correct. A grammatically flawless “?” cue can still mistranslate a rhetorical threat as a polite question.
- A corrective change to a cue triggers recheck of its answer, gesture, reaction, recurring joke and dependent visual text where affected. Preserve source timing/reveal; linguistic correction does not license an automatic timing shift.

## Further editorial checks integrated with intent

1. **Point of view and reference:** pronouns, gender and number by actual speaker/addressee/referent, including quotation and deliberately undisclosed identity.
2. **Negation and modality:** can/may/must/should, permission versus ability, probabilities and hesitant claims, scope of “not”, rhetorical negatives and negative questions.
3. **Power and politeness:** authority, formality, familiarity, intimacy, passive aggression and scene-specific switches; don't make all voices identical.
4. **Implied versus explicit meaning:** preserve subtext without invented exposition or plot spoilers; distinguish lies and mistaken character beliefs from narrator truth.
5. **Response dependency:** yes/no answers, echo questions, repair sequences, overlapping voices and abrupt speaker changes must fit what preceded them.
6. **Comedy and linguistic mechanics:** mishearing, puns, timing, callbacks, deadpan sarcasm, word stress, visual gags and deliberate clumsy speech must survive as connected units.
7. **Disfluency and delivery:** stutter, false start, surprise, silence, interruption and trailing off are included only if they are meaningfully expressive.
8. **Text-to-speech mismatches:** onscreen messages, signs, quotations and dialogue about them preserve distinct writer/reader/viewer knowledge and reveal order.
9. **Audience profile:** genre, period, speaker age, culture, dialect, source profanity strength and platform subtitle constraints govern wording, not fashion.
10. **Technical closure:** word-level synchronization when required, readable CPS/line length, shot changes, visual-text windows, RTL in player, coverage and actual continuous full-watch remain independent quality gates.
