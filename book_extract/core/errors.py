from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(eq=False)
class BookExtractError(Exception):
    message: str
    code: str = "book_extract_error"
    details: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"message": self.message, "code": self.code}
        if self.details is not None:
            payload["details"] = dict(self.details)
        return payload


class InvalidInputError(BookExtractError):
    def __init__(self, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message=message, code="invalid_input", details=details)


class UnsupportedFormatError(BookExtractError):
    def __init__(
        self,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code="unsupported_format", details=details)


class OutputConflictError(BookExtractError):
    def __init__(
        self,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code="output_conflict", details=details)


class DependencyError(BookExtractError):
    def __init__(
        self,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code="dependency_missing", details=details)


class ConversionError(BookExtractError):
    def __init__(
        self,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, code="conversion_failed", details=details)
        self.__cause__ = cause

