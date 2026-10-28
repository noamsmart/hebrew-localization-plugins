# Character voice and forms of address

Apply alongside `hebrew-standards.md`, `names-and-titles.md` and `quality-gates.md`. Preserve existing scoped user preferences and approved names. These records support editorial decisions; they do not establish that a speaker-identification or linguistic-analysis tool is available.

## Evidence-bearing records

Extend the job ledger and continuity bible with:

- Character: `character_id`, approved name, ordinary register, source/approved-Hebrew example cue IDs, recurring expressions, profanity intensity and intentional grammatical features.
- Relationship: speaker/addressee IDs, forms of address, titles or nicknames, context and evidence. Do not infer intimacy, status or a relationship from a single dictionary equivalent.
- Scene: `scene_id`, local register and reason for a supported change, such as professional speech, intimacy, anger or a public performance. A voice profile must allow meaningful changes within a character.
- Cue: `cue_id`, `scene_id`, `source_word_range`, `speaker_id`, `addressee_ids`, addressed number, `referent_ids`, `quoted_person_id` (whose words are quoted), quoted addressee IDs where needed, communicative act and `register`.
- Evidence: source type, timecode/locator, what it supports, confidence or unresolved question, and review status. Keep unknown identity separate from identity deliberately withheld from the audience.

Use existing IDs rather than creating competing character records. Populate fields needed to support a decision; an unknown addressee need not block a faithful line whose wording does not depend on that identity. Automated diarization, facial appearance and a still image are evidence candidates, not conclusive proof of who spoke.

Example record: `speaker_id: c1; addressee_ids: [c2]; quoted_person_id: null; register: professional; evidence: {kind: audiovisual, locator: scene/timecode, supports: speaker and addressee, confidence: confirmed}`. Each value requires actual evidence; a frame alone must be recorded as frame evidence. In `אני אוהבת אותך`, the predicate concerns the speaker; changing it to a plural form to avoid uncertainty would invent a group.

## Translation and review

1. Check each relevant agreement against its actual role: first person belongs to the speaker, second person to the addressee, and third person to its referent. In quotations, distinguish the current speaker, quoted speaker and people addressed inside the quote. Preserve source shifts of perspective rather than mechanically assigning every pronoun to the visible person.
2. Resolve material identity or agreement uncertainty through surrounding dialogue and audiovisual evidence. Use natural neutral wording when it faithfully preserves meaning and the source's disclosure; do not hide information already conveyed or use neutral wording that weakens the line. Log an unresolved material ambiguity for contextual review.
3. Preserve the character's act and delivery when condensing: a tentative request must remain tentative; a command, tease, evasion, staged reassurance or public performance must retain its force. Keep spoken language distinct from a formal written message being read or quoted.
4. Review complete exchanges as well as individual cues. Check turn-taking, changing addressees, quotation, address terms, emotional escalation and deliberate register switches. Do not normalize every utterance to one dictionary form or the character's ordinary register.
5. Compare every rewrite with the source under the semantic gate. Do not turn a character's lie, misunderstanding or staged claim into the true facts. Record a knowledge/disclosure constraint when interpretation depends on what each participant or the audience knows; use `written-text-and-character-response.md` for linked written events.
6. After changing speaker, addressee, name, agreement or register, recheck related turns and callbacks. A second reviewer should inspect material changes independently against the source and context; record reviewer, coverage and unresolved findings. If independent or audiovisual review is unavailable, state that limitation rather than claiming completion.

Report agreement checks, source fidelity, voice naturalness and disclosure checks separately. A text-only review or morphology warning is not evidence of full audiovisual QC. Send subtitle presentation to `subtitle-editorial-rules.md` and final acceptance to `quality-gates.md`.
