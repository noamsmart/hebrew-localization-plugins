# Local tools and honest capability boundaries

The Kimi plugin's stdio MCP entry starts `runtime/launch.cjs`, which locates Python 3.10+ through an explicit `HEBREW_LOCALIZATION_PYTHON` executable or an installed executable on PATH. Node must be available on PATH. There are no required pip dependencies for subtitle/project/editor tools. The process reads/writes only paths supplied for the job and uses no telemetry or external media upload. The browser editor has no external resources.

## Tool inventory

| Tool | Implemented result | Important limit |
| --- | --- | --- |
| `media_capabilities` | Detect local media/OCR/alignment prerequisites | Detection is not successful alignment, OCR or playback |
| `probe_media` | FFprobe track, codec and clock inventory | Language tags need source confirmation; choose the actual original audio stream |
| `prepare_review_segment` | Bounded PNG frames, PCM WAV and time-reference record; optional MCP image/audio content | Samples require actual sensory review; no encoded video or source modification |
| `play_review` | Bounded FFplay with explicitly selected audio and optional subtitles | Requires interactive viewing; launching it is not QC evidence |
| `scan_screen_text` | Frame/shot candidates and optional local Tesseract OCR | OCR is a candidate reading; sampling can miss transient writing |
| `align_source_speech` | Offline adapter to installed WhisperX and local models | Corrected source language text only; no download/install; alignment remains provisional |
| `transcribe_source_audio` | Selected-stream source transcription and timestamped source SRT through an explicit local faster-whisper model | ASR segments and language confidence remain REVIEW; no automatic model download, speaker identification or synchronization PASS |
| `translate_source_subtitles` | Direct source-language-to-Hebrew SRT translation through explicit local NLLB CTranslate2 model/tokenizer and optional glossary | Supports non-English NLLB source tokens; output is a machine draft requiring semantic, audiovisual and playback review |
| `inspect_subtitles` | Strict SRT structure, visible/logical counts, overlap and profile warnings | Does not evaluate meaning or source synchronization |
| `export_subtitles` | Explicit new SRT/WebVTT from cue JSON or SRT | Does not implement TTML/IMSC/ASS, styling, burn-in or mux |
| `audit_source_coverage` | Event/cue mappings, omission and complete-window/composite text coverage | Completeness is only relative to the supplied ledger |
| `build_review_queue` | Prioritize uncertainty, revisions, reading warnings and linked visual responses | Does not replace full-runtime review |
| `init_localization_job` | Explicit local project records and source fingerprints | Fingerprints identify changes; not universal memory or QC |
| `get_job_state` | Read saved state and detect changed recorded sources | Sample fingerprints are not a full cryptographic media hash |
| `save_checkpoint` | Revision-guarded state plus prior-version backup | No mechanism to certify PASS |
| `audit_character_context` | Mechanical metadata/link findings | Cannot judge natural Hebrew, agreement, identity or beliefs |
| `build_review_workspace` | Offline source/target editor, playback controls and edited-file downloads | Browser codec/audio-track support varies; use native playback when needed |

Inspect each tool's `inputSchema` rather than inventing arguments. Times/units are explicit in schemas/results. Source and export clocks remain separate; do not blindly apply offsets twice. Newly extracted audio/frames use the reported source reference and measured PTS where available. No tool has an arbitrary shell/command parameter. New-file defaults and source protection apply, but user-requested explicit output locations are authorized job paths, not a directory sandbox.

## Local execution fallback

If the host has not connected the MCP entry, an authorized local executor can run `node <plugin-root>/runtime/launch.cjs --list` or `--call <tool-name> --arguments-file <absolute-UTF8-JSON-path>`. The argument file is a JSON object matching the discovered schema. Keep intermediates in the job/work directory and return only intended deliverables. The default invocation is MCP JSONL stdio; protocol stdout contains no startup logs. Do not edit the installed cache to reconnect tools. Use the host's normal plugin update/reload flow.

FFmpeg/FFprobe/FFplay must be installed locally for media operations. Tesseract and requested traineddata are optional for OCR. WhisperX, its audio dependencies, local alignment model and required language data are optional for alignment; unavailable dependencies are reported. The adapter does not install/download, and never claims diarization or full-watch completion. Media samples are capped and output directories are explicit. Native playback is an intentional UI action, so never launch it as an unattended test.

The editor preserves cue clocks and logical text. Exported changes still need parsing, source-fidelity, timing and target-player RTL review. Use a local media picker; HEVC or multiple audio tracks may require native playback with the original-language stream. Editor download destination follows the browser's save behavior. No browser proxy conversion or reencoding is automatic.
