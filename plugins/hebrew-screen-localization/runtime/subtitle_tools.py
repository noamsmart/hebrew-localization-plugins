"""Local, standard-library subtitle tools. No media, network or translation writes.

Clock values in JSON files are integer milliseconds. Cue files are arrays of
{id, start, end, text}; source_ids is optional for explicit ledger mapping.
Coverage ledgers are arrays of {id, start, end, decision, target_text,
target_ids?, reason?}. target_text is the approved, line-broken target display
for selected events, not a machine judgment of translation quality.
"""

from __future__ import annotations

import collections
import hashlib
import html
import json
import math
import os
from pathlib import Path
import re
import tempfile
import unicodedata


RLM = "\u200f"
_STAMP = re.compile(r"^([0-9]{2,}):([0-5][0-9]):([0-5][0-9]),([0-9]{3})$")
_TIMING = re.compile(r"^([0-9]{2,}:[0-5][0-9]:[0-5][0-9],[0-9]{3}) --> ([0-9]{2,}:[0-5][0-9]:[0-5][0-9],[0-9]{3})$")
_HTML = re.compile(r"</?(?:i|b|u|s|font)(?:\s+[^<>]*)?>", re.IGNORECASE)
_ASS_POSITION = re.compile(r"\{\\an[1-9]\}")
_BIDI = frozenset("\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069")
_MAX_BYTES = 50 * 1024 * 1024
DEFAULT_LIMITS = {"max_lines": 2, "max_line_characters": 42, "max_cps": 20.0,
                  "min_duration_ms": 833, "max_duration_ms": 7000, "min_gap_ms": 0}


def _issue(code, severity="error", cue_id=None, **details):
    item = {"code": code, "severity": severity}
    if cue_id is not None:
        item["cue_id"] = cue_id
    item.update(details)
    return item


def _path(value):
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ValueError("A nonempty local filesystem path is required.")
    if "://" in value or value.startswith(("\\\\", "//")):
        raise ValueError("Only local filesystem paths are supported; URLs and UNC paths are rejected.")
    path = Path(value).expanduser().resolve()
    if str(path).startswith(("\\\\", "//")):
        raise ValueError("Resolved path must be local, not UNC.")
    return path


def _read_bytes(path):
    if path.stat().st_size > _MAX_BYTES:
        raise ValueError("Input exceeds the 50 MiB local-file limit.")
    return path.read_bytes()


def _read_json(path):
    data = json.loads(_read_bytes(path).decode("utf-8-sig"))
    if not isinstance(data, list):
        raise ValueError("JSON input must be an array.")
    return data


def _ms(value):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError("Clock values must be nonnegative integer milliseconds.")
    return value


def _stamp_ms(value):
    match = _STAMP.fullmatch(value)
    if not match:
        raise ValueError("Invalid SRT timestamp: " + value)
    hours, minutes, seconds, millis = map(int, match.groups())
    return hours * 3600000 + minutes * 60000 + seconds * 1000 + millis


def _format_ms(value, separator=","):
    hours, remainder = divmod(_ms(value), 3600000)
    minutes, remainder = divmod(remainder, 60000)
    seconds, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}{separator}{millis:03d}"


def logical_text(text):
    """Remove presentation RLM marks; never reverse Hebrew characters."""
    if not isinstance(text, str):
        raise ValueError("Subtitle text must be a string.")
    return text.replace("\r\n", "\n").replace(RLM, "")


def visible_lines(text):
    text = _ASS_POSITION.sub("", _HTML.sub("", logical_text(text)))
    return html.unescape(text).split("\n")


def _visible_length(text):
    # Combining vowel/cantillation marks and bidi controls are not printed glyphs.
    return sum(not unicodedata.combining(ch) and ch not in _BIDI for ch in text)


