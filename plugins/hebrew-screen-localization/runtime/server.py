"""Local stdio MCP and CLI transport. Stdout is protocol data only."""
from __future__ import annotations
import argparse
import json
import math
import re
import sys
from pathlib import Path

from subtitle_tools import TOOLS as SUBTITLE_TOOLS
from media_tools import TOOLS as MEDIA_TOOLS
from job_tools import TOOLS as JOB_TOOLS
from localization_tools import TOOLS as LOCALIZATION_TOOLS

VERSION = "0.4.1"
PROTOCOLS = ("2024-11-05", "2025-03-26", "2025-06-18")
TOOLS = {**SUBTITLE_TOOLS, **MEDIA_TOOLS, **JOB_TOOLS, **LOCALIZATION_TOOLS}
assert len(TOOLS) == len(SUBTITLE_TOOLS) + len(MEDIA_TOOLS) + len(JOB_TOOLS) + len(LOCALIZATION_TOOLS), "Duplicate tool names"


def validate(value, schema, at="arguments"):
    for keyword in ("anyOf", "oneOf"):
        if keyword in schema:
            matches = 0
            for option in schema[keyword]:
                try:
                    validate(value, option, at)
                    matches += 1
                except ValueError:
                    pass
            if matches == 0 or (keyword == "oneOf" and matches != 1):
                raise ValueError(f"{at}: does not match {keyword}")
    kind = schema.get("type")
    kinds = {"object": lambda x: isinstance(x, dict), "array": lambda x: isinstance(x, list),
             "string": lambda x: isinstance(x, str), "boolean": lambda x: isinstance(x, bool),
             "integer": lambda x: isinstance(x, int) and not isinstance(x, bool),
             "number": lambda x: isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x),
             "null": lambda x: x is None}
    expected = kind if isinstance(kind, list) else [kind] if kind else []
    if expected and not any(kinds[k](value) for k in expected):
        raise ValueError(f"{at}: expected {kind}")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{at}: unsupported value")
    if "const" in schema and value != schema["const"]:
        raise ValueError(f"{at}: unexpected value")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                raise ValueError(f"{at}.{key}: required")
        for key, item in value.items():
            if key in props:
                validate(item, props[key], at + "." + key)
            elif schema.get("additionalProperties") is False:
                raise ValueError(f"{at}.{key}: unsupported argument")
            elif isinstance(schema.get("additionalProperties"), dict):
                validate(item, schema["additionalProperties"], at + "." + key)
    elif isinstance(value, list):
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", math.inf):
            raise ValueError(f"{at}: array length outside limits")
        for index, item in enumerate(value):
            validate(item, schema.get("items", {}), f"{at}[{index}]")
    elif isinstance(value, str):
        if len(value) < schema.get("minLength", 0) or len(value) > schema.get("maxLength", math.inf):
            raise ValueError(f"{at}: string length outside limits")
        if schema.get("pattern") and not re.search(schema["pattern"], value):
            raise ValueError(f"{at}: invalid format")
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        if not math.isfinite(value) or value < schema.get("minimum", -math.inf) or value > schema.get("maximum", math.inf):
            raise ValueError(f"{at}: number outside limits")
        if value <= schema.get("exclusiveMinimum", -math.inf) or value >= schema.get("exclusiveMaximum", math.inf):
            raise ValueError(f"{at}: number outside exclusive limits")


def call_tool(name, arguments):
    try:
        if name not in TOOLS:
            raise ValueError("Unknown tool: " + str(name))
        validate(arguments, TOOLS[name]["inputSchema"])
        result = TOOLS[name]["handler"](arguments)
        if not isinstance(result, dict):
            raise TypeError("Tool must return an object")
        result = dict(result)
        media = result.pop("_media", [])
        content = [{"type": "text", "text": json.dumps(result, ensure_ascii=False, allow_nan=False)}]
        for item in media:
            if isinstance(item, dict) and item.get("type") in ("image", "audio") and isinstance(item.get("data"), str) and isinstance(item.get("mimeType"), str):
                content.append({"type": item["type"], "data": item["data"], "mimeType": item["mimeType"]})
        return {"content": content, "structuredContent": result,
                "isError": result.get("status") in ("ERROR", "FAILED")}
    except Exception as exc:
        result = {"status": "ERROR", "error_type": type(exc).__name__, "error": str(exc),
                  "translation_quality_status": "NOT_EVALUATED", "synchronization_status": "NOT_VERIFIED"}
        return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}],
                "structuredContent": result, "isError": True}


