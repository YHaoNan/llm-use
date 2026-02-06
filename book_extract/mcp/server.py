from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from book_extract.core import BookExtractError, ConvertOptions, Converter, EpubSource, SourceRegistry


def _debug_enabled() -> bool:
    v = os.environ.get("MCP_DEBUG", "").strip().lower()
    return v not in ("", "0", "false", "no")


def _debug(msg: str) -> None:
    if not _debug_enabled():
        return
    try:
        sys.stderr.write(msg + "\n")
        sys.stderr.flush()
    except Exception:
        pass


def _parse_header_line(line: bytes) -> Optional[Tuple[str, str]]:
    try:
        text = line.decode("utf-8", errors="replace").strip()
    except Exception:
        return None
    if ":" not in text:
        return None
    k, v = text.split(":", 1)
    k = k.strip().lower()
    v = v.strip()
    if not k:
        return None
    return k, v


def _read_headers(stdin: Any, first_line: Optional[bytes] = None) -> Optional[Dict[str, str]]:
    headers: Dict[str, str] = {}
    if first_line is not None:
        if first_line in (b"\r\n", b"\n"):
            return headers
        kv = _parse_header_line(first_line)
        if kv is not None:
            headers[kv[0]] = kv[1]
    while True:
        line = stdin.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            return headers
        kv = _parse_header_line(line)
        if kv is None:
            continue
        headers[kv[0]] = kv[1]


def _read_message(stdin: Any) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    first_line = stdin.readline()
    if not first_line:
        return None, None

    stripped = first_line.strip()
    if stripped.startswith(b"{") and stripped.endswith(b"}"):
        try:
            return json.loads(stripped.decode("utf-8")), "jsonl"
        except Exception:
            pass

    headers = _read_headers(stdin, first_line=first_line)
    if headers is None:
        return None, None
    content_length = headers.get("content-length")
    if not content_length:
        return None, None
    try:
        length = int(content_length)
    except ValueError:
        return None, None
    body = stdin.read(length)
    if not body:
        return None, None
    try:
        return json.loads(body.decode("utf-8")), "content-length"
    except Exception:
        return None, None


def _write_message(stdout: Any, payload: Dict[str, Any], framing: str) -> None:
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if framing == "jsonl":
        stdout.write(data + b"\n")
        stdout.flush()
        return
    header = f"Content-Length: {len(data)}\r\n\r\n".encode("ascii")
    stdout.write(header)
    stdout.write(data)
    stdout.flush()


def _jsonrpc_error(request_id: Any, code: int, message: str, data: Any = None) -> Dict[str, Any]:
    err: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": err}


def _tool_definitions() -> List[Dict[str, Any]]:
    return [
        {
            "name": "convert",
            "description": "Convert a document (epub/mobi/pdf...) into LLM-friendly markdown document set",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "input_path": {"type": "string"},
                    "output_dir": {"type": "string"},
                    "overwrite": {"type": "boolean", "default": False},
                },
                "required": ["input_path", "output_dir"],
            },
        }
    ]


def _handle_initialize(request_id: Any, params: Any) -> Dict[str, Any]:
    protocol_version = "2024-11-05"
    if isinstance(params, dict):
        pv = params.get("protocolVersion")
        if isinstance(pv, str) and pv:
            protocol_version = pv
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "protocolVersion": protocol_version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "book-extract-mcp", "version": "0.1.0"},
        },
    }


def _handle_tools_list(request_id: Any) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": _tool_definitions()}}


def _make_converter() -> Converter:
    registry = SourceRegistry()
    registry.register(EpubSource())
    return Converter(registry=registry)


def _handle_tools_call(request_id: Any, converter: Converter, params: Any) -> Dict[str, Any]:
    if not isinstance(params, dict):
        return _jsonrpc_error(request_id, -32602, "Invalid params")

    name = params.get("name")
    arguments = params.get("arguments") or {}
    if name != "convert":
        return _jsonrpc_error(request_id, -32601, f"Unknown tool: {name}")
    if not isinstance(arguments, dict):
        return _jsonrpc_error(request_id, -32602, "Invalid params: arguments must be an object")

    input_path = arguments.get("input_path")
    output_dir = arguments.get("output_dir")
    overwrite = arguments.get("overwrite", False)

    if not isinstance(input_path, str) or not input_path:
        return _jsonrpc_error(request_id, -32602, "Invalid params: input_path must be a string")
    if not isinstance(output_dir, str) or not output_dir:
        return _jsonrpc_error(request_id, -32602, "Invalid params: output_dir must be a string")
    if not isinstance(overwrite, bool):
        return _jsonrpc_error(request_id, -32602, "Invalid params: overwrite must be a boolean")

    try:
        result = converter.convert(
            input_path=Path(input_path),
            output_dir=Path(output_dir),
            options=ConvertOptions(overwrite=overwrite),
        )
        payload = {
            "ok": True,
            "result": {
                "output_dir": str(result.output_dir),
                "index_path": str(result.index_path),
                "source_type": result.source_type,
                "chapters_count": len(result.chapters),
                "chapters": [c.to_dict() for c in result.chapters],
                "warnings": list(result.warnings),
            },
        }
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
                "isError": False,
            },
        }
    except BookExtractError as exc:
        payload = {"ok": False, "error": exc.to_dict()}
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
                "isError": True,
            },
        }
    except Exception as exc:
        payload = {"ok": False, "error": {"code": "internal_error", "message": str(exc)}}
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
                "isError": True,
            },
        }


def serve() -> None:
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    out_framing = "content-length"

    converter = _make_converter()

    while True:
        msg, in_framing = _read_message(stdin)
        if msg is None:
            break
        if in_framing in ("jsonl", "content-length"):
            out_framing = in_framing

        try:
            method = msg.get("method")
            request_id = msg.get("id", None)
            if not method:
                continue

            if method == "initialize":
                if request_id is None:
                    continue
                _write_message(stdout, _handle_initialize(request_id, msg.get("params")), out_framing)
                continue

            if method == "shutdown":
                if request_id is not None:
                    _write_message(stdout, {"jsonrpc": "2.0", "id": request_id, "result": None}, out_framing)
                continue

            if method == "exit":
                break

            if method == "ping":
                if request_id is not None:
                    _write_message(stdout, {"jsonrpc": "2.0", "id": request_id, "result": {}}, out_framing)
                continue

            if method == "tools/list":
                if request_id is None:
                    continue
                _write_message(stdout, _handle_tools_list(request_id), out_framing)
                continue

            if method == "tools/call":
                if request_id is None:
                    continue
                _write_message(stdout, _handle_tools_call(request_id, converter, msg.get("params")), out_framing)
                continue

            if request_id is not None:
                _write_message(stdout, _jsonrpc_error(request_id, -32601, f"Method not found: {method}"), out_framing)
        except Exception as e:
            _debug(f"internal_error:{type(e).__name__}:{e}")
            if isinstance(msg, dict) and "id" in msg:
                _write_message(stdout, _jsonrpc_error(msg.get("id"), -32603, "Internal error", str(e)), out_framing)