def parse_srt(raw):
    """Strict UTF-8 SRT parser retaining valid cues and reporting every error."""
    result = {"cues": [], "issues": [], "utf8_bom": raw.startswith(b"\xef\xbb\xbf"),
              "newline_style": "CRLF" if b"\r\n" in raw else "LF"}
    try:
        text = raw.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        result["issues"].append(_issue("invalid_utf8", byte_offset=exc.start))
        return result
    if "\ufeff" in text or "\x00" in text or "\ufffd" in text:
        result["issues"].append(_issue("invalid_text_control", detail="Embedded BOM, NUL or replacement character."))
    if re.search(r"\r(?!\n)", text):
        result["issues"].append(_issue("bare_carriage_return"))
    if "\r\n" in text and re.search(r"(?<!\r)\n", text):
        result["issues"].append(_issue("mixed_newlines", "warning"))
    normalized = text.replace("\r\n", "\n").rstrip("\n")
    if not normalized:
        result["issues"].append(_issue("empty_subtitle_file"))
        return result
    blocks = normalized.split("\n\n")
    for expected, block in enumerate(blocks, 1):
        lines = block.split("\n")
        if len(lines) < 3 or not re.fullmatch(r"[0-9]+", lines[0]) or not _TIMING.fullmatch(lines[1]):
            result["issues"].append(_issue("invalid_srt_block", block=expected))
            continue
        index = int(lines[0])
        if lines[0] != str(expected):
            result["issues"].append(_issue("nonsequential_index", cue_id=index, expected=expected))
        start, end = (_stamp_ms(part) for part in _TIMING.fullmatch(lines[1]).groups())
        cue_text = "\n".join(lines[2:])
        for position in range(3, len(lines)):
            if _TIMING.fullmatch(lines[position]) and re.fullmatch(r"[0-9]+", lines[position - 1]):
                result["issues"].append(_issue("missing_block_separator", cue_id=index, line=position + 1))
        if any(not line.strip(RLM).strip() for line in lines[2:]):
            result["issues"].append(_issue("empty_text_line", cue_id=index))
        if end <= start:
            result["issues"].append(_issue("nonpositive_duration", cue_id=index, start=start, end=end))
        for number, line in enumerate(lines[2:], 1):
            marks = line.count(RLM)
            if marks and not (marks == 2 and line.startswith(RLM) and line.endswith(RLM)):
                result["issues"].append(_issue("unexpected_rlm_placement", "warning", index, line=number))
            other = sorted(set(line) & (_BIDI - {RLM}))
            if other:
                result["issues"].append(_issue("other_bidi_controls", "warning", index,
                                               line=number, codepoints=[f"U+{ord(ch):04X}" for ch in other]))
        result["cues"].append({"id": index, "start": start, "end": end,
                                "text": logical_text(cue_text)})
    _clock_issues(result["cues"], result["issues"])
    return result


def _clock_issues(cues, issues):
    previous_start = -1
    active = []
    for cue in cues:
        if cue["start"] < previous_start:
            issues.append(_issue("out_of_order", cue_id=cue["id"]))
        previous_start = cue["start"]
        active = [other for other in active if other["end"] > cue["start"]]
        for other in active:
            if other["start"] < cue["end"] and cue["start"] < other["end"]:
                issues.append(_issue("overlap", cue_id=cue["id"], other_cue_id=other["id"],
                                     overlap_ms=min(cue["end"], other["end"]) - max(cue["start"], other["start"])))
        active.append(cue)


def _json_cues(items):
    cues = []
    identifiers = set()
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict):
            raise ValueError("Every cue must be an object.")
        identity = item.get("id", item.get("base_id", index))
        if isinstance(identity, bool) or not isinstance(identity, (str, int)) or str(identity) in identifiers:
            raise ValueError("Cue IDs must be unique string or integer identifiers.")
        identifiers.add(str(identity))
        start, end = _ms(item.get("start")), _ms(item.get("end"))
        text = logical_text(item.get("text"))
        if end <= start or not text.strip() or "\r" in text or any(not line.strip() for line in text.split("\n")):
            raise ValueError("Each cue needs a positive clock window and nonempty subtitle lines.")
        if any(ch in text for ch in ("\x00", "\ufeff", "\ufffd")):
            raise ValueError("Cue text contains an invalid control or replacement character.")
        cue = {"id": identity, "start": start, "end": end, "text": text}
        if "source_ids" in item:
            if not isinstance(item["source_ids"], list) or any(isinstance(x, bool) or not isinstance(x, (int, str)) for x in item["source_ids"]):
                raise ValueError("source_ids must contain string/integer source IDs.")
            cue["source_ids"] = item["source_ids"]
        if "reading_new_characters" in item:
            count = item["reading_new_characters"]
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                raise ValueError("reading_new_characters must be a nonnegative integer.")
            if not item.get("reading_exception"):
                raise ValueError("An incremental reading count requires a documented reading_exception.")
            if count > sum(_visible_length(line) for line in visible_lines(text)):
                raise ValueError("Incremental reading count exceeds the complete visible text.")
            cue["reading_new_characters"] = count
            cue["reading_exception"] = str(item["reading_exception"])
        cues.append(cue)
    return cues


