from __future__ import annotations

from typing import TYPE_CHECKING

from . import array, basic, compile, logical, object_
from .format import FORMATS as _FORMATS
from .resolve import RefTracker as _RefTracker
from .types import Context as _Context

if TYPE_CHECKING:
    from typing import Any as _Any

    from .types import Format, Schema


class Validator:
    """Validates instances against a given schema.

    Usage:
        >>> validator = Validator(some_schema)
        >>> assert validator.is_valid(some_instance)
        >>> validator.validate(some_instance)
    """

    def __init__(
        self, schema: Schema | bool = True, formats: dict[str, Format] | None = None
    ):
        formats = _FORMATS | (formats or {})
        tracker = _RefTracker(schema)
        self._context = _Context(formats=formats, tracker=tracker)

        while tracker:
            uri = tracker.pop()
            with tracker._resolver.resolving(uri) as sub_defn:
                tracker.compiled[uri] = compile.compile_(sub_defn, self._context)

        self._validator = tracker.entrypoint

    def is_valid(self, instance: _Any) -> bool:
        return not self._validator(instance, [])

    def validate(self, instance: _Any) -> None:
        err = self._validator(instance, [])
        if err is not None:
            # I didn't set out to write go-like python, but it turns out
            # errors as return values are just neater in this context
            raise err


__all__ = ["Validator", "array", "basic", "compile", "logical", "object_"]
