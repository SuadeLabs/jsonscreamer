from typing import Any as _Any

from . import array, basic, compile, logical, object_
from ._types import _Schema

from .resolve import RefTracker


class ValidationError(ValueError):
    """Raised when an instance does not conform to the provided schema."""


class Validator:
    """Validates instances against a given schema.

    Usage:
        >>> validator = Validator(some_schema)
        >>> assert validator.is_valid(some_instance)
        >>> validator.validate(some_instance)
    """

    def __init__(self, schema: _Schema = True):
        self._tracker = RefTracker(schema)

        while self._tracker:
            uri = self._tracker.pop()
            with self._tracker._resolver.resolving(uri) as sub_defn:
                self._tracker.compiled[uri] = compile.compile_(sub_defn, self._tracker)

        self._validator = self._tracker.entrypoint

    def is_valid(self, instance: _Any) -> bool:
        return self._validator(instance, [])[0]

    def validate(self, instance: _Any) -> None:
        ok, err = self._validator(instance, [])
        if not ok:
            raise ValidationError(err)


__all__ = ["Validator", "array", "basic", "compile", "logical", "object_"]
