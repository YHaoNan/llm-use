from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from book_extract.core.models import ConvertRequest, SourceConvertResult

if TYPE_CHECKING:
    from book_extract.core.workspace import OutputWorkspace


class DocumentSource(ABC):
    type: str
    supported_extensions: tuple[str, ...]

    def can_handle(self, input_path: Path) -> bool:
        return True

    @abstractmethod
    def convert(self, request: ConvertRequest, workspace: OutputWorkspace) -> SourceConvertResult: ...

