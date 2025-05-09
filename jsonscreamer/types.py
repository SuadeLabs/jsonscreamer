from __future__ import annotations

from collections.abc import Callable as _Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any as _Any, Protocol

if TYPE_CHECKING:
    from .resolve import RefTracker

Json = bool | int | float | str | list["Json"] | dict[str, "Json"]
Path = list[str | int]
Format = _Callable[[str], bool]


class ValidationError(ValueError):
    """Raised when an instance does not conform to the provided schema."""

    def __init__(self, absolute_path: Path, message: str, type: str):
        self.absolute_path = absolute_path
        self.message = message
        self.type = type


@dataclass
class Context:
    formats: dict[str, Format]
    tracker: RefTracker


Schema = dict[str, _Any]
Result = ValidationError | None


class Validator(Protocol):
    def __call__(self, x: Json, path: Path) -> Result: ...


Compiler = _Callable[[Schema, Context], Validator | None]
