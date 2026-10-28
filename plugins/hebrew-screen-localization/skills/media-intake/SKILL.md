---
name: media-intake
description: Inspect source film or episode assets before localization. Use for video/audio/subtitle track inventory, frame rate, runtime, source-language detection, M&E availability, and deciding the best transcription path.
---

# Media intake

Inspect before translating.

Capture: runtime, frame rate, resolution, audio tracks, channel layout, language tags, existing subtitle tracks, captions, forced-narrative tracks, timecode behavior and whether a clean M&E track exists.

Inspect representative frames for narrative cards, messages, documents, signs and existing burned-in captions; note what the supplied tracks cover and what needs visual inspection downstream. Do not treat an initial sample as full-runtime visual-text coverage.

Prefer original-language audio plus the best available source subtitle/template. Treat existing subtitles as evidence, not unquestionable truth.

If multiple audio tracks exist, identify commentary, descriptive audio, dubs and source dialogue. Do not accidentally transcribe a commentary or dub track as the original.

For dubbing, explicitly determine whether source dialogue can be removed cleanly. M&E is preferred; otherwise note that source separation and artifact QC will be required.

For subtitle timing, record audio/video stream starts, time bases/presentation timestamps, selected track and extraction details, plus the mapping from extracted-audio zero to original-media zero. Use `../../references/subtitle-synchronization.md` to keep an explicit transformation ledger; a stream start-time field is not by itself proof that a manual subtitle delay is needed. Every applied offset must have one recorded application point.

Return an intake record and recommended downstream path. Do not translate at this stage.
