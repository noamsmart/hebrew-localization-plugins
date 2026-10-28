"""Local media evidence tools. Stdlib core; optional OCR/alignment never downloads.

Handlers return data, not QC approval. Only play_review opens a player window.
All subprocesses use argv lists, never a shell. Subtitle filter paths are avoided
by byte-for-byte staging to a fixed, safe basename in a fresh output directory.
"""
from __future__ import annotations

import base64
import csv
import hashlib
import importlib.util
import inspect
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import socket
import statistics
import subprocess
import sys
import wave
from fractions import Fraction


class MediaToolError(ValueError):
    """Invalid input, unavailable required utility, or failed local operation."""


MAX_REVIEW_SECONDS = 180.0
MAX_SCAN_SECONDS = 180.0
MAX_ALIGNMENT_SECONDS = 21600.0
MAX_FRAMES = 24
SAFE_SRT_NAME = "delivered.srt"
TIME = r"(\d{2,}):(\d{2}):(\d{2})[,.](\d{3})"
SRT_TIME = re.compile(r"^" + TIME + r"\s*-->\s*" + TIME + r"(?:\s+.*)?$")


def _number(value, name, minimum=0.0, maximum=None):
    if isinstance(value, bool):
        raise MediaToolError(f"{name} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise MediaToolError(f"{name} must be a finite number") from None
    if not math.isfinite(number) or number < minimum or (maximum is not None and number > maximum):
        raise MediaToolError(f"{name} outside allowed range")
    return number


def _integer(value, name, minimum=0, maximum=None):
    number = _number(value, name, minimum, maximum)
    if number != int(number):
        raise MediaToolError(f"{name} must be an integer")
    return int(number)


def _reject_remote(value, name):
    text = str(value).strip()
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", text) or text.replace("\\", "/").startswith("//"):
        raise MediaToolError(f"{name} must be local; URLs, UNC and device paths are not accepted")


def _file(value, name):
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise MediaToolError(f"{name} must name a local file")
    _reject_remote(value, name)
    path = Path(value).expanduser().resolve()
    _reject_remote(path, name)
    if not path.is_file():
        raise MediaToolError(f"{name} does not exist: {path}")
    return path


def _utility(name):
    path = shutil.which(name)
    if not path:
        raise MediaToolError(f"missing_dependency: {name}; no automatic installation")
    return path


def _run(command, *, cwd=None, timeout=120, env=None):
    try:
        result = subprocess.run(command, cwd=cwd, env=env, capture_output=True,
                                text=True, encoding="utf-8", errors="replace",
                                timeout=timeout, shell=False)
    except subprocess.TimeoutExpired:
        raise MediaToolError(f"Local operation exceeded {timeout}s") from None
    except OSError as exc:
        raise MediaToolError(f"Cannot execute local utility: {exc}") from exc
    if result.returncode:
        # Do not return environment variables or large unsolicited output.
        raise MediaToolError(f"{Path(command[0]).name} failed: {result.stderr[-3000:]}")
    return result


def _identifier(path, full_hash=False):
    stat = path.stat()
    result = {"path": str(path), "size_bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns}
    if full_hash:
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        result["sha256"] = digest.hexdigest()
    return result


def _fresh_directory(value):
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise MediaToolError("output_dir must be a new local directory")
    _reject_remote(value, "output_dir")
    path = Path(value).expanduser().resolve()
    _reject_remote(path, "output_dir")
    if path.exists():
        raise MediaToolError(f"Refusing output overwrite: {path} already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.mkdir()
    except FileExistsError:
        raise MediaToolError(f"Refusing output overwrite: {path}") from None
    return path


def _write_json(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as target:
        json.dump(data, target, ensure_ascii=False, indent=2, allow_nan=False)


def _srt_seconds(values):
    h, m, s, ms = map(int, values)
    if m > 59 or s > 59:
        raise MediaToolError("Invalid SRT timestamp")
    return h * 3600 + m * 60 + s + ms / 1000


def _read_srt(path):
    try:
        text = path.read_bytes().decode("utf-8-sig")
    except UnicodeDecodeError:
        raise MediaToolError("SRT must be UTF-8 (UTF-8 BOM accepted)") from None
    cues = []
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n").replace("\r", "\n").strip()):
        lines = block.splitlines()
        if not lines:
            continue
        timing_index = 1 if lines[0].strip().isdigit() else 0
        if timing_index >= len(lines):
            raise MediaToolError("SRT event has no timing line")
        match = SRT_TIME.fullmatch(lines[timing_index].strip())
        if not match:
            raise MediaToolError(f"Invalid SRT timing line: {lines[timing_index][:100]}")
        start, end = _srt_seconds(match.groups()[:4]), _srt_seconds(match.groups()[4:])
        if end <= start:
            raise MediaToolError("SRT event has non-positive duration")
        cues.append({"cue_id": lines[0].strip() if timing_index else str(len(cues) + 1),
                     "start": start, "end": end, "text": "\n".join(lines[timing_index + 1:])})
    if not cues:
        raise MediaToolError("SRT contains no events")
    return cues


def _stage_srt(source, directory):
    target = directory / SAFE_SRT_NAME
    with source.open("rb") as original, target.open("xb") as staged:
        shutil.copyfileobj(original, staged)
    return target


def _probe(path):
    command = [_utility("ffprobe"), "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)]
    try:
        data = json.loads(_run(command, timeout=60).stdout)
    except json.JSONDecodeError as exc:
        raise MediaToolError("ffprobe returned invalid JSON") from exc
    if not data.get("streams"):
        raise MediaToolError("No media streams found")
    return data, command


def _origin(data):
    value = data.get("format", {}).get("start_time", "0")
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    return number if math.isfinite(number) else 0.0


def _duration(data):
    values = [data.get("format", {}).get("duration")]
    values.extend(stream.get("duration") for stream in data.get("streams", []))
    finite = []
    for value in values:
        try:
            parsed = float(value)
            if math.isfinite(parsed) and parsed > 0:
                finite.append(parsed)
        except (TypeError, ValueError):
            pass
    if not finite:
        raise MediaToolError("Source duration unavailable; bounded extraction cannot be checked")
    return max(finite)


def _stream(data, index, kind):
    index = _integer(index, f"{kind}_stream_index")
    for stream in data["streams"]:
        if stream.get("index") == index:
            if stream.get("codec_type") != kind:
                raise MediaToolError(f"Stream {index} is not {kind}")
            if kind == "video" and stream.get("disposition", {}).get("attached_pic"):
                raise MediaToolError("Attached cover art is not a source video stream")
            return stream
    raise MediaToolError(f"Stream {index} not found")


def _video(data, args):
    if "video_stream_index" in args:
        return _stream(data, args["video_stream_index"], "video")
    for stream in data["streams"]:
        if stream.get("codec_type") == "video" and not stream.get("disposition", {}).get("attached_pic"):
            return stream
    raise MediaToolError("Source has no video stream")


def _range(args, data, maximum):
    start = _number(args.get("start_seconds"), "start_seconds")
    duration = _number(args.get("duration_seconds"), "duration_seconds", 0.001, maximum)
    if start + duration > _duration(data) + 0.0005:
        raise MediaToolError("Requested range exceeds source duration")
    return start, duration


def _fps(stream):
    for key in ("avg_frame_rate", "r_frame_rate"):
        try:
            rate = Fraction(stream.get(key, "0/1"))
            if rate > 0:
                return float(rate)
        except (ValueError, ZeroDivisionError, TypeError):
            pass
    return None


def _pts_records(log, kind="video"):
    """Use integer PTS/time base, not FFmpeg's rounded human-readable pts_time."""
    if kind == "audio":
        prefix = r"\[Parsed_ashowinfo[^\]]*\]"
        time_base = None
    else:
        prefix = r"\[Parsed_showinfo[^\]]*\]"
        config = re.search(r"config in time_base:\s*(\d+)/(\d+)", log)
        time_base = Fraction(int(config[1]), int(config[2])) if config else None
    rows = []
    for match in re.finditer(prefix + r"[^\r\n]*?\bn:\s*\d+\s+pts:\s*([+-]?\d+)\s+pts_time:([+-]?[\d.]+)([^\r\n]*)", log):
        base = time_base
        samples = None
        if kind == "audio":
            rate = re.search(r"\brate:(\d+)", match[3])
            count = re.search(r"\bnb_samples:(\d+)", match[3])
            if rate:
                base = Fraction(1, int(rate[1]))
            if count:
                samples = int(count[1])
        if base is None:
            raise MediaToolError("Source PTS time base unavailable; rounded log time is not exact evidence")
        rows.append({"pts_ticks": int(match[1]), "time_base": str(base),
                     "seconds": float(int(match[1]) * base),
                     "rounded_log_seconds": float(match[2]), "sample_count": samples})
    return rows


def _pts(log, kind="video"):
    return [row["seconds"] for row in _pts_records(log, kind)]


def _base_source_command(path, start, *, duration=None):
    command = [_utility("ffmpeg"), "-nostdin", "-n", "-hide_banner", "-loglevel", "info",
               "-ss", f"{start:.9f}", "-copyts", "-threads", "2"]
    if duration is not None:
        command.extend(["-t", f"{duration:.9f}"])
    return command + ["-i", str(path)]


def _frame(path, data, stream, requested, target, directory, *, subtitles=False):
    origin = _origin(data)
    filters = "showinfo"
    if subtitles:
        # The fixed basename is deliberately not a user-controlled FFmpeg filter.
        filters += f",setpts=PTS-({origin:.9f})/TB,subtitles=filename={SAFE_SRT_NAME}"
    command = _base_source_command(path, requested)
    command += ["-map", f"0:{stream['index']}", "-an", "-sn", "-dn", "-vf", filters,
                "-frames:v", "1", "-pix_fmt", "rgb24", "-update", "1", str(target)]
    result = _run(command, cwd=directory, timeout=90)
    timestamps = _pts_records(result.stderr)
    if not target.is_file() or not timestamps:
        raise MediaToolError("Frame extraction produced no native PTS evidence")
    first = timestamps[0]
    return {"requested_media_seconds": requested, "source_pts_seconds": first["seconds"],
            "source_pts_ticks": first["pts_ticks"], "source_pts_time_base": first["time_base"],
            "source_media_seconds": first["seconds"] - origin, "path": str(target),
            "identifier": _identifier(target, True), "command": command}


def _audio(path, data, stream, start, duration, target, directory):
    origin = _origin(data)
    raw_start, raw_end = origin + start, origin + start + duration
    filters = (f"atrim=start={raw_start:.9f}:end={raw_end:.9f},aresample=16000,"
               "aformat=sample_fmts=s16:channel_layouts=mono,ashowinfo,asetpts=PTS-STARTPTS")
    command = _base_source_command(path, start, duration=duration + 0.5)
    command += ["-map", f"0:{stream['index']}", "-vn", "-sn", "-dn", "-af", filters,
                "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(target)]
    result = _run(command, cwd=directory, timeout=max(90, min(1800, duration * 0.5)))
    timestamps = _pts_records(result.stderr, "audio")
    if not target.is_file() or not timestamps:
        raise MediaToolError("Audio extraction produced no source-sample PTS evidence")
    with wave.open(str(target), "rb") as audio:
        samples, rate, channels = audio.getnframes(), audio.getframerate(), audio.getnchannels()
    if not samples or rate != 16000 or channels != 1:
        raise MediaToolError("Extracted audio is empty or has unexpected PCM format")
    for previous, current in zip(timestamps, timestamps[1:]):
        if previous["sample_count"] is None or abs(current["pts_ticks"] - previous["pts_ticks"] - previous["sample_count"]) > 1:
            raise MediaToolError("Noncontiguous source audio PTS: a single affine audio clock is unsupported; no synchronization verified")
    if sum(row["sample_count"] or 0 for row in timestamps) != samples:
        raise MediaToolError("Decoded source sample count differs from WAV; audio time ledger cannot be verified")
    first = timestamps[0]
    return {"path": str(target), "identifier": _identifier(target, True), "command": command,
            "sample_rate": rate, "sample_count": samples, "channels": channels,
            "duration_seconds": samples / rate, "first_source_pts_seconds": first["seconds"],
            "first_source_pts_ticks": first["pts_ticks"], "source_pts_time_base": first["time_base"],
            "audio_pts_contiguous": True, "audio_zero_source_media_seconds": first["seconds"] - origin,
            "last_sample_source_media_seconds": first["seconds"] - origin + (samples - 1) / rate}


def _ledger(data, audio=None):
    origin = _origin(data)
    ledger = [{"input_domain": "raw_source_pts_seconds", "output_domain": "source_media_seconds",
               "scale": 1, "offset_seconds": -origin, "applied_at": "reported source frame/audio timestamps",
               "reason": "Media playback zero is the probed format start_time; not an observed AV delay"}]
    if audio:
        ledger.append({"input_domain": "extracted_audio_seconds", "output_domain": "source_media_seconds",
                       "scale": 1, "offset_seconds": audio["audio_zero_source_media_seconds"],
                       "applied_at": "alignment word timestamps only",
                       "reason": "Measured first sample after trim/resample; never also add requested seek"})
    return ledger


def _package_available(name):
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def media_capabilities(args):
    utilities = {}
    for name in ("ffmpeg", "ffprobe", "ffplay", "tesseract"):
        path = shutil.which(name)
        info = {"available": bool(path), "path": path, "version": None}
        if path:
            try:
                result = _run([path, "--version" if name == "tesseract" else "-version"], timeout=10)
                info["version"] = (result.stdout or result.stderr).splitlines()[0]
            except (MediaToolError, IndexError) as exc:
                info["version_error"] = str(exc)
        utilities[name] = info
    ffmpeg = utilities["ffmpeg"]
    if ffmpeg["available"]:
        try:
            filters = _run([ffmpeg["path"], "-hide_banner", "-filters"], timeout=10).stdout
            ffmpeg["subtitle_rendering_available"] = bool(re.search(r"\bsubtitles\s+V", filters))
        except MediaToolError as exc:
            ffmpeg["filter_probe_error"] = str(exc)
    return {"utilities": utilities, "optional_python_packages": {name: _package_available(name) for name in ("whisperx", "torch", "transformers", "nltk")},
            "alignment": {"adapter": "WhisperX", "requires_local_model_directory": True,
                          "automatic_install_or_download": False, "evidence_status": "NOT_VERIFIED"},
            "continuous_watch_status": "NOT_VERIFIED", "video_encoding": False}


def probe_media(args):
    path = _file(args.get("media_path"), "media_path")
    data, command = _probe(path)
    return {"source": _identifier(path, bool(args.get("hash_source", False))), "probe": data,
            "command": command, "time_reference": {"source_media_zero_raw_pts_seconds": _origin(data),
                                                       "unit": "seconds", "AV_delay_observed": None},
            "qc_status": "NOT_VERIFIED"}


def prepare_review_segment(args):
    source = _file(args.get("media_path"), "media_path")
    subtitle = _file(args.get("subtitle_path"), "subtitle_path")
    cues = _read_srt(subtitle)
    data, _ = _probe(source)
    audio_stream = _stream(data, args.get("audio_stream_index"), "audio")
    video_stream = _video(data, args)
    start, duration = _range(args, data, MAX_REVIEW_SECONDS)
    count = _integer(args.get("frame_count", 3), "frame_count", 1, MAX_FRAMES)
    times = args.get("frame_times_seconds")
    if times is None:
        times = [start + duration * i / count for i in range(count)]
    else:
        if not isinstance(times, list) or not 1 <= len(times) <= MAX_FRAMES:
            raise MediaToolError("frame_times_seconds must have 1..24 entries")
        times = [_number(value, "frame_times_seconds") for value in times]
        if any(not start <= value < start + duration for value in times):
            raise MediaToolError("Frame times must lie within the requested half-open range")
    directory = _fresh_directory(args.get("output_dir"))
    staged = _stage_srt(subtitle, directory)
    frames = []
    for index, timestamp in enumerate(times):
        original = _frame(source, data, video_stream, timestamp, directory / f"source_{index:03d}.png", directory)
        rendered = _frame(source, data, video_stream, timestamp, directory / f"subtitles_{index:03d}.png", directory, subtitles=True)
        if abs(original["source_pts_seconds"] - rendered["source_pts_seconds"]) > 0.0005:
            raise MediaToolError("Native/rendered frames have different source PTS")
        active = [cue for cue in cues if cue["start"] <= original["source_media_seconds"] < cue["end"]]
        frames.append({"source": original, "with_exact_subtitle": rendered, "active_subtitle_events": active,
                       "review_status": "NOT_VERIFIED"})
    audio = _audio(source, data, audio_stream, start, duration, directory / "selected_audio.wav", directory)
    result = {"status": "PARTIAL", "source": _identifier(source), "exact_subtitle": _identifier(subtitle, True),
              "staged_subtitle": _identifier(staged, True), "audio_stream": audio_stream,
              "video_stream": video_stream, "requested_interval": [start, start + duration],
              "frames": frames, "audio": audio, "transformation_ledger": _ledger(data, audio),
              "video_encoding_performed": False, "rendering_generated": True,
              "original_playback_status": "NOT_VERIFIED", "final_playback_status": "NOT_VERIFIED",
              "continuous_watch_status": "NOT_VERIFIED",
              "limitations": ["Generated evidence requires direct inspection; it is not playback or a full-watch pass.",
                              "Separate PNG and WAV evidence does not constitute simultaneous audiovisual playback."]}
    manifest = directory / "review_segment.json"
    _write_json(manifest, result)
    result["manifest_path"] = str(manifest)
    if args.get("include_media", False):
        # Limit MCP inline payload independently from extraction bounds.
        blocks, total = [], 0
        for frame in frames[:3]:
            payload = Path(frame["with_exact_subtitle"]["path"]).read_bytes()
            if total + len(payload) <= 6 * 1024 * 1024:
                blocks.append({"type": "image", "mimeType": "image/png", "data": base64.b64encode(payload).decode("ascii")})
                total += len(payload)
        if audio["duration_seconds"] <= 30 and Path(audio["path"]).stat().st_size <= 2 * 1024 * 1024:
            blocks.append({"type": "audio", "mimeType": "audio/wav", "data": base64.b64encode(Path(audio["path"]).read_bytes()).decode("ascii")})
        result["_media"] = blocks
    return result


def play_review(args):
    """Explicit tool call is authorization to open the bounded ffplay window."""
    source = _file(args.get("media_path"), "media_path")
    subtitle = _file(args.get("subtitle_path"), "subtitle_path")
    _read_srt(subtitle)
    data, _ = _probe(source)
    stream = _stream(data, args.get("audio_stream_index"), "audio")
    video = _video(data, args)
    start, duration = _range(args, data, MAX_REVIEW_SECONDS)
    player = _utility("ffplay")
    directory = _fresh_directory(args.get("output_dir"))
    staged = _stage_srt(subtitle, directory)
    vf = f"setpts=PTS-({_origin(data):.9f})/TB,subtitles=filename={SAFE_SRT_NAME}"
    command = [player, "-hide_banner", "-loglevel", "warning", "-autoexit", "-ss", f"{start:.9f}",
               "-t", f"{duration:.9f}", "-ast", str(stream["index"]), "-vst", str(video["index"]),
               "-vf", vf, "-window_title", "Hebrew subtitle review", str(source)]
    log_path = directory / "player.log"
    try:
        with log_path.open("xb") as log:
            process = subprocess.Popen(command, cwd=directory, stdout=subprocess.DEVNULL, stderr=log,
                                       shell=False, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0)
    except OSError as exc:
        raise MediaToolError(f"Could not open ffplay: {exc}") from exc
    result = {"status": "LAUNCH_REQUESTED", "pid": process.pid, "command": command, "player_log": str(log_path),
              "source": _identifier(source), "exact_subtitle": _identifier(subtitle, True),
              "staged_subtitle": _identifier(staged, True), "audio_stream_index": stream["index"],
              "requested_interval": [start, start + duration], "transformation_ledger": _ledger(data),
              "requested_player_offset_seconds": 0, "observed_player_offset_seconds": None,
              "final_playback_status": "NOT_VERIFIED",
              "continuous_watch_status": "NOT_VERIFIED", "video_encoding_performed": False,
              "limitations": ["Launching a player proves neither viewing nor successful rendering; record actual reviewer evidence separately."]}
    manifest = directory / "player_launch.json"
    _write_json(manifest, result)
    result["manifest_path"] = str(manifest)
    return result


def _ocr(path, language, psm):
    result = _run([_utility("tesseract"), str(path), "stdout", "-l", language, "--psm", str(psm), "tsv"], timeout=45)
    words = []
    for row in csv.DictReader(io.StringIO(result.stdout), delimiter="\t"):
        text = (row.get("text") or "").strip()
        if not text:
            continue
        try:
            score = float(row["conf"])
            box = {key: int(row[key]) for key in ("left", "top", "width", "height")}
        except (KeyError, TypeError, ValueError):
            continue
        words.append({"text": text, "confidence_0_to_100": score if score >= 0 else None, "box_pixels": box})
    scores = [word["confidence_0_to_100"] for word in words if word["confidence_0_to_100"] is not None]
    return {"text_candidate": " ".join(word["text"] for word in words), "words": words,
            "median_model_confidence_0_to_100": statistics.median(scores) if scores else None,
            "status": "REVIEW", "confidence_is_calibrated_accuracy": False}


def scan_screen_text(args):
    source = _file(args.get("media_path"), "media_path")
    data, _ = _probe(source)
    video = _video(data, args)
    start, duration = _range(args, data, MAX_SCAN_SECONDS)
    maximum = _integer(args.get("max_frames", 12), "max_frames", 2, MAX_FRAMES)
    threshold = _number(args.get("scene_threshold", 0.15), "scene_threshold", 0.001, 1)
    language = args.get("ocr_language", "eng")
    if not isinstance(language, str) or not re.fullmatch(r"[A-Za-z0-9_+]+", language):
        raise MediaToolError("Invalid Tesseract language identifier")
    psm = _integer(args.get("ocr_psm", 11), "ocr_psm", 3, 13)
    directory = _fresh_directory(args.get("output_dir"))
    command = _base_source_command(source, start, duration=duration)
    command += ["-map", f"0:{video['index']}", "-an", "-sn", "-dn", "-vf",
                f"select='gt(scene,{threshold:.6f})',showinfo", "-f", "null", "-"]
    cuts_raw = _pts(_run(command, timeout=180).stderr)
    cuts = [value - _origin(data) for value in cuts_raw if start <= value - _origin(data) < start + duration]
    fps = _fps(video)
    frame_step = 1 / fps if fps else 0.04
    # Half the budget gives distributed coverage, half gives before/after cuts.
    samples = max(2, maximum // 2)
    targets = [(start + duration * i / samples, "uniform_sample") for i in range(samples)]
    for cut in cuts:
        for when, kind in ((max(start, cut - frame_step - 0.0005), "before_candidate_cut"), (cut - 0.0005, "candidate_cut")):
            if start <= when < start + duration and len(targets) < maximum:
                targets.append((when, kind))
    ocr_requested = bool(args.get("ocr", True))
    ocr_available = bool(shutil.which("tesseract"))
    frames = []
    for index, (when, kind) in enumerate(targets):
        frame = _frame(source, data, video, when, directory / f"candidate_{index:03d}.png", directory)
        frame.update({"candidate_reason": kind, "status": "REVIEW", "ocr": None})
        if ocr_requested and ocr_available:
            try:
                frame["ocr"] = _ocr(Path(frame["path"]), language, psm)
            except MediaToolError as exc:
                frame["ocr"] = {"status": "NOT_VERIFIED", "error": str(exc)}
        frames.append(frame)
    result = {"status": "PARTIAL", "source": _identifier(source), "requested_interval": [start, start + duration],
              "scene_threshold": threshold, "candidate_cuts_source_media_seconds": cuts,
              "candidate_cuts_source_pts_seconds": cuts_raw, "shot_detection_command": command,
              "frames": frames, "frame_budget": maximum,
              "ocr": {"requested": ocr_requested, "available": ocr_available, "language": language,
                      "missing_dependency": "tesseract" if ocr_requested and not ocr_available else None},
              "transformation_ledger": _ledger(data), "video_encoding_performed": False,
              "limitations": ["Candidates are not verified text, shot boundaries or readability edges.",
                              "Flashes, fades, camera motion and typing can cause false scene changes.",
                              "Sparse samples cannot establish complete disclosure order or missing text; inspect native frame neighbors.",
                              "The frame budget may omit candidates; this is not complete runtime coverage."],
              "continuous_watch_status": "NOT_VERIFIED"}
    manifest = directory / "screen_text_candidates.json"
    _write_json(manifest, result)
    result["manifest_path"] = str(manifest)
    return result


def _clean_speech(text, strip_sdh):
    text = re.sub(r"\{[^}]*\}|<[^>]*>", "", text)
    if "♪" in text or "♫" in text:
        return "", "MUSIC_REQUIRES_SEPARATE_REVIEW"
    if strip_sdh:
        text = re.sub(r"(?m)^\s*(?:[-–—]\s*)?[A-Z][A-Z\s.'’\-]{1,60}:\s*", "", text)
        text = re.sub(r"\([^)]*\)|\[[^]]*\]", "", text)
        text = re.sub(r"[\[(][^\])]*$", "", text)
    text = re.sub(r"(?m)^\s*[-–—]\s*", "", text)
    return " ".join(text.split()), None


def _local_model(value):
    if not isinstance(value, str) or not value.strip():
        return None
    _reject_remote(value, "local_model_path")
    path = Path(value).expanduser().resolve()
    _reject_remote(path, "local_model_path")
    if not path.is_dir() or not (path / "config.json").is_file():
        return None
    weights = list(path.glob("*.safetensors")) + list(path.glob("pytorch_model*.bin"))
    return path if weights else None


def align_source_speech(args):
    """Forced alignment of corrected source SRT, not ASR or automatic clock repair."""
    source = _file(args.get("media_path"), "media_path")
    corrected = _file(args.get("corrected_source_srt"), "corrected_source_srt")
    cues = _read_srt(corrected)
    data, _ = _probe(source)
    audio_stream = _stream(data, args.get("audio_stream_index"), "audio")
    start, duration = _range(args, data, MAX_ALIGNMENT_SECONDS)
    missing = [name for name in ("whisperx", "torch", "transformers", "nltk") if not _package_available(name)]
    model = _local_model(args.get("local_model_path"))
    if model is None:
        missing.append("local HuggingFace CTC model directory (config, tokenizer/processor and weights)")
    if missing:
        return {"status": "NOT_VERIFIED", "missing_dependencies": missing,
                "automatic_install_or_download": False, "source": _identifier(source),
                "corrected_source_srt": _identifier(corrected, True), "output_created": False,
                "reason": "Optional alignment requires installed packages and an explicit local model; core review tools remain available."}
    language = args.get("language", "en")
    if not isinstance(language, str) or not re.fullmatch(r"[a-z]{2,3}", language):
        raise MediaToolError("language must be a source-language code")
    device = args.get("device", "cpu")
    if device not in ("cpu", "cuda"):
        raise MediaToolError("device must be cpu or cuda")
    threshold = _number(args.get("review_score_below", 0.5), "review_score_below", 0, 1)
    timeout = _integer(args.get("timeout_seconds", 1800), "timeout_seconds", 10, 7200)
    directory = _fresh_directory(args.get("output_dir"))
    staged = directory / "corrected_source.srt"
    with corrected.open("rb") as original, staged.open("xb") as target:
        shutil.copyfileobj(original, target)
    audio = _audio(source, data, audio_stream, start, duration, directory / "alignment_audio.wav", directory)
    zero = audio["audio_zero_source_media_seconds"]
    selected, omitted = [], []
    for cue in cues:
        if cue["end"] <= start or cue["start"] >= start + duration:
            continue
        cleaned, reason = _clean_speech(cue["text"], bool(args.get("strip_sdh", True)))
        if not cleaned:
            omitted.append({**cue, "reason": reason or "NO_SPOKEN_TEXT", "status": "REVIEW"})
            continue
        lower, upper = max(0, cue["start"] - zero - 0.35), min(audio["duration_seconds"], cue["end"] - zero + 0.35)
        if upper <= lower:
            omitted.append({**cue, "reason": "OUTSIDE_EXTRACTED_AUDIO", "status": "REVIEW"})
            continue
        selected.append({**cue, "normalized_source_text": cleaned,
                         "normalization_changed_text": cleaned != cue["text"],
                         "alignment_start": lower, "alignment_end": upper,
                         "range_clipped": cue["start"] < start or cue["end"] > start + duration})
    if not selected:
        result = {"status": "NOT_VERIFIED", "error": "NO_SPOKEN_CUES_IN_RANGE", "omitted_events": omitted,
                  "audio": audio, "transformation_ledger": _ledger(data, audio)}
        _write_json(directory / "alignment_report.json", result)
        return result
    request = {"audio_path": audio["path"], "model_path": str(model), "language": language,
               "device": device, "cues": selected, "audio_zero_source_media_seconds": zero,
               "review_score_below": threshold, "result_path": str(directory / "aligned_words.json")}
    request_path = directory / "alignment_request.json"
    _write_json(request_path, request)
    env = os.environ.copy()
    env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "HF_DATASETS_OFFLINE": "1",
                "TOKENIZERS_PARALLELISM": "false"})
    command = [sys.executable, str(Path(__file__).resolve()), "--align-worker", str(request_path)]
    try:
        _run(command, cwd=directory, timeout=timeout, env=env)
        worker = json.loads(Path(request["result_path"]).read_text(encoding="utf-8"))
    except (MediaToolError, OSError, json.JSONDecodeError) as exc:
        worker = {"status": "NOT_VERIFIED", "error": str(exc), "cue_alignments": []}
    result = {"status": worker.get("status", "PARTIAL"), "method": "WhisperX local forced alignment",
              "source": _identifier(source), "corrected_source_srt": _identifier(corrected, True),
              "staged_corrected_source_srt": _identifier(staged, True), "audio": audio,
              "local_model_path": str(model), "language": language, "device": device,
              "automatic_install_or_download": False, "selected_audio_stream": audio_stream,
              "requested_interval": [start, start + duration], "transformation_ledger": _ledger(data, audio),
              "cue_alignments": worker.get("cue_alignments", []), "worker_error": worker.get("error"),
              "omitted_or_unaligned_events": omitted, "runtime_versions": worker.get("runtime_versions", {}),
              "coverage": {"selected_spoken_cues": len(selected), "returned_cues": len(worker.get("cue_alignments", [])),
                           "omitted_events": len(omitted), "directly_verified_cues": 0},
              "speech_synchronization_status": "PARTIAL" if worker.get("cue_alignments") else "NOT_VERIFIED",
              "final_playback_status": "NOT_VERIFIED", "continuous_watch_status": "NOT_VERIFIED",
              "video_encoding_performed": False, "automatic_subtitle_clock_changes": False,
              "limitations": ["Alignment scores are model evidence, not calibrated accuracy or exact audible edges.",
                              "Interpolated or unscored words require review; dialogue association and corrected text must be verified.",
                              "Every result remains unverified until direct audiovisual and exact-deliverable checks are recorded."]}
    report = directory / "alignment_report.json"
    _write_json(report, result)
    result["report_path"] = str(report)
    return result


def _alignment_worker(request_path):
    request = json.loads(Path(request_path).read_text(encoding="utf-8"))

    def no_network(*args, **kwargs):
        raise RuntimeError("Offline alignment: network/download disabled; provide dependencies locally")

    # Prevent both model and auxiliary-data downloads in the child, not the MCP process.
    socket.socket.connect = no_network
    socket.socket.connect_ex = no_network
    socket.create_connection = no_network
    import nltk
    nltk.download = no_network
    import whisperx
    import whisperx.alignment as alignment
    import numpy as np
    import importlib.metadata
    kwargs = {"language_code": request["language"], "device": request["device"],
              "model_name": request["model_path"], "model_dir": request["model_path"]}
    if "model_cache_only" in inspect.signature(alignment.load_align_model).parameters:
        kwargs["model_cache_only"] = True
    model, metadata = alignment.load_align_model(**kwargs)
    with wave.open(request["audio_path"], "rb") as source:
        if source.getsampwidth() != 2 or source.getnchannels() != 1 or source.getframerate() != 16000:
            raise RuntimeError("Alignment audio must be mono PCM16 16kHz")
        audio = np.frombuffer(source.readframes(source.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
    rows = []
    zero = request["audio_zero_source_media_seconds"]
    for cue in request["cues"]:
        result = alignment.align([{"start": cue["alignment_start"], "end": cue["alignment_end"],
                                   "text": cue["normalized_source_text"]}], model, metadata, audio,
                                 request["device"], interpolate_method="ignore", return_char_alignments=False)
        words = []
        for word in result.get("word_segments", []):
            def finite(key):
                value = word.get(key)
                return float(value) if value is not None and math.isfinite(float(value)) else None
            lower, upper, score = finite("start"), finite("end"), finite("score")
            words.append({"word": word.get("word", ""), "raw_audio_start_seconds": lower,
                          "raw_audio_end_seconds": upper, "source_start_seconds": lower + zero if lower is not None else None,
                          "source_end_seconds": upper + zero if upper is not None else None,
                          "model_score": score, "status": "NOT_VERIFIED",
                          "requires_review": score is None or score < request["review_score_below"] or lower is None or upper is None})
        timed = [word for word in words if word["source_start_seconds"] is not None and word["source_end_seconds"] is not None]
        scores = [word["model_score"] for word in words if word["model_score"] is not None]
        first = min((word["source_start_seconds"] for word in timed), default=None)
        last = max((word["source_end_seconds"] for word in timed), default=None)
        rows.append({"cue_id": cue["cue_id"], "source_text": cue["text"],
                     "normalized_source_text": cue["normalized_source_text"], "original_start_seconds": cue["start"],
                     "original_end_seconds": cue["end"], "range_clipped": cue["range_clipped"], "words": words,
                     "candidate_first_word_seconds": first, "candidate_last_word_seconds": last,
                     "candidate_signed_onset_error_seconds": cue["start"] - first if first is not None else None,
                     "candidate_signed_offset_error_seconds": cue["end"] - last if last is not None else None,
                     "mean_model_score": statistics.mean(scores) if scores else None,
                     "confidence_is_calibrated_accuracy": False, "status": "NOT_VERIFIED",
                     "requires_review": True})
    versions = {}
    for name in ("whisperx", "torch", "transformers", "nltk"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "unknown"
    _write_json(Path(request["result_path"]), {"status": "PARTIAL", "cue_alignments": rows, "runtime_versions": versions})


def _schema(properties, required):
    return {"type": "object", "properties": properties, "required": required, "additionalProperties": False}


MEDIA = {"media_path": {"type": "string", "description": "Existing local media file; no URL."},
         "output_dir": {"type": "string", "description": "Fresh local directory. Existing output is refused."},
         "start_seconds": {"type": "number", "minimum": 0, "description": "Source playback seconds relative to format start_time."},
         "duration_seconds": {"type": "number", "exclusiveMinimum": 0},
         "video_stream_index": {"type": "integer", "minimum": 0, "description": "Absolute ffprobe stream index; defaults to first actual video."}}
AUDIO = {"audio_stream_index": {"type": "integer", "minimum": 0, "description": "Required absolute ffprobe audio stream index; language is never guessed."}}
SIDE = {"subtitle_path": {"type": "string", "description": "Exact local UTF-8 SRT to load without shifting or rewriting."}}
READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
LOCAL_WRITE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}
TOOLS = {
    "media_capabilities": {"description": "Inspect local FFmpeg/player/OCR and optional alignment dependencies. Never installs, downloads, plays media or approves QC.", "inputSchema": _schema({}, []), "handler": media_capabilities, "annotations": READ_ONLY},
    "probe_media": {"description": "Probe local media streams and source time reference using ffprobe; does not establish sync or watch status.", "inputSchema": _schema({"media_path": MEDIA["media_path"], "hash_source": {"type": "boolean", "default": False}}, ["media_path"]), "handler": probe_media, "annotations": READ_ONLY},
    "prepare_review_segment": {"description": "Generate bounded original/rendered PNGs and selected-stream WAV with measured source PTS and exact SRT hash. No video encoding or player launch. Evidence remains PARTIAL.", "inputSchema": _schema({**MEDIA, **AUDIO, **SIDE, "frame_count": {"type": "integer", "minimum": 1, "maximum": 24, "default": 3}, "frame_times_seconds": {"type": "array", "minItems": 1, "maxItems": 24, "items": {"type": "number", "minimum": 0}}, "include_media": {"type": "boolean", "default": False}}, ["media_path", "output_dir", "start_seconds", "duration_seconds", "audio_stream_index", "subtitle_path"]), "handler": prepare_review_segment, "annotations": LOCAL_WRITE},
    "play_review": {"description": "Explicitly open a bounded interactive ffplay window with the selected audio stream and exact SRT. Max180 seconds. Launching never marks playback/full-watch PASS.", "inputSchema": _schema({**MEDIA, **AUDIO, **SIDE}, ["media_path", "output_dir", "start_seconds", "duration_seconds", "audio_stream_index", "subtitle_path"]), "handler": play_review, "annotations": LOCAL_WRITE},
    "scan_screen_text": {"description": "Produce bounded native-PTS frame/shot candidates and optional installed Tesseract OCR. Candidates and model scores remain REVIEW; no model download or truth/readability claim.", "inputSchema": _schema({**MEDIA, "max_frames": {"type": "integer", "minimum": 2, "maximum": 24, "default": 12}, "scene_threshold": {"type": "number", "minimum": 0.001, "maximum": 1, "default": 0.15}, "ocr": {"type": "boolean", "default": True}, "ocr_language": {"type": "string", "default": "eng"}, "ocr_psm": {"type": "integer", "minimum": 3, "maximum": 13, "default": 11}}, ["media_path", "output_dir", "start_seconds", "duration_seconds"]), "handler": scan_screen_text, "annotations": LOCAL_WRITE},
    "align_source_speech": {"description": "Optional offline WhisperX forced-alignment adapter for corrected source SRT and explicit audio stream/local model. Installed packages and model required; no ASR, installation, network, automatic clock repair or verification PASS.", "inputSchema": _schema({**MEDIA, **AUDIO, "corrected_source_srt": {"type": "string"}, "local_model_path": {"type": "string", "description": "Prepared local HuggingFace CTC model directory, not a remote model ID."}, "language": {"type": "string", "default": "en"}, "device": {"type": "string", "enum": ["cpu", "cuda"], "default": "cpu"}, "strip_sdh": {"type": "boolean", "default": True}, "review_score_below": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.5}, "timeout_seconds": {"type": "integer", "minimum": 10, "maximum": 7200, "default": 1800}}, ["media_path", "output_dir", "start_seconds", "duration_seconds", "audio_stream_index", "corrected_source_srt", "local_model_path"]), "handler": align_source_speech, "annotations": LOCAL_WRITE},
}


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--align-worker":
        _alignment_worker(sys.argv[2])
    else:
        raise SystemExit("This module is invoked through MCP tool handlers, or --align-worker REQUEST_JSON.")
