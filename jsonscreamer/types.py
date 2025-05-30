from __future__ import annotations

from collections.abc import (
    Callable as _Callable,
    Mapping as _Mapping,
    Sequence as _Sequence,
)
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any as _Any, Protocol as _Protocol

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .resolve import RefTracker

Json = None | bool | int | float | str | _Sequence["Json"] | _Mapping[str, "Json"]
Path = list[str | int]
ImmutablePath = tuple[str | int, ...]
Format = _Callable[[str], bool]


class ValidationError(ValueError):
    """Raised when an instance does not conform to the provided schema."""

    def __init__(self, absolute_path: ImmutablePath, message: str, type: str) -> None:
        self.absolute_path = absolute_path
        self.message = message
        self.type = type


@dataclass
class Context:
    formats: dict[str, Format]
    tracker: RefTracker


Schema = dict[str, _Any]
Result = ValidationError | None


class Validator(_Protocol):
    def __call__(self, x: Json, path: Path) -> Iterable[ValidationError]: ...


Compiler = _Callable[[Schema, Context], Validator | None]
