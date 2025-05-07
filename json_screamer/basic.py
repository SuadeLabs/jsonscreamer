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
from typing import List as _List
from typing import Union as _Union

from ._types import _Schema, _Validator
from .compile import register as _register
from .format import FORMATS as _FORMATS

_TYPE_VALIDATORS = {
    "object": lambda x: isinstance(x, dict),
    "array": lambda x: isinstance(x, list),
    "string": lambda x: isinstance(x, str),
    "number": lambda x: (isinstance(x, (float, int)) and not isinstance(x, bool)),
    "integer": lambda x: isinstance(x, int) and not isinstance(x, bool),
    "boolean": lambda x: isinstance(x, bool),
    "null": lambda x: x is None,
}


@_register
def type_(defn: _Schema) -> _Validator:
    value: str = defn["type"]
    return _TYPE_VALIDATORS[value]


@_register
def min_length(defn: _Schema) -> _Validator:
    value: int = defn["minLength"]
    return lambda x: len(x) >= value


@_register
def max_length(defn: _Schema) -> _Validator:
    value: int = defn["maxLength"]
    return lambda x: len(x) <= value


@_register
def pattern(defn: _Schema) -> _Validator:
    value: str = defn["pattern"]
    rex = _re.compile(value)
    return lambda x: bool(rex.match(x))


@_register
def enum(defn: _Schema) -> _Validator:
    value: _List[str] = defn["enum"]
    members = set(value)
    return lambda x: x in members


@_register
def const(defn: _Schema) -> _Validator:
    value: _Any = defn["const"]
    return lambda x: x == value


@_register
def format_(defn: _Schema) -> _Validator:
    value: str = defn["format"]
    if value in _FORMATS:
        return _FORMATS[value]

    _logging.warning(f"Unsupported format ({value}) will not be checked")
    return lambda x: True


@_register
def minimum(defn: _Schema) -> _Validator:
    value: _Union[float, int] = defn["minimum"]
    return lambda x: x >= value


@_register
def exclusive_minimum(defn: _Schema) -> _Validator:
    value: _Union[float, int] = defn["exclusiveMinimum"]
    return lambda x: x > value


@_register
def maximum(defn: _Schema) -> _Validator:
    value: _Union[float, int] = defn["maximum"]
    return lambda x: x <= value


@_register
def exclusive_maximum(defn: _Schema) -> _Validator:
    value: _Union[float, int] = defn["exclusiveMaximum"]
    return lambda x: x < value


@_register
def multiple_of(defn: _Schema) -> _Validator:
    value: _Union[float, int] = defn["multipleOf"]

    def is_multiple(x):
        # More accurate than x % multiplier == 0
        frac = x / value
        return int(frac) == frac

    return is_multiple
