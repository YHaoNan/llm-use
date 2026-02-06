from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from book_extract.core import BookExtractError, ConvertOptions, Converter, EpubSource, SourceRegistry
from book_extract.mcp import serve as mcp_serve


def _make_default_converter() -> Converter:
    registry = SourceRegistry()
    registry.register(EpubSource())
    return Converter(registry=registry)


def _raw_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="book-extract raw")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    converter = _make_default_converter()
    try:
        result = converter.convert(
            input_path=Path(args.input),
            output_dir=Path(args.output),
            options=ConvertOptions(overwrite=bool(args.overwrite)),
        )
        payload: dict[str, Any] = {
            "ok": True,
            "result": {
                "output_dir": str(result.output_dir),
                "index_path": str(result.index_path),
                "source_type": result.source_type,
                "chapters_count": len(result.chapters),
                "warnings": list(result.warnings),
            },
        }
        sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return 0
    except BookExtractError as exc:
        payload = {"ok": False, "error": exc.to_dict()}
        sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return 2


def _mcp_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="book-extract mcp")
    parser.parse_args(argv)
    mcp_serve()
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(prog="book-extract")
    parser.add_argument("--mode", choices=["raw", "mcp"], required=True)
    args, rest = parser.parse_known_args(argv)

    if args.mode == "raw":
        return _raw_main(rest)
    return _mcp_main(rest)


if __name__ == "__main__":
    raise SystemExit(main())
