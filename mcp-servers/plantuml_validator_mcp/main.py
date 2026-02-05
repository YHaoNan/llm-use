import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


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


def _resolve_default_jar_path() -> Optional[Path]:
    here = Path(__file__).resolve()
    jars_dir = here.parents[1] / "jars"
    if jars_dir.is_dir():
        candidates = sorted(jars_dir.glob("plantuml-*.jar"))
        if candidates:
            return candidates[-1]
    return None


def _validate_plantuml_code(jar_path: Path, code: str) -> Tuple[bool, List[str]]:
    if not jar_path.exists():
        return False, [f"PlantUML jar not found: {jar_path}"]

    timeout_s = 20.0
    try:
        v = os.environ.get("PLANTUML_RUN_TIMEOUT_S", "").strip()
        if v:
            timeout_s = float(v)
    except Exception:
        timeout_s = 20.0

    with tempfile.TemporaryDirectory(prefix="plantuml-validate-") as td:
        puml_path = Path(td) / "input.puml"
        puml_path.write_text(code, encoding="utf-8")

        cmd = [
            "java",
            "-jar",
            str(jar_path),
            "-charset",
            "UTF-8",
            "-tpng",
            str(puml_path),
        ]
        try:
            proc = subprocess.run(
                cmd,
                cwd=td,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_s,
            )
        except FileNotFoundError:
            return False, ["java executable not found in PATH"]
        except subprocess.TimeoutExpired as e:
            output = (e.stdout or "").strip()
            lines: List[str] = []
            if output:
                lines = [line.rstrip() for line in output.splitlines() if line.strip()]
            lines.append(f"PlantUML timed out after {timeout_s:.1f}s")
            return False, lines
        except Exception as e:
            return False, [f"Failed to run PlantUML: {e}"]

        output = (proc.stdout or "").strip()
        if proc.returncode == 0:
            return True, []

        if not output:
            return False, [f"PlantUML exited with code {proc.returncode} (no output)"]

        lines = [line.rstrip() for line in output.splitlines() if line.strip()]
        return False, lines


def _tool_definitions() -> List[Dict[str, Any]]:
    return [
        {
            "name": "plantuml_validate",
            "description": "Validate PlantUML syntax using PlantUML jar",
            "inputSchema": {
                "type": "object",
                "properties": {"code": {"type": "string"}},
                "required": ["code"],
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
            "serverInfo": {"name": "plantuml-validator-mcp", "version": "0.1.0"},
        },
    }


def _handle_tools_list(request_id: Any) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": _tool_definitions()}}


def _handle_tools_call(request_id: Any, jar_path: Path, params: Any) -> Dict[str, Any]:
    if not isinstance(params, dict):
        return _jsonrpc_error(request_id, -32602, "Invalid params")
    name = params.get("name")
    arguments = params.get("arguments") or {}
    if name != "plantuml_validate":
        return _jsonrpc_error(request_id, -32601, f"Unknown tool: {name}")
    if not isinstance(arguments, dict):
        return _jsonrpc_error(request_id, -32602, "Invalid params: arguments must be an object")
    code = arguments.get("code")
    if not isinstance(code, str):
        return _jsonrpc_error(request_id, -32602, "Invalid params: code must be a string")

    ok, errors = _validate_plantuml_code(jar_path=jar_path, code=code)
    result_json = {"errors": errors}
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "content": [
                {"type": "text", "text": json.dumps(result_json, ensure_ascii=False)},
            ],
            "isError": not ok,
        },
    }


def serve(jar_path: Path) -> None:
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    out_framing = "content-length"

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
                _write_message(stdout, _handle_tools_call(request_id, jar_path, msg.get("params")), out_framing)
                continue

            if request_id is not None:
                _write_message(stdout, _jsonrpc_error(request_id, -32601, f"Method not found: {method}"), out_framing)
        except Exception as e:
            if isinstance(msg, dict) and "id" in msg:
                _write_message(stdout, _jsonrpc_error(msg.get("id"), -32603, "Internal error", str(e)), out_framing)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="plantuml-validator-mcp")
    parser.add_argument(
        "--plantuml-jar",
        default=os.environ.get("PLANTUML_JAR_PATH"),
        help="Path to plantuml.jar (or set env PLANTUML_JAR_PATH)",
    )
    args = parser.parse_args(argv)

    jar = args.plantuml_jar
    if jar:
        jar_path = Path(jar).expanduser().resolve()
    else:
        resolved = _resolve_default_jar_path()
        if not resolved:
            sys.stderr.write("PlantUML jar path not provided and no jars/plantuml-*.jar found\n")
            return 2
        jar_path = resolved

    serve(jar_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
