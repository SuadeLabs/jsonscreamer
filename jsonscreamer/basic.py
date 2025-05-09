"""Functions to build validators for basic types of the JSON schema.

For example `enum({"type": "string", "enum": ["foo", "bar"]})`
should return a validator function like this:
```
def validate(value):
    return value in {"foo", "bar"}
```
"""

from __future__ import annotations

import functools
import logging as _logging
import re as _re
from typing import TYPE_CHECKING

from .compile import register as _register
from .types import ValidationError

if TYPE_CHECKING:
    from collections.abc import Collection

    from .types import Context, Json, Path, Result, Schema, Validator

_TYPE_CHECKERS = {
    "object": lambda x: isinstance(x, dict),
    "array": lambda x: isinstance(x, list),
    "string": lambda x: isinstance(x, str),
    "number": lambda x: (isinstance(x, (float, int)) and not isinstance(x, bool)),
    "integer": lambda x: (
        (isinstance(x, int) and not isinstance(x, bool))
        or (isinstance(x, float) and x == int(x))
    ),
    "boolean": lambda x: isinstance(x, bool),
    "null": lambda x: x is None,
}


class _StrictBool:
    """Exists purely because 0 == False in python.

    Casting to this type will ensure that 0 != False, [0] != [False] etc.
    """

    def __init__(self, value: float | bool):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return f"<_StrictBool({self.value!r})>"

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        return (
            self.value is other
            or (
                self.value == other
                and not isinstance(self.value, bool)
                and not isinstance(other, bool)
            )
            or (
                isinstance(other, self.__class__)
                and (
                    self.value is other.value
                    or (
                        self.value == other.value
                        and not isinstance(self.value, bool)
                        and not isinstance(other.value, bool)
                    )
                )
            )
        )

    __req__ = __eq__


__true = _StrictBool(True)
__false = _StrictBool(False)
__one = _StrictBool(1)
__zero = _StrictBool(0)


def _strict_bool_nested(x):
    """Convert possible bools in nested data structures to _StrictBool"""
    if isinstance(x, list):
        return [_strict_bool_nested(v) for v in x]
    elif isinstance(x, dict):
        return {k: _strict_bool_nested(v) for k, v in x.items()}
    elif x is True:
        return __true
    elif x is False:
        return __false
    elif x == 1:
        return __one
    elif x == 0:
        return __zero
    return x


@_register
def type_(defn: Schema, context: Context) -> Validator:
    required_type: str | list[str] = defn["type"]

    if isinstance(required_type, str):
        type_checker = _TYPE_CHECKERS[required_type]

        def validate(x, path):
            if not type_checker(x):
                return ValidationError(
                    path, f"{x} is not of type '{required_type}'", "type"
                )

    elif isinstance(required_type, list):
        type_checkers = [_TYPE_CHECKERS[v] for v in required_type]

        def validate(x, path):
            if not any(t(x) for t in type_checkers):
                return ValidationError(
                    path, f"{x} is not any of the types '{required_type}'", "type"
                )

    return validate


def _min_len_validator(n: int, kind: str) -> Validator:
    def validate(x: Json, path: Path) -> Result:
        if len(x) < n:  # type: ignore (assumption: sized object provided)
            return ValidationError(path, f"{x} is too short (min length {n})", kind)

    return validate


def _max_len_validator(n: int, kind: str) -> Validator:
    def validate(x: Json, path: Path) -> Result:
        if len(x) > n:  # type: ignore (assumption: sized object provided)
            return ValidationError(path, f"{x} is too long (max length {n})", kind)

    return validate


@_register
def min_length(defn: Schema, context: Context) -> Validator | None:
    value: int = defn["minLength"]
    guard = _string_guard(defn)
    return guard(_min_len_validator(value, "minLength"))


@_register
def max_length(defn: Schema, context: Context) -> Validator | None:
    value: int = defn["maxLength"]
    guard = _string_guard(defn)
    return guard(_max_len_validator(value, "maxLength"))


