"""Functions to build validators for basic types of the JSON schema.

For example `enum({"type": "string", "enum": ["foo", "bar"]})`
should return a validator function like this:
```
def validate(value):
    return value in {"foo", "bar"}
```
"""

from __future__ import annotations

import functools as _functools
import logging as _logging
import re as _re
from typing import TYPE_CHECKING as _TYPE_CHECKING

from .compile import register as _register
from .types import ValidationError

if _TYPE_CHECKING:
    from collections.abc import Callable, Collection, Iterable
    from typing import Any

    from .types import Context, Json, Path, Schema, Validator


class _StrictBool:
    """Exists purely because 0 == False in python.

    Casting to this type will ensure that 0 != False, [0] != [False] etc.
    """

    def __init__(self, value: float | bool) -> None:
        self.value = value

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"<_StrictBool({self.value!r})>"

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: object) -> bool:
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


def _strict_bool_nested(x: object) -> object:
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


def _min_len_validator(n: int, kind: str) -> Validator:
    def validate(x: Json, path: Path) -> Iterable[ValidationError]:
        if len(x) < n:  # type: ignore (assumption: sized object provided)
            yield ValidationError(
                tuple(path), f"{x} is too short (min length {n})", kind
            )

    return validate


def _max_len_validator(n: int, kind: str) -> Validator:
    def validate(x: Json, path: Path) -> Iterable[ValidationError]:
        if len(x) > n:  # type: ignore (assumption: sized object provided)
            yield ValidationError(
                tuple(path), f"{x} is too long (max length {n})", kind
            )

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
    def validate(x: str, path: Path) -> Iterable[ValidationError]:
        if not rex.search(x):
            yield ValidationError(
                tuple(path), f"'{x}' does not match pattern '{value}'", "pattern"
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

    def validate(x: Json, path: Path) -> Iterable[ValidationError]:
        try:
            if x not in members:
                yield ValidationError(
                    tuple(path), f"'{x}' is not one of {value}", "enum"
                )
        except TypeError:  # checking if unhashable type in a set of hashable objects
            yield ValidationError(tuple(path), f"'{x}' is not one of {value}", "enum")

    return validate


@_register
def const(defn: Schema, context: Context) -> Validator:
    value: object = _strict_bool_nested(defn["const"])

    def validate(x: Json, path: Path) -> Iterable[ValidationError]:
        if x != value:
            yield ValidationError(tuple(path), f"{x} is not {value}", "const")

    return validate


@_register
def format_(defn: Schema, context: Context) -> Validator | None:
    value: str = defn["format"]
    if value in context.formats:
        format = context.formats[value]

        @_string_guard(defn)
        def validate(x: str, path: Path) -> Iterable[ValidationError]:
            if not format(x):
                yield ValidationError(
                    tuple(path), f"{x} does not match format '{value}", "format"
                )

        return validate

    _logging.warning(f"Unsupported format ({value}) will not be checked")


@_register
def minimum(defn: Schema, context: Context) -> Validator | None:
    value: float | int = defn["minimum"]

    @_number_guard(defn)
    def validate(x: float, path: Path) -> Iterable[ValidationError]:
        if x < value:
            yield ValidationError(tuple(path), f"{x} < {value}", "minimum")

    return validate


@_register
def exclusive_minimum(defn: Schema, context: Context) -> Validator | None:
    value: float | int = defn["exclusiveMinimum"]

    @_number_guard(defn)
    def validate(x: float, path: Path) -> Iterable[ValidationError]:
        if x <= value:
            yield ValidationError(tuple(path), f"{x} <= {value}", "exclusiveMinimum")

    return validate


@_register
def maximum(defn: Schema, context: Context) -> Validator | None:
    value: float | int = defn["maximum"]

    @_number_guard(defn)
    def validate(x: float, path: Path) -> Iterable[ValidationError]:
        if x > value:
            yield ValidationError(tuple(path), f"{x} > {value}", "maximum")

    return validate


@_register
def exclusive_maximum(defn: Schema, context: Context) -> Validator | None:
    value: float | int = defn["exclusiveMaximum"]

    @_number_guard(defn)
    def validate(x: float, path: Path) -> Iterable[ValidationError]:
        if x >= value:
            yield ValidationError(tuple(path), f"{x} >= {value}", "exclusiveMaximum")

    return validate


@_register
def multiple_of(defn: Schema, context: Context) -> Validator | None:
    value: float | int = defn["multipleOf"]

    @_number_guard(defn)
    def validate(x: float, path: Path) -> Iterable[ValidationError]:
        # More accurate than x % multiplier == 0
        try:
            frac = x / value
            if int(frac) == frac:
                return None
        except OverflowError:
            pass

        yield ValidationError(
            tuple(path), f"{x} is not a multiple of {value}", "multipleOf"
        )

    return validate


def _type_guard(
    defn: Schema, schema_types: tuple[str, ...], py_types: tuple[type, ...] | type
) -> ...:
    """Create a type guard suitable for decorating a validator.

    We are lazy in our type checking: failing a type check at the schema level
    will always short-circuit the validations and stop further checks. This means
    we can be confident these validators will always be passed e.g. str even without
    performing the type check directly.

    Usage:
        @_type_guard(defn, schema_types=("integer",), py_types=int)
        def validator(...)
            ...
    """

    def decorator(
        validator: Callable[[Any, Path], Iterable[ValidationError]],
    ) -> Validator:
        if "type" in defn:
            types = (
                {defn["type"]} if isinstance(defn["type"], str) else set(defn["type"])
            )
            if types.issubset(schema_types):
                # we can omit type check as it's guaranteed by the schema
                return validator  # pyright: ignore[reportReturnType] (protected by schema type)

        @_functools.wraps(validator)
        def guarded(x: Json, path: Path) -> Iterable[ValidationError]:
            if isinstance(x, py_types):
                yield from validator(x, path)

        return guarded

    return decorator


_number_guard = _functools.partial(
    _type_guard, schema_types=("number", "integer"), py_types=(int, float)
)
_string_guard = _functools.partial(_type_guard, schema_types=("string",), py_types=str)
