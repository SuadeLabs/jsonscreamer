"""Functions to build validators for basic types of the JSON schema.

For example `enum({"type": "string", "enum": ["foo", "bar"]})`
should return a validator function like this:
```
def validate(value):
    return value in {"foo", "bar"}
```
"""

import logging as _logging
import re as _re
from typing import Any as _Any
from typing import Union as _Union
from collections.abc import Collection as _Collection

from ._types import _Schema, _Validator, _Error
from .compile import register as _register
from .format import FORMATS as _FORMATS


_TYPE_CHECKERS = {
    "object": lambda x: isinstance(x, dict),
    "array": lambda x: isinstance(x, list),
    "string": lambda x: isinstance(x, str),
    "number": lambda x: (isinstance(x, (float, int)) and not isinstance(x, bool)),
    "integer": lambda x: (
        isinstance(x, int)
        and not isinstance(x, bool)
        or isinstance(x, float)
        and x == int(x)
    ),
    "boolean": lambda x: isinstance(x, bool),
    "null": lambda x: x is None,
}


class _StrictBool:
    """Exists purely because 0 == False in python."""

    def __init__(self, value: _Union[int, float, bool]):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return f"<_StrictEquality({repr(self.value)})>"

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        # TODO: make more efficient
        return self.value is other or (
            self.value == other
            and not isinstance(self.value, bool)
            and not isinstance(other, bool)
        )

    __req__ = __eq__


_true = _StrictBool(True)
_false = _StrictBool(False)
_one = _StrictBool(1)
_zero = _StrictBool(0)


def _strict_bool_nested(x):
    if isinstance(x, list):
        return [_strict_bool_nested(v) for v in x]
    elif isinstance(x, dict):
        return {k: _strict_bool_nested(v) for k, v in x.items()}
    elif x is True:
        return _true
    elif x is False:
        return _false
    elif x == 1:
        return _one
    elif x == 0:
        return _zero
    return x


@_register
def type_(defn: _Schema, record_path: bool) -> _Validator:
    value: str | list[str] = defn["type"]

    if isinstance(value, str):
        type_checker = _TYPE_CHECKERS[value]

        def validate(x, path):
            if type_checker(x):
                return True, None
            return False, _Error(path, f"{x} is not of type '{value}'")

    else:
        type_checkers = [_TYPE_CHECKERS[v] for v in value]

        def validate(x, path):
            if any(t(x) for t in type_checkers):
                return True, None
            return False, _Error(path, f"{x} is not any of the types '{value}'")

    return validate


def _min_len_validator(n: int, record_path: bool) -> _Validator:
    def validate(x, path):
        if len(x) >= n:
            return True, None

        return False, _Error(path, f"{x} is too short (min length {n})")

    return validate


def _max_len_validator(n: int, record_path: bool) -> _Validator:
    def validate(x, path):
        if len(x) <= n:
            return True, None

        return False, _Error(path, f"{x} is too long (max length {n})")

    return validate


@_register
def min_length(defn: _Schema, record_path: bool) -> _Validator:
    value: int = defn["minLength"]
    guard = _string_guard(defn)
    return guard(_min_len_validator(value, record_path))


@_register
def max_length(defn: _Schema, record_path: bool) -> _Validator:
    value: int = defn["maxLength"]
    guard = _string_guard(defn)
    return guard(_max_len_validator(value, record_path))


@_register
def pattern(defn: _Schema, record_path: bool) -> _Validator:
    value: str = defn["pattern"]
    rex = _re.compile(value)

    @_string_guard(defn)
    def validate(x, path):
        if not rex.search(x):
            return False, _Error(path, f"'{x}' does not match pattern '{value}'")
        return True, None

    return validate


@_register
def enum(defn: _Schema, record_path: bool) -> _Validator:
    value: list[object] = defn["enum"]

    members: _Collection[object] = list(map(_strict_bool_nested, value))
    try:
        members = set(members)
    except TypeError:
        pass  # Unhashable have to use O(n) lookup

    def validate(x, path):
        if x in members:
            return True, None
        return False, _Error(path, f"'{x}' is not one of {value}")

    return validate


@_register
def const(defn: _Schema, record_path: bool) -> _Validator:
    value: _Any = _strict_bool_nested(defn["const"])

    def validate(x, path):
        if x == value:
            return True, None
        return False, _Error(path, f"{x} is not {value}")

    return validate


@_register
def format_(defn: _Schema, record_path: bool) -> _Validator:
    value: str = defn["format"]
    if value in _FORMATS:

        @_string_guard(defn)
        def validate(x, path):
            if _FORMATS[value](x):
                return True, None

            return False, _Error(path, f"{x} does not match format '{value}")

        return validate

    _logging.warning(f"Unsupported format ({value}) will not be checked")
    return lambda x, path: (True, None)


@_register
def minimum(defn: _Schema, record_path: bool) -> _Validator:
    value: _Union[float, int] = defn["minimum"]

    @_number_guard(defn)
    def validate(x, path):
        if isinstance(x, (float, int)) and x < value:
            return False, _Error(path, f"{x} < {value}")
        return True, None

    return validate


@_register
def exclusive_minimum(defn: _Schema, record_path: bool) -> _Validator:
    value: _Union[float, int] = defn["exclusiveMinimum"]

    @_number_guard(defn)
    def validate(x, path):
        if isinstance(x, (float, int)) and x <= value:
            return False, _Error(path, f"{x} <= {value}")
        return True, None

    return validate


@_register
def maximum(defn: _Schema, record_path: bool) -> _Validator:
    value: _Union[float, int] = defn["maximum"]

    @_number_guard(defn)
    def validate(x, path):
        if isinstance(x, (float, int)) and x > value:
            return False, _Error(path, f"{x} > {value}")
        return True, None

    return validate


@_register
def exclusive_maximum(defn: _Schema, record_path: bool) -> _Validator:
    value: _Union[float, int] = defn["exclusiveMaximum"]

    @_number_guard(defn)
    def validate(x, path):
        if isinstance(x, (float, int)) and x >= value:
            return False, _Error(path, f"{x} >= {value}")
        return True, None

    return validate


@_register
def multiple_of(defn: _Schema, record_path: bool) -> _Validator:
    value: _Union[float, int] = defn["multipleOf"]

    @_number_guard(defn)
    def validate(x, path):
        # More accurate than x % multiplier == 0
        try:
            frac = x / value
            if int(frac) == frac:
                return True, None
        except OverflowError:
            return False, _Error(path, f"{x} is not a multiple of {value}")

        return False, _Error(path, f"{x} is not a multiple of {value}")

    return validate


def _build_guard(type_names: set[str], *python_types: type):

    def guard(defn: _Schema):

        def decorator(validator):
            # makes no sense, no need to validate
            if "type" in defn and (
                (isinstance(defn["type"], str) and defn["type"] not in type_names)
                or (
                    isinstance(defn["type"], list)
                    and not type_names.intersection(defn["type"])
                )
            ):
                return None

            # may need a type guard
            if "type" not in defn or (
                isinstance(defn["type"], list)
                and not type_names.issuperset(defn["type"])
            ):

                def guarded(x, path):
                    if not isinstance(x, python_types):
                        return True, None
                    return validator(x, path)

                return guarded

            return validator

        return decorator

    return guard


_number_guard = _build_guard({"number", "integer"}, float, int)
_string_guard = _build_guard({"string"}, str)
_array_guard = _build_guard({"array"}, list)
_object_guard = _build_guard({"object"}, dict)
