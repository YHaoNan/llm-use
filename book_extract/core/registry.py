from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from book_extract.core.errors import UnsupportedFormatError
from book_extract.core.sources.base import DocumentSource


class SourceRegistry:
    def __init__(self) -> None:
        self._by_extension: dict[str, list[DocumentSource]] = defaultdict(list)

    def register(self, source: DocumentSource) -> None:
        for ext in source.supported_extensions:
            normalized = self._normalize_extension(ext)
            self._by_extension[normalized].append(source)

    def get_for_path(self, input_path: Path) -> DocumentSource:
        ext = input_path.suffix.lower()
        if not ext:
            raise UnsupportedFormatError(
                "无法从输入文件名推断文档类型（缺少后缀）",
                details={"input_path": str(input_path)},
            )

        candidates = list(self._by_extension.get(ext, []))
        if not candidates:
            raise UnsupportedFormatError(
                f"不支持的文档类型：{ext}",
                details={"input_path": str(input_path), "extension": ext},
            )

        if len(candidates) == 1:
            return candidates[0]

        for source in candidates:
            if source.can_handle(input_path):
                return source

        raise UnsupportedFormatError(
            f"无法为 {ext} 找到可处理的 DocumentSource",
            details={"input_path": str(input_path), "extension": ext},
        )

    @staticmethod
    def _normalize_extension(extension: str) -> str:
        ext = extension.strip().lower()
        if not ext.startswith("."):
            ext = "." + ext
        return ext

