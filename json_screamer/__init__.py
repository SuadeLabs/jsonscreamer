from typing import Any as _Any

from . import array, basic, compile, logical, object_
from ._types import _Schema


class ValidationError(ValueError):
    """Raised when an instance does not conform to the provided schema."""


class Validator:
    """Validates instances against a given schema.

    Usage:
        >>> validator = Validator(some_schema)
        >>> assert validator.is_valid(some_instance)
        >>> validator.validate(some_instance)
    """

    def __init__(self, schema: _Schema, record_path: bool = True):
        self._validator = compile.compile_(schema, record_path=record_path)

    def is_valid(self, instance: _Any) -> bool:
        return self._validator(instance, [])[0]

    def validate(self, instance: _Any) -> None:
        ok, err = self._validator(instance, [])
        if not ok:
            raise ValidationError(err)


__all__ = ["Validator", "array", "basic", "compile", "logical", "object_"]