@_register
def pattern(defn: Schema, context: Context) -> Validator | None:
    value: str = defn["pattern"]
    rex = _re.compile(value)

    @_string_guard(defn)
    def validate(x, path):
        if not rex.search(x):
            return ValidationError(
                path, f"'{x}' does not match pattern '{value}'", "pattern"
            )

    return validate


@_register
def enum(defn: Schema, context: Context) -> Validator:
    value: list[object] = defn["enum"]

    members: Collection[object] = list(map(_strict_bool_nested, value))
    try:
        members = set(members)
    except TypeError:
        pass  # Unhashable have to use O(n) lookup

    def validate(x, path):
        if x not in members:
            return ValidationError(path, f"'{x}' is not one of {value}", "enum")

    return validate


@_register
def const(defn: Schema, context: Context) -> Validator:
    value: object = _strict_bool_nested(defn["const"])

    def validate(x, path):
        if x != value:
            return ValidationError(path, f"{x} is not {value}", "const")

    return validate


@_register
def format_(defn: Schema, context: Context) -> Validator | None:
    value: str = defn["format"]
    if value in context.formats:
        format = context.formats[value]

        @_string_guard(defn)
        def validate(x, path):
            if not format(x):
                return ValidationError(
                    path, f"{x} does not match format '{value}", "format"
                )

        return validate

    _logging.warning(f"Unsupported format ({value}) will not be checked")


@_register
def minimum(defn: Schema, context: Context) -> Validator | None:
    value: float | int = defn["minimum"]

    @_number_guard(defn)
    def validate(x, path):
        if x < value:
            return ValidationError(path, f"{x} < {value}", "minimum")

    return validate


@_register
def exclusive_minimum(defn: Schema, context: Context) -> Validator | None:
    value: float | int = defn["exclusiveMinimum"]

    @_number_guard(defn)
    def validate(x, path):
        if x <= value:
            return ValidationError(path, f"{x} <= {value}", "exclusiveMinimum")

    return validate


@_register
def maximum(defn: Schema, context: Context) -> Validator | None:
    value: float | int = defn["maximum"]

    @_number_guard(defn)
    def validate(x, path):
        if x > value:
            return ValidationError(path, f"{x} > {value}", "maximum")

    return validate


@_register
def exclusive_maximum(defn: Schema, context: Context) -> Validator | None:
    value: float | int = defn["exclusiveMaximum"]

    @_number_guard(defn)
    def validate(x, path):
        if x >= value:
            return ValidationError(path, f"{x} >= {value}", "exclusiveMaximum")

    return validate


@_register
def multiple_of(defn: Schema, context: Context) -> Validator | None:
    value: float | int = defn["multipleOf"]

    @_number_guard(defn)
    def validate(x, path):
        # More accurate than x % multiplier == 0
        try:
            frac = x / value
            if int(frac) == frac:
                return None
        except OverflowError:
            pass

        return ValidationError(path, f"{x} is not a multiple of {value}", "multipleOf")

    return validate


def _guard(defn: Schema, js_types: set[str], py_types: tuple[type, ...] | type):
    """Create a type guard suitable for decorating a validator.

    Our type guards are lazy: we pass them the schema, and if they spot a
    type assertion at compile time, we defer to that rather checking again.

    Usage:
        @_guard({"some": "schema"}, {"foo"}, (foo,))
        def validator(...)
            ...
    """

    def decorator(validator: Validator) -> Validator | None:
        # makes no sense, skip the validator entirely
        if "type" in defn and (
            (isinstance(defn["type"], str) and defn["type"] not in js_types)
            or (
                isinstance(defn["type"], list)
                and not js_types.intersection(defn["type"])
            )
        ):
            return None

        # may need a type guard for this validator
        if "type" not in defn or (
            isinstance(defn["type"], list) and not js_types.issuperset(defn["type"])
        ):

            def guarded(x, path):
                if not isinstance(x, py_types):
                    return None
                return validator(x, path)

            return guarded

        # implicit type guard in schema
        return validator

    return decorator


_number_guard = functools.partial(
    _guard, js_types={"number", "integer"}, py_types=(float, int)
)
_string_guard = functools.partial(_guard, js_types={"string"}, py_types=str)
