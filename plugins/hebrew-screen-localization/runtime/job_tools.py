"""Local checkpoint and review tools; no network, translation or media writes."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import html
from html.entities import html5
import json
import os
from pathlib import Path
import tempfile
import unicodedata

try:
    from .subtitle_tools import parse_srt, _validate, _limits, _LIMIT_SCHEMA
except ImportError:
    from subtitle_tools import parse_srt, _validate, _limits, _LIMIT_SCHEMA


_MAX_JSON = 50 * 1024 * 1024
_SAMPLE_BYTES = 65536
_DATA_KEYS = ("cues", "characters", "visual_events", "findings", "decisions")
_QC_KEYS = ("semantic", "synchronization", "visual_context", "rendering", "full_watch")


def _now():
    return datetime.now(timezone.utc).isoformat()


def _path(value):
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ValueError("A nonempty explicit local path is required.")
    if "://" in value or value.startswith(("\\\\", "//")):
        raise ValueError("Network URLs and UNC paths are not supported.")
    result = Path(value).expanduser().resolve()
    if str(result).startswith(("\\\\", "//")):
        raise ValueError("Resolved path must be local, not UNC.")
    return result


def _raw(path):
    if not path.is_file() or path.stat().st_size > _MAX_JSON:
        raise ValueError("Expected a local file no larger than 50 MiB.")
    return path.read_bytes()


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def _fingerprint(path):
    before = path.stat()
    if not path.is_file():
        raise ValueError("Source media must be a regular local file.")
    size = before.st_size
    offsets = sorted({0, max(0, size // 2 - _SAMPLE_BYTES // 2), max(0, size - _SAMPLE_BYTES)})
    digest = hashlib.sha256()
    digest.update(str(size).encode("ascii"))
    samples = []
    with path.open("rb") as stream:
        for offset in offsets:
            stream.seek(offset)
            block = stream.read(_SAMPLE_BYTES)
            digest.update(f"/{offset}/{len(block)}/".encode("ascii"))
            digest.update(block)
            samples.append({"offset": offset, "length": len(block)})
    after = path.stat()
    if (size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("Media changed during fingerprinting; retry after it is stable.")
    return {"path": str(path), "size": size, "mtime_ns": before.st_mtime_ns,
            "sample_sha256": digest.hexdigest(), "hash_mode": "sample_plus_stat_not_full_file",
            "samples": samples,
            "limitation": "Changes outside sampled regions with unchanged size/mtime may be missed; this is not a full-file hash."}


def _qc():
    return {key: "NOT_VERIFIED" for key in _QC_KEYS}


def _state_path(job_dir):
    root = _path(job_dir)
    path = root / "job.json"
    if path.is_symlink():
        raise ValueError("Checkpoint state must not be a symlink.")
    return root, path


def _load_state(job_dir):
    root, path = _state_path(job_dir)
    state = json.loads(_raw(path).decode("utf-8-sig"))
    if not isinstance(state, dict) or state.get("format") != "hebrew-localization-job-v1":
        raise ValueError("Unsupported job state.")
    revision = state.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        raise ValueError("Invalid checkpoint revision.")
    if not isinstance(state.get("source_media"), list) or not state["source_media"]:
        raise ValueError("Missing source-media fingerprints.")
    return root, path, state


def _changes(state):
    changes = []
    for recorded in state["source_media"]:
        if not isinstance(recorded, dict) or "path" not in recorded:
            raise ValueError("Malformed source fingerprint.")
        try:
            current = _fingerprint(_path(recorded["path"]))
            fields = [key for key in ("size", "mtime_ns", "sample_sha256") if recorded.get(key) != current[key]]
            if fields:
                changes.append({"path": recorded["path"], "changed_fields": fields, "current_fingerprint": current})
        except (OSError, ValueError) as exc:
            changes.append({"path": recorded["path"], "changed_fields": ["missing_or_unreadable"], "error": str(exc)})
    return changes


def _init(args):
    root = _path(args["job_dir"])
    if root.exists():
        raise FileExistsError("Job directory must be new; existing directories are never overwritten.")
    if not root.parent.is_dir():
        raise ValueError("The explicit job-directory parent must already exist.")
    sources = [_path(value) for value in args["source_media_paths"]]
    if not sources or len({os.path.normcase(str(p)) for p in sources}) != len(sources):
        raise ValueError("Supply one or more distinct source media paths.")
    fingerprints = [_fingerprint(path) for path in sources]
    state = {"format": "hebrew-localization-job-v1", "revision": 0, "created_at": _now(),
             "updated_at": _now(), "profile": args.get("profile", "adult"),
             "source_media": fingerprints, "data": {key: [] for key in _DATA_KEYS}, "qc": _qc()}
    root.mkdir()  # Exclusive directory creation prevents races and overwrites.
    (root / "backups").mkdir()
    with (root / "job.json").open("xb") as stream:
        stream.write(_json_bytes(state))
    return {"status": "CREATED", "job_dir": str(root), "state_path": str(root / "job.json"),
            "revision": 0, "state": state, "source_media_modified": False}


def _get(args):
    root, path, state = _load_state(args["job_dir"])
    changes = _changes(state)
    return {"status": "SOURCE_CHANGED" if changes else "LOADED", "job_dir": str(root),
            "state_path": str(path), "revision": state["revision"], "state": state,
            "source_changes": changes, "qc_invalidated": bool(changes),
            "effective_qc": {key: "INVALIDATED" if changes else "NOT_VERIFIED" for key in _QC_KEYS},
            "scope": "Checkpoint and sampled-media identity only; saved data cannot certify QC.",
            "source_media_modified": False}


@contextmanager
def _lock(root):
    lock = root / ".checkpoint.lock"
    descriptor = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii") as stream:
            stream.write(str(os.getpid()))
        yield
    finally:
        lock.unlink(missing_ok=True)


def _reject_qc_setters(value):
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower()
            if lowered in ("qc", "quality_gates", "effective_qc"):
                raise ValueError("Checkpoints cannot set quality-gate state.")
            if (lowered == "status" or lowered.endswith("_status")) and isinstance(item, str) and item.upper() in ("PASS", "PASSED"):
                raise ValueError("Checkpoints cannot set a PASS review status.")
            _reject_qc_setters(item)
    elif isinstance(value, list):
        for item in value:
            _reject_qc_setters(item)


def _save(args):
    root, state_path, _ = _load_state(args["job_dir"])
    data = args["data"]
    for key, items in data.items():
        if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
            raise ValueError("Checkpoint categories must be arrays of JSON objects.")
    _reject_qc_setters(data)
    if len(_json_bytes(data)) > _MAX_JSON:
        raise ValueError("Checkpoint data exceeds 50 MiB.")
    with _lock(root):
        _, state_path, state = _load_state(str(root))
        if state["revision"] != args["expected_revision"]:
            raise ValueError(f"Revision conflict: expected {args['expected_revision']}, current {state['revision']}.")
        backup_dir = root / "backups"
        if backup_dir.is_symlink() or not backup_dir.is_dir():
            raise ValueError("Job backup directory must be an ordinary local directory.")
        previous_raw = _raw(state_path)
        backup = backup_dir / f"revision-{state['revision']:06d}.json"
        if backup.exists():
            if backup.is_symlink() or _raw(backup) != previous_raw:
                raise FileExistsError("Existing revision backup differs; no overwrite permitted.")
        else:
            with backup.open("xb") as stream:
                stream.write(previous_raw)
                stream.flush()
                os.fsync(stream.fileno())
        state["data"].update(data)
        state["revision"] += 1
        state["updated_at"] = _now()
        state["qc"] = _qc()
        changes = _changes(state)
        state["source_changes_at_checkpoint"] = changes
        encoded = _json_bytes(state)
        descriptor, temporary = tempfile.mkstemp(prefix=".job-", dir=str(root))
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, state_path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return {"status": "SAVED", "revision": state["revision"], "state_path": str(state_path),
            "backup_path": str(backup), "qc_invalidated": True,
            "source_changes": changes, "effective_qc": _qc(), "source_media_modified": False}


def _audit(args):
    path = _path(args["context_path"])
    content = json.loads(_raw(path).decode("utf-8-sig"))
    if isinstance(content, dict) and content.get("format") == "hebrew-localization-job-v1":
        content = content.get("data")
    if not isinstance(content, dict):
        raise ValueError("Context must be a JSON object containing cues and visual_events.")
    cues = content.get("cues", [])
    visuals = content.get("visual_events", [])
    if not isinstance(cues, list) or not isinstance(visuals, list) or any(not isinstance(x, dict) for x in cues + visuals):
        raise ValueError("Context cues/visual_events must be arrays of objects.")
    issues = []
    def identifiers(items, alternative, kind):
        found = set()
        for index, item in enumerate(items):
            identity = item.get("id", item.get(alternative))
            if isinstance(identity, bool) or not isinstance(identity, (str, int)) or not str(identity).strip():
                issues.append({"row": index, "code": "missing_or_invalid_id", "kind": kind})
            elif str(identity) in found:
                issues.append({"id": identity, "code": "duplicate_id", "kind": kind})
            else:
                found.add(str(identity))
        return found
    def evidence_missing(value):
        if not value:
            return True
        if isinstance(value, str):
            return value.lower() in ("unknown", "unresolved", "pending", "not_verified")
        if isinstance(value, dict):
            return str(value.get("status", "")).lower() in ("unknown", "unresolved", "pending", "not_verified")
        if isinstance(value, list):
            return all(evidence_missing(item) for item in value)
        return True
    cue_ids = identifiers(cues, "cue_id", "cue")
    visual_ids = identifiers(visuals, "visual_event_id", "visual_event")
    for index, cue in enumerate(cues):
        identity = cue.get("id", cue.get("cue_id", index))
        for field in ("speaker_id", "addressee_ids", "quoted_person_id", "register", "evidence"):
            if field not in cue:
                issues.append({"id": identity, "code": "missing_cue_metadata", "field": field})
        if "addressee_ids" in cue and not isinstance(cue["addressee_ids"], list):
            issues.append({"id": identity, "code": "invalid_addressee_ids"})
        if "evidence" in cue and evidence_missing(cue["evidence"]):
            issues.append({"id": identity, "code": "empty_or_unresolved_evidence"})
        if cue.get("event_kind") in ("reading", "reference", "reaction", "misreading") and not cue.get("visual_event_ids"):
            issues.append({"id": identity, "code": "missing_visual_link"})
        visual_links = cue.get("visual_event_ids", [])
        if not isinstance(visual_links, list):
            issues.append({"id": identity, "code": "invalid_visual_event_ids"})
            visual_links = []
        for linked in visual_links:
            if str(linked) not in visual_ids:
                issues.append({"id": identity, "code": "unknown_visual_link", "linked_id": linked})
    for index, event in enumerate(visuals):
        identity = event.get("id", event.get("visual_event_id", index))
        for field in ("source_visible_text", "readable_start", "readable_end", "read_response_links", "evidence"):
            if field not in event:
                issues.append({"id": identity, "code": "missing_visual_metadata", "field": field})
        if "evidence" in event and evidence_missing(event["evidence"]):
            issues.append({"id": identity, "code": "empty_or_unresolved_evidence"})
        links = event.get("read_response_links", [])
        if not isinstance(links, list) or any(not isinstance(link, dict) for link in links):
            issues.append({"id": identity, "code": "invalid_read_response_links"})
            continue
        for link in links:
            for field in ("cue_id", "relation", "character_id", "evidence", "knowledge"):
                if field not in link:
                    issues.append({"id": identity, "code": "missing_link_metadata", "field": field})
            if "cue_id" in link and str(link["cue_id"]) not in cue_ids:
                issues.append({"id": identity, "code": "unknown_linked_cue", "linked_id": link["cue_id"]})
            knowledge = link.get("knowledge")
            if not isinstance(knowledge, dict) or "audience" not in knowledge or "character" not in knowledge:
                issues.append({"id": identity, "code": "missing_knowledge_metadata"})
            if "evidence" in link and evidence_missing(link["evidence"]):
                issues.append({"id": identity, "code": "empty_or_unresolved_link_evidence"})
    status = "NO_CONTEXT_ITEMS" if not cues and not visuals else ("METADATA_REVIEW_REQUIRED" if issues else "METADATA_COMPLETE")
    return {"status": status,
            "semantic_status": "SEMANTIC_NOT_VERIFIED", "scope": "Mechanical metadata presence and ID links only; no speaker, agreement, interpretation or fidelity judgment.",
            "context_path": str(path), "cue_count": len(cues), "visual_event_count": len(visuals), "issues": issues}


def _load_srt(path):
    if path.suffix.lower() != ".srt":
        raise ValueError("The local review workspace accepts strict UTF-8 SRT inputs.")
    raw = _raw(path)
    parsed = parse_srt(raw)
    errors = [issue for issue in parsed["issues"] if issue["severity"] == "error"]
    if errors or not parsed["cues"]:
        raise ValueError("SRT input has structural errors or no cues: " + ", ".join(item["code"] for item in errors))
    return raw, parsed


def _workspace(args):
    source = _path(args["source_subtitle_path"])
    target = _path(args["target_subtitle_path"])
    output = _path(args["output_dir"])
    if output.exists():
        raise FileExistsError("Output directory must be new; no overwrite is supported.")
    if not output.parent.is_dir():
        raise ValueError("Output-directory parent must already exist.")
    source_raw, source_parsed = _load_srt(source)
    target_raw, target_parsed = _load_srt(target)
    template_path = Path(__file__).resolve().parent.parent / "assets" / "review-workspace.html"
    template = template_path.read_text(encoding="utf-8")
    payload = {"source_name": source.name, "target_name": target.name,
               "source_sha256": hashlib.sha256(source_raw).hexdigest(), "target_sha256": hashlib.sha256(target_raw).hexdigest(),
               "source_cues": source_parsed["cues"], "target_cues": target_parsed["cues"],
               "parse_warnings": source_parsed["issues"] + target_parsed["issues"],
               "profile": args.get("profile", "adult"), "limits": _limits(args),
               "rtl_marks": b"\xe2\x80\x8f" in target_raw,
               "html_entities": html5,
               "numeric_entity_replacements": {str(key): value for key, value in html._invalid_charrefs.items()},
               "invalid_entity_codepoints": sorted(html._invalid_codepoints),
               "combining_characters": "".join(chr(i) for i in range(0x110000) if unicodedata.combining(chr(i)))}
    # JSON in a nonexecutable script element must still escape HTML delimiters.
    safe_json = json.dumps(payload, ensure_ascii=False, allow_nan=False).replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    if template.count("__WORKSPACE_DATA__") != 1:
        raise ValueError("Review template must contain exactly one payload marker.")
    rendered = template.replace("__WORKSPACE_DATA__", safe_json)
    output.mkdir()
    html_path = output / "review.html"
    with html_path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(rendered)
    with (output / "workspace.json").open("xb") as stream:
        stream.write(_json_bytes(payload))
    return {"status": "CREATED", "html_path": str(html_path), "workspace_data_path": str(output / "workspace.json"),
            "cue_count": len(target_parsed["cues"]), "semantic_status": "SEMANTIC_NOT_VERIFIED",
            "synchronization_status": "NOT_VERIFIED", "rendering_status": "NOT_VERIFIED", "source_media_modified": False,
            "limitations": ["Media is selected locally by the user; no media is copied or encoded.",
                            "Browser HEVC decoding and selection of the selected source-language audio track may be unavailable; verify in the original player.",
                            "This workspace does not certify continuous watching, translation quality or timing."]}


def _handler(function, schema):
    def invoke(args):
        try:
            _validate(args, schema)
            return function(args)
        except (ValueError, OSError, UnicodeError, TypeError, KeyError) as exc:
            return {"status": "ERROR", "error_type": type(exc).__name__, "error": str(exc),
                    "semantic_status": "SEMANTIC_NOT_VERIFIED", "source_media_modified": False}
    return invoke


_PATH = {"type": "string", "minLength": 1}
_DATA = {"type": "object", "additionalProperties": False,
         "properties": {key: {"type": "array", "items": {"type": "object"}} for key in _DATA_KEYS}}


def _tool(description, function, properties, required, readonly=False):
    schema = {"type": "object", "properties": properties, "required": required, "additionalProperties": False}
    return {"description": description, "inputSchema": schema, "handler": _handler(function, schema),
            "annotations": {"readOnlyHint": readonly, "destructiveHint": False,
                            "idempotentHint": readonly, "openWorldHint": False}}


TOOLS = {
    "init_localization_job": _tool("Create a new local revision-zero job with sampled media hashes plus stat, profile, empty ledgers and unverified QC. Refuses existing directories; never writes source media.", _init,
        {"job_dir": _PATH, "source_media_paths": {"type": "array", "items": _PATH}, "profile": {"type": "string", "enum": ["adult", "children"], "default": "adult"}}, ["job_dir", "source_media_paths"]),
    "get_job_state": _tool("Read a checkpoint and compare sampled media identity. Report source changes and invalidate effective QC; never certifies quality or edits files.", _get, {"job_dir": _PATH}, ["job_dir"], True),
    "save_checkpoint": _tool("Atomically save allowed ledger categories at an expected revision, retaining an immutable revision backup. Revision collisions and QC/PASS setters are rejected.", _save,
        {"job_dir": _PATH, "expected_revision": {"type": "integer", "minimum": 0}, "data": _DATA}, ["job_dir", "expected_revision", "data"]),
    "audit_character_context": _tool("Check only presence of speaker/addressee/quoted-person/register/evidence and written-read-response link metadata. Semantic quality always remains SEMANTIC_NOT_VERIFIED.", _audit, {"context_path": _PATH}, ["context_path"], True),
    "build_review_workspace": _tool("Create an offline, safe Hebrew SRT editor with local-file media selection, previous/next/loop, text overlay, counts/CPS and edited SRT/JSON downloads. New explicit directory only; no media encoding, uploading or quality certification.", _workspace,
        {"source_subtitle_path": _PATH, "target_subtitle_path": _PATH, "output_dir": _PATH,
         "profile": {"type": "string", "enum": ["adult", "children"], "default": "adult"}, "limits": _LIMIT_SCHEMA},
        ["source_subtitle_path", "target_subtitle_path", "output_dir"]),
}
