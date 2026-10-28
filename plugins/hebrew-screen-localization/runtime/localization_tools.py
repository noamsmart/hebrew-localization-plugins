"""Optional direct source-language ASR and Hebrew translation adapters.

All models are explicit local directories. Network access and automatic downloads
are disabled. Outputs are drafts/evidence, never semantic or synchronization PASS.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import textwrap

from media_tools import (
    MEDIA, AUDIO, LOCAL_WRITE, MediaToolError, _audio, _file, _fresh_directory,
    _identifier, _integer, _ledger, _number, _package_available, _probe,
    _range, _read_srt, _schema, _stream, _write_json, MAX_ALIGNMENT_SECONDS,
)

MAX_TRANSLATION_CUES = 20000
LANG_TOKEN = re.compile(r"^[a-z]{3}_[A-Z][a-z]{3}$")


def _offline_environment():
    os.environ.update({
        "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
        "HF_DATASETS_OFFLINE": "1", "TOKENIZERS_PARALLELISM": "false",
    })


def _model_directory(value, label, required):
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise MediaToolError(f"{label} must identify a local model directory")
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise MediaToolError(f"{label} does not exist: {path}")
    missing = [name for name in required if not (path / name).is_file()]
    if missing:
        raise MediaToolError(f"{label} is missing: {', '.join(missing)}")
    return path


def _language_token(value, label):
    if not isinstance(value, str) or not LANG_TOKEN.fullmatch(value):
        raise MediaToolError(f"{label} must be an NLLB token such as eng_Latn, nob_Latn or heb_Hebr")
    return value


def _srt_clock(seconds):
    milliseconds = max(0, round(seconds * 1000))
    hours, milliseconds = divmod(milliseconds, 3600000)
    minutes, milliseconds = divmod(milliseconds, 60000)
    secs, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def transcribe_source_audio(args):
    """Transcribe selected source audio with an installed faster-whisper model."""
    source = _file(args.get("media_path"), "media_path")
    model = _model_directory(args.get("asr_model_path"), "asr_model_path", ("model.bin", "config.json"))
    data, _ = _probe(source)
    stream = _stream(data, args.get("audio_stream_index"), "audio")
    start, duration = _range(args, data, MAX_ALIGNMENT_SECONDS)
    language = args.get("source_language")
    if not isinstance(language, str) or not re.fullmatch(r"[a-z]{2,3}", language):
        raise MediaToolError("source_language must be an ISO Whisper code such as no, en or he")
    missing = [name for name in ("faster_whisper", "ctranslate2", "av") if not _package_available(name)]
    if missing:
        return {"status": "NOT_AVAILABLE", "missing_dependencies": missing,
                "automatic_install_or_download": False, "output_created": False}
    directory = _fresh_directory(args.get("output_dir"))
    audio = _audio(source, data, stream, start, duration, directory / "source_audio.wav", directory)
    request = {
        "audio_path": audio["path"], "model_path": str(model), "language": language,
        "beam_size": _integer(args.get("beam_size", 3), "beam_size", 1, 5),
        "device": args.get("device", "cpu"), "audio_zero": audio["audio_zero_source_media_seconds"],
        "result_path": str(directory / "transcript.json"), "srt_path": str(directory / "source.srt"),
    }
    if request["device"] not in ("cpu", "cuda"):
        raise MediaToolError("device must be cpu or cuda")
    _write_json(directory / "transcription_request.json", request)
    _offline_environment()
    from faster_whisper import WhisperModel
    asr = WhisperModel(str(model), device=request["device"], compute_type="int8", local_files_only=True)
    segments, info = asr.transcribe(audio["path"], language=language, task="transcribe",
                                    beam_size=request["beam_size"], vad_filter=True)
    rows, srt_blocks = [], []
    for index, segment in enumerate(segments, 1):
        text = segment.text.strip()
        if not text:
            continue
        lower, upper = segment.start + request["audio_zero"], segment.end + request["audio_zero"]
        row = {"cue_id": index, "start_seconds": lower, "end_seconds": upper,
               "text": text, "avg_logprob": segment.avg_logprob,
               "no_speech_prob": segment.no_speech_prob, "status": "REVIEW"}
        rows.append(row)
        wrapped = textwrap.wrap(text, width=42, break_long_words=False, break_on_hyphens=False)
        srt_blocks.append(f"{index}\n{_srt_clock(lower)} --> {_srt_clock(upper)}\n" + "\n".join(wrapped))
    (directory / "source.srt").write_text("\n\n".join(srt_blocks) + "\n", encoding="utf-8", newline="\n")
    transcript = {"status": "PARTIAL", "source": _identifier(source), "model_path": str(model),
                  "language": info.language, "language_probability": info.language_probability,
                  "requested_language": language, "segments": rows,
                  "automatic_install_or_download": False,
                  "translation_quality_status": "NOT_EVALUATED",
                  "synchronization_status": "ASR_CANDIDATES_NOT_VERIFIED"}
    _write_json(directory / "transcript.json", transcript)
    return {"status": "PARTIAL", "source": _identifier(source), "audio_stream": stream,
            "requested_interval": [start, start + duration], "audio": audio,
            "transformation_ledger": _ledger(data, audio), "language": info.language,
            "language_probability": info.language_probability, "segment_count": len(rows),
            "source_srt": str(directory / "source.srt"), "transcript_json": str(directory / "transcript.json"),
            "automatic_install_or_download": False, "translation_quality_status": "NOT_EVALUATED",
            "synchronization_status": "ASR_CANDIDATES_NOT_VERIFIED",
            "continuous_watch_status": "NOT_VERIFIED"}


def _clean_source_line(text):
    return re.sub(r"\{[^}]*\}|<[^>]*>", "", text).strip()


def _protect_names(text, glossary):
    mapping = {}
    for index, source in enumerate(sorted(glossary, key=len, reverse=True)):
        token = f"ZXQNAME{index:04d}QXZ"
        text, count = re.subn(rf"(?<![\w]){re.escape(source)}(?![\w])", token, text, flags=re.UNICODE)
        if count:
            mapping[token] = glossary[source]
    return text, mapping


def translate_source_subtitles(args):
    """Translate existing source-language SRT to Hebrew with a local NLLB CT2 model."""
    source = _file(args.get("source_srt"), "source_srt")
    cues = _read_srt(source)
    if len(cues) > MAX_TRANSLATION_CUES:
        raise MediaToolError("Too many subtitle events in one job")
    model = _model_directory(args.get("translation_model_path"), "translation_model_path", ("model.bin", "config.json"))
    tokenizer_path = _model_directory(args.get("tokenizer_path"), "tokenizer_path", ("tokenizer.json",))
    source_language = _language_token(args.get("source_language"), "source_language")
    target_language = _language_token(args.get("target_language", "heb_Hebr"), "target_language")
    glossary = {}
    if args.get("glossary_path"):
        glossary_path = _file(args.get("glossary_path"), "glossary_path")
        raw = json.loads(glossary_path.read_text(encoding="utf-8-sig"))
        glossary = raw.get("names", raw)
        if not isinstance(glossary, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in glossary.items()):
            raise MediaToolError("Glossary must be a string-to-string JSON object or contain a names object")
    missing = [name for name in ("ctranslate2", "transformers", "tokenizers") if not _package_available(name)]
    if missing:
        return {"status": "NOT_AVAILABLE", "missing_dependencies": missing,
                "automatic_install_or_download": False, "output_created": False}
    output = Path(args.get("output_path", "")).expanduser().resolve()
    if not str(output) or output.exists():
        raise MediaToolError("output_path must be a new local file")
    if output == source:
        raise MediaToolError("Source subtitles must not be overwritten")
    _offline_environment()
    import ctranslate2
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(str(tokenizer_path), src_lang=source_language, local_files_only=True)
    translator = ctranslate2.Translator(str(model), device="cpu", compute_type="int8",
                                        inter_threads=1, intra_threads=_integer(args.get("threads", 8), "threads", 1, 32))
    batch_size = _integer(args.get("batch_size", 32), "batch_size", 1, 128)
    entries = []
    for cue_index, cue in enumerate(cues):
        for line_index, raw_line in enumerate(cue["text"].splitlines()):
            cleaned = _clean_source_line(raw_line)
            if cleaned:
                entries.append((cue_index, line_index, cleaned))
    translated = {}
    cache = {}
    for offset in range(0, len(entries), batch_size):
        chunk = entries[offset:offset + batch_size]
        sources, mappings, prefixes = [], [], []
        for _, _, text in chunk:
            if text in cache:
                continue
            prefix = "- " if text.startswith("-") else ""
            content = text[1:].strip() if prefix else text
            protected, mapping = _protect_names(content, glossary)
            sources.append(tokenizer.convert_ids_to_tokens(tokenizer.encode(protected)))
            mappings.append(mapping)
            prefixes.append(prefix)
        if sources:
            results = translator.translate_batch(sources, target_prefix=[[target_language]] * len(sources),
                                                  beam_size=3, max_decoding_length=160)
            result_index = 0
            for _, _, text in chunk:
                if text in cache:
                    continue
                hypothesis = results[result_index].hypotheses[0]
                result_index += 1
                value = tokenizer.decode(tokenizer.convert_tokens_to_ids(hypothesis), skip_special_tokens=True).strip()
                mapping = mappings[result_index - 1]
                for token, replacement in mapping.items():
                    value = value.replace(token, replacement)
                if re.search(r"ZXQNAME\d{4}QXZ", value):
                    raise MediaToolError("Translation model altered a protected glossary placeholder")
                prefix = prefixes[result_index - 1]
                if prefix:
                    value = re.sub(r"^[-–—]\s*", "", value)
                cache[text] = prefix + value
        for cue_index, line_index, text in chunk:
            translated[(cue_index, line_index)] = cache[text]
    blocks = []
    for cue_index, cue in enumerate(cues):
        lines = []
        for line_index, raw_line in enumerate(cue["text"].splitlines()):
            value = translated.get((cue_index, line_index), "")
            prefix = "- " if value.startswith("- ") else ""
            width = 40 if prefix else 42
            wrapped = textwrap.wrap(value, width=width, break_long_words=False, break_on_hyphens=False) or [""]
            lines.extend("\u202b" + part + "\u202c" for part in wrapped)
        blocks.append(f"{cue['cue_id']}\n{_srt_clock(cue['start'])} --> {_srt_clock(cue['end'])}\n" + "\n".join(lines))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\r\n") as target:
        target.write("\n\n".join(blocks) + "\n")
    report = {"status": "DRAFT", "source_srt": _identifier(source, True),
              "output_srt": _identifier(output, True), "cue_count": len(cues),
              "source_language": source_language, "target_language": target_language,
              "translation_model_path": str(model), "tokenizer_path": str(tokenizer_path),
              "glossary_entries": len(glossary), "automatic_install_or_download": False,
              "translation_quality_status": "MACHINE_DRAFT_REVIEW_REQUIRED",
              "synchronization_status": "SOURCE_CLOCKS_PRESERVED_NOT_AUDIO_ALIGNED",
              "continuous_watch_status": "NOT_VERIFIED"}
    report_path = output.with_suffix(output.suffix + ".report.json")
    _write_json(report_path, report)
    report["report_path"] = str(report_path)
    return report


TOOLS = {
    "transcribe_source_audio": {
        "description": "Transcribe a selected non-English or English audio stream with an explicit local faster-whisper model. Produces source SRT and review transcript; offline only; no translation or sync PASS.",
        "inputSchema": _schema({**MEDIA, **AUDIO,
            "asr_model_path": {"type": "string", "description": "Local faster-whisper CTranslate2 model directory."},
            "source_language": {"type": "string", "description": "Whisper ISO source code, for example no, en or he."},
            "beam_size": {"type": "integer", "minimum": 1, "maximum": 5, "default": 3},
            "device": {"type": "string", "enum": ["cpu", "cuda"], "default": "cpu"}},
            ["media_path", "output_dir", "start_seconds", "duration_seconds", "audio_stream_index", "asr_model_path", "source_language"]),
        "handler": transcribe_source_audio, "annotations": LOCAL_WRITE},
    "translate_source_subtitles": {
        "description": "Translate source-language SRT directly to Hebrew with explicit local NLLB CTranslate2 model and tokenizer. Supports non-English NLLB source tokens; preserves clocks and returns a machine-draft QC status.",
        "inputSchema": _schema({
            "source_srt": {"type": "string"}, "output_path": {"type": "string"},
            "translation_model_path": {"type": "string"}, "tokenizer_path": {"type": "string"},
            "source_language": {"type": "string", "description": "NLLB source token such as nob_Latn, eng_Latn or rus_Cyrl."},
            "target_language": {"type": "string", "default": "heb_Hebr"},
            "glossary_path": {"type": "string"}, "batch_size": {"type": "integer", "minimum": 1, "maximum": 128, "default": 32},
            "threads": {"type": "integer", "minimum": 1, "maximum": 32, "default": 8}},
            ["source_srt", "output_path", "translation_model_path", "tokenizer_path", "source_language"]),
        "handler": translate_source_subtitles, "annotations": LOCAL_WRITE},
}
