from __future__ import annotations

import shutil
from pathlib import Path

from book_extract.core.errors import BookExtractError, ConversionError, InvalidInputError, OutputConflictError
from book_extract.core.models import ConvertOptions, ConvertRequest, ConvertResult
from book_extract.core.registry import SourceRegistry
from book_extract.core.workspace import OutputWorkspace


class Converter:
    def __init__(self, *, registry: SourceRegistry | None = None) -> None:
        self._registry = registry or SourceRegistry()

    @property
    def registry(self) -> SourceRegistry:
        return self._registry

    def convert(
        self,
        *,
        input_path: str | Path,
        output_dir: str | Path,
        options: ConvertOptions | None = None,
    ) -> ConvertResult:
        opts = options or ConvertOptions()
        in_path = Path(input_path)
        out_dir = Path(output_dir)

        if not in_path.exists() or not in_path.is_file():
            raise InvalidInputError(
                "输入文件不存在或不可读",
                details={"input_path": str(in_path)},
            )

        if out_dir.exists():
            if not opts.overwrite:
                raise OutputConflictError(
                    "输出目录已存在且 overwrite=False",
                    details={"output_dir": str(out_dir)},
                )
            shutil.rmtree(out_dir)

        source = self._registry.get_for_path(in_path)
        workspace = OutputWorkspace(output_dir=out_dir, input_path=in_path, source_type=source.type)
        workspace.init_layout()

        request = ConvertRequest(input_path=in_path, output_dir=out_dir, options=opts)

        try:
            source_result = source.convert(request, workspace)
        except BookExtractError:
            raise
        except Exception as exc:
            raise ConversionError(
                "转换失败",
                details={"input_path": str(in_path), "source_type": getattr(source, "type", None)},
                cause=exc,
            ) from exc

        index_path = workspace.finalize_index(chapters=source_result.chapters, warnings=source_result.warnings)
        return ConvertResult(
            output_dir=out_dir,
            index_path=index_path,
            source_type=source.type,
            chapters=source_result.chapters,
            warnings=source_result.warnings,
            metadata=source_result.metadata,
        )


def convert(
    *,
    input_path: str | Path,
    output_dir: str | Path,
    options: ConvertOptions | None = None,
    registry: SourceRegistry | None = None,
) -> ConvertResult:
    return Converter(registry=registry).convert(input_path=input_path, output_dir=output_dir, options=options)

