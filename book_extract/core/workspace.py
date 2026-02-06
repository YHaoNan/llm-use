from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from book_extract.core.models import ChapterRef


_INVALID_SLUG_CHARS = re.compile(r"[^a-zA-Z0-9._-]+")


@dataclass(frozen=True)
class WorkspaceLayout:
    output_dir: Path
    chapters_dir: Path
    images_dir: Path
    index_path: Path


class OutputWorkspace:
    def __init__(self, *, output_dir: Path, input_path: Path, source_type: str) -> None:
        self._layout = WorkspaceLayout(
            output_dir=output_dir,
            chapters_dir=output_dir / "chapters",
            images_dir=output_dir / "images",
            index_path=output_dir / "chapter-index.json",
        )
        self._input_path = input_path
        self._source_type = source_type
        self._chapter_counter = 0

    @property
    def layout(self) -> WorkspaceLayout:
        return self._layout

    def init_layout(self) -> None:
        self._layout.output_dir.mkdir(parents=True, exist_ok=True)
        self._layout.chapters_dir.mkdir(parents=True, exist_ok=True)
        self._layout.images_dir.mkdir(parents=True, exist_ok=True)

    def write_chapter(
        self,
        *,
        slug: str,
        markdown: str,
        title: str | None = None,
        level: int | None = None,
        parent_id: str | None = None,
        source_ref: Any | None = None,
    ) -> ChapterRef:
        safe_slug = self._sanitize_slug(slug)
        filename = safe_slug if safe_slug.lower().endswith(".md") else f"{safe_slug}.md"
        path = self._unique_path(self._layout.chapters_dir / filename)
        path.write_text(markdown, encoding="utf-8", newline="\n")

        self._chapter_counter += 1
        chapter_id = f"ch_{self._chapter_counter:04d}"
        rel_path = path.relative_to(self._layout.output_dir).as_posix()
        return ChapterRef(
            id=chapter_id,
            path=rel_path,
            title=title,
            level=level,
            parent_id=parent_id,
            source_ref=source_ref,
        )

    def write_image(self, *, filename: str, content: bytes, media_type: str | None = None) -> str:
        safe_name = self._sanitize_filename(filename)
        target = self._unique_path(self._layout.images_dir / safe_name)
        target.write_bytes(content)
        return target.relative_to(self._layout.output_dir).as_posix()

    def finalize_index(self, *, chapters: list[ChapterRef], warnings: list[str] | None = None) -> Path:
        payload: dict[str, Any] = {
            "version": 1,
            "source": {"input_path": str(self._input_path), "detected_type": self._source_type},
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "chapters": [c.to_dict() for c in chapters],
        }
        if warnings:
            payload["warnings"] = list(warnings)

        self._layout.index_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return self._layout.index_path

    @staticmethod
    def _sanitize_slug(slug: str) -> str:
        cleaned = _INVALID_SLUG_CHARS.sub("-", slug.strip()).strip("-")
        return cleaned or "chapter"

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        cleaned = name.replace("\\", "/").split("/")[-1]
        cleaned = _INVALID_SLUG_CHARS.sub("-", cleaned.strip()).strip("-")
        return cleaned or "file"

    @staticmethod
    def _unique_path(path: Path) -> Path:
        if not path.exists():
            return path

        stem = path.stem
        suffix = path.suffix
        parent = path.parent

        i = 2
        while True:
            candidate = parent / f"{stem}-{i}{suffix}"
            if not candidate.exists():
                return candidate
            i += 1

