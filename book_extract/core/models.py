from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ConvertOptions:
    overwrite: bool = False
    language: str | None = None
    max_image_width: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConvertRequest:
    input_path: Path
    output_dir: Path
    options: ConvertOptions


@dataclass(frozen=True)
class ChapterRef:
    id: str
    path: str
    title: str | None = None
    level: int | None = None
    parent_id: str | None = None
    source_ref: Any | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"id": self.id, "path": self.path}
        if self.title is not None:
            payload["title"] = self.title
        if self.level is not None:
            payload["level"] = self.level
        if self.parent_id is not None:
            payload["parent_id"] = self.parent_id
        if self.source_ref is not None:
            payload["source_ref"] = self.source_ref
        return payload


@dataclass(frozen=True)
class SourceConvertResult:
    chapters: list[ChapterRef]
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConvertResult:
    output_dir: Path
    index_path: Path
    source_type: str
    chapters: list[ChapterRef]
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