def _load_cues(path):
    if path.suffix.lower() == ".srt":
        parsed = parse_srt(_read_bytes(path))
        errors = [issue for issue in parsed["issues"] if issue["severity"] == "error"]
        if errors:
            raise ValueError("Target SRT has structural errors: " + ", ".join(issue["code"] for issue in errors))
        return parsed["cues"]
    if path.suffix.lower() != ".json":
        raise ValueError("Cue input must be .json or .srt.")
    return _json_cues(_read_json(path))


def _limits(args):
    limits = dict(DEFAULT_LIMITS)
    if args.get("profile", "adult") == "children":
        limits["max_cps"] = 17.0
    limits.update(args.get("limits", {}))
    if limits["min_duration_ms"] > limits["max_duration_ms"]:
        raise ValueError("Minimum duration cannot exceed maximum duration.")
    return limits


def _measure(cues, limits):
    metrics = []
    issues = []
    previous = None
    for cue in cues:
        lines = visible_lines(cue["text"])
        lengths = [_visible_length(line) for line in lines]
        duration = cue["end"] - cue["start"]
        characters = sum(lengths)
        reading_chars = cue.get("reading_new_characters", characters)
        cps = characters * 1000.0 / duration if duration > 0 else None
        reading_cps = reading_chars * 1000.0 / duration if duration > 0 else None
        metric = {"id": cue["id"], "start": cue["start"], "end": cue["end"],
                  "duration_ms": duration, "visible_characters": characters,
                  "line_characters": lengths, "line_count": len(lines),
                  "cps": round(cps, 4) if cps is not None else None,
                  "reading_cps": round(reading_cps, 4) if reading_cps is not None else None}
        if "reading_exception" in cue:
            metric["reading_exception"] = cue["reading_exception"]
            metric["reading_new_characters"] = reading_chars
        tests = [(len(lines) > limits["max_lines"], "too_many_lines"),
                 (max(lengths, default=0) > limits["max_line_characters"], "line_too_long"),
                 (reading_cps is not None and reading_cps > limits["max_cps"] + 1e-9, "fast_cps"),
                 (duration < limits["min_duration_ms"], "short_duration"),
                 (duration > limits["max_duration_ms"], "long_duration")]
        for failed, code in tests:
            if failed:
                issues.append(_issue(code, "warning", cue["id"], start=cue["start"], end=cue["end"], metrics=metric))
        if previous is not None:
            gap = cue["start"] - previous["end"]
            metric["previous_gap_ms"] = gap
            if 0 <= gap < limits["min_gap_ms"]:
                issues.append(_issue("short_gap", "warning", cue["id"], gap_ms=gap))
        metrics.append(metric)
        previous = cue
    return metrics, issues


