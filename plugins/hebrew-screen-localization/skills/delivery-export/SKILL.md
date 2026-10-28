---
name: delivery-export
description: Package and validate final Hebrew subtitle or dubbing deliverables after QC. Use for format selection, RTL-safe export, naming/versioning, final reports, SRT/WebVTT/TTML outputs, and delivery readiness.
---

# Delivery export

Do not export a 'final' version until applicable QC gates pass.

For subtitles, export the requested format and validate parseability, timing order, encoding, RTL display, line endings and target-platform constraints. SRT is convenient for broad compatibility; WebVTT adds web semantics; TTML/IMSC is preferable when professional platform delivery requires explicit styling/direction metadata.

For dubbing, package the approved mix/stems and recording script according to the requested technical specification. Preserve sample rate, channel layout, sync reference and version metadata.

Use deterministic version names such as project_episode_language_deliverable_vNN plus an approval status. Do not overwrite the only prior approved version.

For subtitle delivery, include the timing report required by `../../references/subtitle-synchronization.md`. Verify the exported track against the original source and the exact final sidecar/muxed playback artifact, checking that every timestamp correction is applied once. Report structural/readability, speech synchronization, final-playback and continuous full-watch statuses separately. An unresolved early/late timing issue or unverified runtime region blocks final status even when the exported file parses and has no overlaps.

Return: deliverable files, version, source basis, QC status, timing report, unresolved exceptions and a concise change log.

## Local delivery safeguards

Use the packaged `export_subtitles` for SRT/WebVTT and `inspect_subtitles` on the exact exported SRT. Optional RLM is player-dependent and must be tested, not added as a universal rendering fix. Other formats need an actual available exporter. Keep raw translation, edited cues and final exports versioned; never overwrite source media or the only approved subtitle copy.

For a no-encoding request, return sidecars by default. The local tools extract PCM audio and review frames without encoding a video; they do not burn subtitles, remux tracks or alter the original. A separately requested mux requires an available stream-copy operation and verification. Deliver a concise report separating structure/readability, coverage, semantics, RTL, alignment, final playback and full-watch, with remaining limitations and exact artifact versions. Package only intended subtitles/reports and omit source media, model caches and project secrets.
