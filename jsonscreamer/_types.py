from __future__ import annotations

from collections.abc import Callable as _Callable
from typing import Any as _Any, Protocol

from .resolve import RefTracker

_Json = bool | int | float | str | list["_Json"] | dict[str, "_Json"]
_Path = list[str | int]


class ValidationError(ValueError):
    """Raised when an instance does not conform to the provided schema."""

    def __init__(self, absolute_path: _Path, message: str, type: str):
        self.absolute_path = absolute_path
        self.message = message
        self.type = type


_Schema = dict[str, _Any]
_Result = ValidationError | None


class _Validator(Protocol):
    def __call__(self, x: _Json, path: _Path) -> _Result: ...


_Compiler = _Callable[[_Schema, RefTracker], _Validator | None]