def handle(request):
    if not isinstance(request, dict) or request.get("jsonrpc") != "2.0" or not isinstance(request.get("method"), str):
        return {"jsonrpc": "2.0", "id": request.get("id") if isinstance(request, dict) else None,
                "error": {"code": -32600, "message": "Invalid request"}}
    if "id" in request and (isinstance(request["id"], bool) or not isinstance(request["id"], (str, int, float, type(None)))):
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid request id"}}
    if "id" not in request:
        return None
    ident, method = request["id"], request["method"]
    params = request.get("params", {})
    if not isinstance(params, dict):
        return {"jsonrpc": "2.0", "id": ident, "error": {"code": -32602, "message": "Parameters must be an object"}}
    if method == "initialize":
        protocol = params.get("protocolVersion")
        result = {"protocolVersion": protocol if protocol in PROTOCOLS else PROTOCOLS[-1],
                  "capabilities": {"tools": {"listChanged": False}},
                  "serverInfo": {"name": "hebrew-screen-localization-local", "version": VERSION},
                  "instructions": "Local media/subtitle tools. Structural checks, OCR, alignment, playback and checkpoints never prove semantic quality or full-watch completion."}
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": [{"name": name, **{key: value for key, value in spec.items() if key != "handler"}} for name, spec in sorted(TOOLS.items())]}
    elif method == "tools/call":
        result = call_tool(params.get("name"), params.get("arguments", {}))
    else:
        return {"jsonrpc": "2.0", "id": ident, "error": {"code": -32601, "message": "Method not found"}}
    return {"jsonrpc": "2.0", "id": ident, "result": result}


def main():
    parser = argparse.ArgumentParser(description="Hebrew localization local tools; defaults to MCP stdio.")
    parser.add_argument("--list", action="store_true", help="Print tool names and schemas as JSON")
    parser.add_argument("--call", help="Call one named tool locally")
    parser.add_argument("--arguments-file", help="UTF-8 JSON file of tool arguments")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="strict")
    sys.stdin.reconfigure(encoding="utf-8", errors="strict")
    if args.list:
        print(json.dumps(handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})["result"], ensure_ascii=False))
        return
    if args.call:
        try:
            arguments = json.loads(Path(args.arguments_file).read_text(encoding="utf-8-sig")) if args.arguments_file else {}
            result = call_tool(args.call, arguments)
        except (ValueError, OSError, UnicodeError) as exc:
            data = {"status": "ERROR", "error_type": type(exc).__name__, "error": str(exc)}
            result = {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}], "structuredContent": data, "isError": True}
        print(json.dumps(result, ensure_ascii=False, allow_nan=False), flush=True)
        if result["isError"]:
            sys.exit(1)
        return
    def read_packet():
        first = sys.stdin.buffer.readline()
        if not first:
            return None, False
        if first.lower().startswith(b"content-length:"):
            try:
                length = int(first.split(b":", 1)[1].strip())
            except (ValueError, IndexError) as exc:
                raise ValueError("Invalid Content-Length header") from exc
            if length < 0 or length > 16 * 1024 * 1024:
                raise ValueError("Request exceeds 16 MiB")
            while True:
                header = sys.stdin.buffer.readline()
                if not header:
                    raise ValueError("Truncated MCP headers")
                if header in (b"\r\n", b"\n"):
                    break
            payload = sys.stdin.buffer.read(length)
            if len(payload) != length:
                raise ValueError("Truncated MCP request")
            return payload.decode("utf-8"), True
        if len(first) > 16 * 1024 * 1024:
            raise ValueError("Request exceeds 16 MiB")
        return first.decode("utf-8"), False

    while True:
        framed = False
        try:
            packet, framed = read_packet()
            if packet is None:
                break
            request = json.loads(packet, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Non-finite JSON number")))
            response = handle(request)
        except (ValueError, UnicodeError) as exc:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}
        if response is not None:
            if framed:
                encoded = json.dumps(response, ensure_ascii=False, allow_nan=False).encode("utf-8")
                sys.stdout.buffer.write(f"Content-Length: {len(encoded)}\r\n\r\n".encode("ascii") + encoded)
                sys.stdout.buffer.flush()
            else:
                print(json.dumps(response, ensure_ascii=False, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