def _inspect(args):
    path = _path(args["subtitle_path"])
    if path.suffix.lower() != ".srt":
        raise ValueError("inspect_subtitles currently accepts strict UTF-8 SRT.")
    raw = _read_bytes(path)
    parsed = parse_srt(raw)
    limits = _limits(args)
    metrics, readability = _measure(parsed["cues"], limits)
    errors = [item for item in parsed["issues"] if item["severity"] == "error"]
    result = {"subtitle_path": str(path), "sha256": hashlib.sha256(raw).hexdigest(),
              "structure_status": "FAIL" if errors else "PASS",
              "readability_status": "REVIEW" if readability else ("PASS" if not errors else "NOT_EVALUATED"),
              "synchronization_status": "NOT_VERIFIED", "translation_quality_status": "NOT_EVALUATED",
              "scope": "File structure and measurable readability only; source audio, visual context and player rendering were not verified.",
              "utf8_bom": parsed["utf8_bom"], "newline_style": parsed["newline_style"],
              "cue_count": len(parsed["cues"]), "limits": limits,
              "maximum_line_count": max((m["line_count"] for m in metrics), default=0),
              "maximum_line_characters": max((max(m["line_characters"], default=0) for m in metrics), default=0),
              "maximum_cps": max((m["reading_cps"] for m in metrics if m["reading_cps"] is not None), default=0),
              "issues": parsed["issues"] + readability}
    if args.get("include_cues", True):
        result["cues"] = [dict(cue, metrics=metric) for cue, metric in zip(parsed["cues"], metrics)]
    return result


def _write(path, raw, overwrite=False, protected=()):
    for source in protected:
        if os.path.normcase(str(path)) == os.path.normcase(str(source)):
            raise ValueError("Output cannot overwrite an input or protected source path.")
        if path.exists() and source.exists() and os.path.samefile(path, source):
            raise ValueError("Output aliases an input or protected source file.")
    if path.exists() and not overwrite:
        raise FileExistsError("Output already exists; choose a new path or explicitly set overwrite=true.")
    if not path.parent.is_dir():
        raise ValueError("Output parent directory must already exist.")
    if not overwrite:
        # Exclusive creation also rejects a destination created after the check.
        with path.open("xb") as stream:
            stream.write(raw)
    else:
        handle, temporary = tempfile.mkstemp(prefix=".subtitle-export-", dir=str(path.parent))
        try:
            with os.fdopen(handle, "wb") as stream:
                stream.write(raw)
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)


def _export(args):
    limits = _limits(args)
    source = _path(args["cue_path"])
    output = _path(args["output_path"])
    format_name = args.get("format", "srt")
    suffixes = (".srt",) if format_name == "srt" else (".vtt", ".webvtt")
    if output.suffix.lower() not in suffixes:
        raise ValueError("Output extension must match the selected SRT/WebVTT format.")
    cues = _load_cues(source)
    issues = []
    _clock_issues(cues, issues)
    if issues:
        raise ValueError("Export refuses invalid ordering or overlapping cues; resolve composite presentation explicitly.")
    if not cues:
        raise ValueError("Export requires at least one cue.")
    lines = ["WEBVTT", ""] if format_name == "webvtt" else []
    use_marks = args.get("rtl_marks", False)
    for index, cue in enumerate(cues, 1):
        display = cue["text"].split("\n")
        if format_name == "webvtt" and any("-->" in line for line in display):
            raise ValueError("WebVTT payload cannot contain a timing arrow.")
        # Keep logical character order. Presentation marks are per line only.
        if use_marks:
            display = [RLM + line + RLM for line in display]
        separator = "," if format_name == "srt" else "."
        lines.extend([str(index), _format_ms(cue["start"], separator) + " --> " + _format_ms(cue["end"], separator), *display, ""])
    encoded = ("\r\n".join(lines) + "\r\n").encode("utf-8")
    if args.get("utf8_bom", False):
        encoded = b"\xef\xbb\xbf" + encoded
    protected = [source, *(_path(value) for value in args.get("protected_paths", []))]
    _write(output, encoded, args.get("overwrite", False), protected)
    metrics, readability = _measure(cues, limits)
    return {"status": "EXPORTED", "output_path": str(output), "format": format_name,
            "sha256": hashlib.sha256(encoded).hexdigest(), "cue_count": len(cues),
            "clock_policy": "Every input clock preserved exactly; no shift, drift repair, splitting or merging.",
            "cue_id_map": [{"source_id": cue["id"], "output_id": index} for index, cue in enumerate(cues, 1)],
            "rtl_marks": use_marks, "structure_status": "PASS",
            "readability_status": "REVIEW" if readability else "PASS", "readability_issues": readability,
            "synchronization_status": "NOT_VERIFIED", "translation_quality_status": "NOT_EVALUATED",
            "rendering_status": "NOT_VERIFIED", "source_media_modified": False}


