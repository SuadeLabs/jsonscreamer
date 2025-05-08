from __future__ import annotations

from collections.abc import Callable as _Callable
from typing import Any as _Any, NamedTuple, Protocol

from .resolve import RefTracker


class _Error(NamedTuple):
    absolute_path: list[str | int]
    message: str
    type: str = ""


_Json = bool | int | float | str | list["_Json"] | dict[str, "_Json"]
_Path = list[str | int]
_Schema = dict[str, _Any]
_Result = tuple[bool, _Error | None]


class _Validator(Protocol):
    def __call__(self, x: _Json, path: _Path) -> _Result: ...


_Compiler = _Callable[[_Schema, RefTracker], _Validator | None]
