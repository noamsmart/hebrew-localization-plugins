# Tooling contract

This workflow can produce studio-grade results only when the underlying environment exposes the required media capabilities. Skills must inspect available tools and use the strongest available path. Never claim a media step was completed if the source could not actually be accessed.

## Required capabilities for full automation

1. Media probing: duration, frame rate, resolution, audio/subtitle tracks, language tags, time base and codec metadata.
2. Audio extraction and channel/stem handling. FFmpeg-class functionality is sufficient for demuxing and muxing.
3. Speech recognition with word- or segment-level timestamps and confidence data.
4. Speaker diarization or reliable speaker assignment support.
5. Direct video/audio inspection for ambiguous lines, scene context, visible speakers, signs and on-screen text.
6. Subtitle parsing and writing for at least SRT and WebVTT; TTML/IMSC support is strongly preferred for professional RTL delivery.
7. Subtitle timing analysis: duration, frame gaps, characters per line, characters per second and overlap checks.
8. Optional shot-change detection for timing polish.
9. Optional source separation or access to dialogue/music/effects stems for dubbing. An M&E track is preferred.
10. Optional speech synthesis/recording tools for scratch dubbing; final broadcast dubbing should use appropriately licensed voices and a proper mix.

## Speech synchronization capability

For subtitle synchronization, require corrected source-word/phrase alignment against the actual selected audio and direct audiovisual verification of uncertain boundaries, with coverage of every translated event throughout the runtime. Recognition segment timestamps, VAD, overlap checks, reading-speed checks, screenshots or a successful mux do not provide this capability on their own. Follow `subtitle-synchronization.md`, preserve raw and transformed time domains, verify the original and exact delivered playback artifact, and save the timing report. If the environment cannot complete this evidence, report synchronization as PARTIAL/NOT VERIFIED and continue verifiable work without a final/synchronized claim.

## Operational truthfulness

If full-video playback is not available, say exactly which parts were verified from audio, subtitle files, frames or transcripts. Do not describe a spot-check as a full-watch QC pass.

## Background voices

For standard interlingual subtitles, incidental background chatter should normally be omitted unless viewers are meant to understand it or it is plot-relevant. For SDH, audible information is treated differently and meaningful sounds/speech may need inclusion.

For dubbed audio, translated speech must not simply be layered over clearly audible source dialogue. Prefer an M&E track. If none exists, use high-quality dialogue/source separation and manually inspect artifacts before mixing.

## Packaged local capabilities (0.3.0)

The plugin now includes a standard-library Python local MCP server and Node launcher declared in `../mcp.json`. See `local-tools.md` for actual tool contracts and `../skills/local-subtitle-tools/SKILL.md` for discovery/fallback. SRT parsing, SRT/WebVTT export, structural/readability checks, source-ledger coverage, review queues, project checkpoints, metadata audits and an offline editing workspace are implemented locally. FFprobe/FFmpeg/FFplay, Tesseract and WhisperX remain optional locally installed dependencies; call `media_capabilities` before assuming them. The runtime neither installs packages nor downloads models.

The alignment adapter needs explicitly available local speech/alignment models and language data; OCR needs the requested installed Tesseract language data. Missing dependencies produce a truthful capability result. Diarization, human-grade scene interpretation, source separation, dubbing synthesis, TTML/IMSC/ASS export and full-watch acceptance are not implemented by this server. They require another available tool/reviewer. A local package saved to the account does not automatically prove the current host connected its MCP server; web/mobile cannot run this local stdio process.