_DECISIONS = {"selected": "selected", "translate": "selected", "omitted": "omitted",
              "omit": "omitted", "review": "review", "review-in-context": "review"}


def _ledger(items):
    events = []
    identifiers = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Every ledger event must be an object.")
        identity = item.get("id")
        if isinstance(identity, bool) or not isinstance(identity, (str, int)) or str(identity) in identifiers:
            raise ValueError("Ledger IDs must be unique strings or integers.")
        identifiers.add(str(identity))
        decision = _DECISIONS.get(str(item.get("decision", "")).lower())
        if decision is None:
            raise ValueError("Ledger decision must be selected, omitted, review or TRANSLATE/OMIT/REVIEW-IN-CONTEXT.")
        start, end = _ms(item.get("start")), _ms(item.get("end"))
        if end <= start:
            raise ValueError("Ledger events require positive source clock windows.")
        event = dict(item, id=identity, start=start, end=end, decision=decision)
        if "target_text" in event:
            event["target_text"] = logical_text(event["target_text"])
        if "target_ids" in event and (not isinstance(event["target_ids"], list) or any(isinstance(x, bool) or not isinstance(x, (int, str)) for x in event["target_ids"])):
            raise ValueError("target_ids must be an array of string/integer cue IDs.")
        events.append(event)
    return events


def _counter_at(windows, stamp):
    return collections.Counter(line for window in windows if window["start"] <= stamp < window["end"]
                               for line in visible_lines(window["text"]))


def _coverage(args):
    ledger_path = _path(args["source_events_path"])
    target_path = _path(args["target_path"])
    events = _ledger(_read_json(ledger_path))
    targets = _load_cues(target_path)
    issues = []
    mappings = []
    selected = []
    unresolved = []
    target_by_id = {str(cue["id"]): cue for cue in targets}
    for event in events:
        explicit = event.get("target_ids", [])
        mapped = [target_by_id[str(identity)] for identity in explicit if str(identity) in target_by_id]
        for identity in explicit:
            if str(identity) not in target_by_id:
                issues.append(_issue("unknown_target_id", event_id=event["id"], target_id=identity))
        source_mapped = [cue for cue in targets if str(event["id"]) in {str(x) for x in cue.get("source_ids", [])}]
        mapped = list({str(cue["id"]): cue for cue in mapped + source_mapped}.values())
        if event["decision"] == "omitted":
            if mapped:
                issues.append(_issue("omitted_event_emitted", event_id=event["id"], target_ids=[c["id"] for c in mapped]))
            if not event.get("reason"):
                issues.append(_issue("omission_reason_missing", "warning", event_id=event["id"]))
        elif event["decision"] == "review":
            unresolved.append(event["id"])
            issues.append(_issue("unresolved_selection", "warning", event_id=event["id"]))
        else:
            text = event.get("target_text")
            if not text or not text.strip():
                unresolved.append(event["id"])
                issues.append(_issue("approved_target_text_missing", "warning", event_id=event["id"]))
            else:
                selected.append({"id": event["id"], "start": event["start"], "end": event["end"], "text": text})
                wanted = collections.Counter(visible_lines(text))
                inferred = [cue for cue in targets if cue["start"] < event["end"] and cue["end"] > event["start"]
                            and not (wanted - collections.Counter(visible_lines(cue["text"])))]
                if not mapped:
                    mapped = inferred
                if explicit or source_mapped:
                    for cue in mapped:
                        if not (cue["start"] < event["end"] and cue["end"] > event["start"]):
                            issues.append(_issue("mapped_target_outside_event", event_id=event["id"], target_id=cue["id"]))
                    event_cuts = sorted({event["start"], event["end"],
                                         *(max(event["start"], min(event["end"], t))
                                           for cue in mapped for t in (cue["start"], cue["end"]))})
                    missing_intervals = []
                    for left, right in zip(event_cuts, event_cuts[1:]):
                        missing = wanted - _counter_at(mapped, left)
                        if missing:
                            missing_intervals.append({"start": left, "end": right,
                                                      "missing_lines": list(missing.elements())})
                    if missing_intervals:
                        issues.append(_issue("mapped_event_coverage_mismatch", event_id=event["id"],
                                             intervals=missing_intervals))
        mappings.append({"source_id": event["id"], "decision": event["decision"],
                         "target_ids": [cue["id"] for cue in mapped],
                         "mapping_basis": "explicit_or_source_ids" if explicit or source_mapped else "text_and_window"})
    cuts = sorted({time for window in selected + targets for time in (window["start"], window["end"])})
    coverage_issues = []
    compared = 0
    for start, end in zip(cuts, cuts[1:]):
        expected = _counter_at(selected, start)
        actual = _counter_at(targets, start)
        if expected or actual:
            compared += 1
        if expected != actual:
            coverage_issues.append({"start": start, "end": end,
                                    "missing_lines": list((expected - actual).elements()),
                                    "extra_lines": list((actual - expected).elements())})
    if coverage_issues:
        issues.append(_issue("timeline_text_coverage_mismatch", intervals=len(coverage_issues)))
    _clock_issues(targets, issues)
    errors = [item for item in issues if item["severity"] == "error"]
    status = "FAIL" if errors else ("REVIEW" if unresolved or any(i["severity"] == "warning" for i in issues) else "PASS")
    return {"coverage_status": status, "source_events_path": str(ledger_path), "target_path": str(target_path),
            "source_event_count": len(events), "selected_count": sum(e["decision"] == "selected" for e in events),
            "omitted_count": sum(e["decision"] == "omitted" for e in events),
            "review_count": sum(e["decision"] == "review" for e in events), "target_cue_count": len(targets),
            "active_timeline_intervals_compared": compared, "source_target_mapping": mappings,
            "unresolved_source_ids": unresolved, "issues": issues, "coverage_mismatches": coverage_issues,
            "coverage_scope": "Exact approved visible target lines over ledger clock windows, including composites; omission checks use mappings and unmatched output text.",
            "synchronization_status": "NOT_VERIFIED", "translation_quality_status": "NOT_EVALUATED",
            "source_media_modified": False}


def _queue(args):
    limits = _limits(args)
    path = _path(args["review_items_path"])
    items = _read_json(path)
    queue = []
    seen = set()
    for ordinal, item in enumerate(items, 1):
        if not isinstance(item, dict):
            raise ValueError("Review items must be objects.")
        if item.get("resolved") is True:
            continue
        identity = item.get("id", ordinal)
        if isinstance(identity, bool) or not isinstance(identity, (int, str)) or str(identity) in seen:
            raise ValueError("Review item IDs must be unique strings or integers.")
        seen.add(str(identity))
        reasons = []
        score = 0
        confidence = item.get("confidence")
        if confidence is not None:
            if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
                raise ValueError("Confidence must be a finite number from 0 to 1.")
            if confidence < 0.85:
                reasons.append("low_confidence")
                score = max(score, 85 if confidence < 0.5 else 75)
        decision = item.get("decision", "")
        if not isinstance(decision, str):
            raise ValueError("Review decision must be a string.")
        if item.get("uncertainty") or decision.lower() in ("review", "review-in-context"):
            reasons.append("unresolved_uncertainty")
            score = max(score, 85)
        changes = item.get("source_target_changes", [])
        if changes:
            reasons.append("reported_source_target_changes")
            score = max(score, 90)
        if item.get("previous_target_text") is not None and logical_text(item["previous_target_text"]) != logical_text(item.get("target_text", "")):
            reasons.append("target_revision_requires_semantic_recheck")
            score = max(score, 80)
        checks = item.get("semantic_checks", {})
        if not isinstance(checks, dict):
            raise ValueError("semantic_checks must be an object of recorded review outcomes.")
        if any(value is False or str(value).lower() in ("fail", "review", "uncertain") for value in checks.values()):
            reasons.append("semantic_check_requires_review")
            score = max(score, 100)
        flags = item.get("flags", [])
        if not isinstance(flags, list) or any(not isinstance(flag, str) for flag in flags):
            raise ValueError("Review flags must be an array of strings.")
        if flags:
            reasons.extend(flags)
            score = max(score, 70)
        source = item.get("source_text")
        target = item.get("target_text")
        if isinstance(source, str) and isinstance(target, str):
            if re.findall(r"\d+", source) != re.findall(r"\d+", target):
                reasons.append("digit_changes_require_context_review")
                score = max(score, 75)
        linked = item.get("linked_visual_reactions", item.get("visual_reactions", []))
        if linked:
            reasons.append("inspect_linked_visual_reactions")
            score = max(score, 60)
        if "start" in item or "end" in item:
            start, end = _ms(item.get("start")), _ms(item.get("end"))
            if end <= start:
                raise ValueError("Review items require a positive clock window.")
            if target:
                cue = {"id": identity, "start": start, "end": end, "text": logical_text(target)}
                metric, measurement_issues = _measure([cue], limits)
                reasons.extend(issue["code"] for issue in measurement_issues)
                if any(issue["code"] == "fast_cps" for issue in measurement_issues):
                    score = max(score, 70)
                elif measurement_issues:
                    score = max(score, 55)
        else:
            start, end = None, None
        if reasons:
            queue.append({"id": identity, "start": start, "end": end, "priority_score": score,
                          "priority": "high" if score >= 80 else "medium" if score >= 55 else "low",
                          "reasons": list(dict.fromkeys(reasons)), "source_text": source,
                          "target_text": target, "uncertainty": item.get("uncertainty"),
                          "source_target_changes": changes, "semantic_checks": checks,
                          "linked_visual_reactions": linked,
                          "evidence": item.get("evidence", [])})
    if args.get("subtitle_path"):
        inspection = _inspect(dict(subtitle_path=args["subtitle_path"], profile=args.get("profile", "adult"), limits=args.get("limits", {})))
        cues = {str(cue["id"]): cue for cue in inspection["cues"]}
        for issue in inspection["issues"]:
            cue = cues.get(str(issue.get("cue_id")), {})
            score = 100 if issue["severity"] == "error" else 70 if issue["code"] == "fast_cps" else 55
            queue.append({"id": "subtitle:" + str(issue.get("cue_id", "file")) + ":" + issue["code"],
                          "start": cue.get("start"), "end": cue.get("end"), "priority_score": score,
                          "priority": "high" if score >= 80 else "medium", "reasons": [issue["code"]],
                          "target_text": cue.get("text"), "evidence": [issue], "linked_visual_reactions": []})
    queue.sort(key=lambda item: (-item["priority_score"], item["start"] if item["start"] is not None else -1, str(item["id"])))
    result = {"status": "REVIEW_REQUIRED" if queue else "NO_RECORDED_ITEMS", "item_count": len(queue),
              "items": queue, "translation_quality_status": "NOT_EVALUATED", "synchronization_status": "NOT_VERIFIED",
              "scope": "Prioritizes recorded uncertainty, revisions, numeric differences, timing warnings and linked visual reactions; does not infer complete semantic equivalence."}
    if args.get("output_path"):
        output = _path(args["output_path"])
        if output.suffix.lower() != ".json":
            raise ValueError("Review queue output must be .json.")
        protected = [path]
        if args.get("subtitle_path"):
            protected.append(_path(args["subtitle_path"]))
        _write(output, (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"), args.get("overwrite", False), protected)
        result["output_path"] = str(output)
    return result


def _validate(value, schema, label="arguments"):
    kind = schema.get("type")
    valid = {"object": lambda x: isinstance(x, dict), "array": lambda x: isinstance(x, list),
             "string": lambda x: isinstance(x, str), "boolean": lambda x: isinstance(x, bool),
             "integer": lambda x: isinstance(x, int) and not isinstance(x, bool),
             "number": lambda x: isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)}
    if kind and not valid[kind](value):
        raise ValueError(f"{label} must be {kind}.")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{label} must be one of {schema['enum']}.")
    if kind == "object":
        properties = schema.get("properties", {})
        missing = set(schema.get("required", [])) - set(value)
        unknown = set(value) - set(properties)
        if missing or (unknown and schema.get("additionalProperties") is False):
            raise ValueError(f"{label}: missing {sorted(missing)}; unsupported {sorted(unknown)}.")
        for key, item in value.items():
            if key in properties:
                _validate(item, properties[key], label + "." + key)
    elif kind == "array":
        for index, item in enumerate(value):
            _validate(item, schema.get("items", {}), f"{label}[{index}]")
    elif kind in ("integer", "number"):
        if value < schema.get("minimum", -math.inf) or value > schema.get("maximum", math.inf):
            raise ValueError(f"{label} is outside the allowed range.")
    elif kind == "string" and len(value) < schema.get("minLength", 0):
        raise ValueError(f"{label} is too short.")


def _handler(function, schema):
    def invoke(args):
        try:
            _validate(args, schema)
            return function(args)
        except (ValueError, OSError, UnicodeError, TypeError, KeyError) as exc:
            return {"status": "ERROR", "error_type": type(exc).__name__, "error": str(exc),
                    "synchronization_status": "NOT_VERIFIED", "translation_quality_status": "NOT_EVALUATED"}
    return invoke


_PATH = {"type": "string", "minLength": 1}
_LIMIT_SCHEMA = {"type": "object", "additionalProperties": False, "properties": {
    "max_lines": {"type": "integer", "minimum": 1, "maximum": 10},
    "max_line_characters": {"type": "integer", "minimum": 1, "maximum": 200},
    "max_cps": {"type": "number", "minimum": 1, "maximum": 100},
    "min_duration_ms": {"type": "integer", "minimum": 0},
    "max_duration_ms": {"type": "integer", "minimum": 1},
    "min_gap_ms": {"type": "integer", "minimum": 0}}}
_PROFILE = {"profile": {"type": "string", "enum": ["adult", "children"], "default": "adult"}, "limits": _LIMIT_SCHEMA}


def _tool(description, function, properties, required, readonly):
    schema = {"type": "object", "properties": properties, "required": required, "additionalProperties": False}
    return {"description": description, "inputSchema": schema, "handler": _handler(function, schema),
            "annotations": {"readOnlyHint": readonly, "destructiveHint": not readonly,
                            "idempotentHint": readonly, "openWorldHint": False}}


TOOLS = {
    "inspect_subtitles": _tool(
        "Inspect strict UTF-8 SRT structure, logical/visible Hebrew counts, overlaps and adult/children reading profiles. Synchronization and translation quality remain unverified.",
        _inspect, {"subtitle_path": _PATH, "include_cues": {"type": "boolean", "default": True}, **_PROFILE}, ["subtitle_path"], True),
    "export_subtitles": _tool(
        "Export cue JSON or SRT to SRT/WebVTT, preserving every clock and logical character order. Optional RLM at both line boundaries. Explicit output path; existing/protected sources rejected by default. Never modifies media.",
        _export, {"cue_path": _PATH, "output_path": _PATH, "format": {"type": "string", "enum": ["srt", "webvtt"], "default": "srt"},
                  "rtl_marks": {"type": "boolean", "default": False}, "utf8_bom": {"type": "boolean", "default": False},
                  "overwrite": {"type": "boolean", "default": False}, "protected_paths": {"type": "array", "items": _PATH}, **_PROFILE},
        ["cue_path", "output_path"], False),
    "audit_source_coverage": _tool(
        "Audit a selected/omitted/review source ledger against target SRT/JSON: map cues and compare approved visible text across complete clock windows and composite intervals. Structural evidence never establishes translation quality or audiovisual synchronization.",
        _coverage, {"source_events_path": _PATH, "target_path": _PATH}, ["source_events_path", "target_path"], True),
    "build_review_queue": _tool(
        "Prioritize recorded uncertainty, semantic changes, revisions, fast/short cues and linked visual reactions. Optionally save JSON to an explicit new output path; never grants automatic translation-quality PASS.",
        _queue, {"review_items_path": _PATH, "subtitle_path": _PATH, "output_path": _PATH,
                 "overwrite": {"type": "boolean", "default": False}, **_PROFILE}, ["review_items_path"], False),
}
