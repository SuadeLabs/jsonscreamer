"""Functions to build validators for basic types of the JSON schema.

For example `string({"type": "string", "enum": ["foo", "bar"]})`
should return a validator function like this:
```
def validate(value):
    return isinstance(value, str) and value in {"foo", "bar"}
```
"""
import logging as _logging
import re as _re
from typing import List as _List, Union as _Union

from ._types import _Validator
from .compile import register as _register
from .format import FORMATS as _FORMATS


@_register
def type_(string: str) -> _Validator:
    validators = {
        "object": lambda x: isinstance(x, dict),
        "array": lambda x: isinstance(x, list),
        "string": lambda x: isinstance(x, str),
        "number": lambda x: (
            isinstance(x, (float, int)) and not isinstance(x, bool)
        ),
        "integer": lambda x: isinstance(x, int) and not isinstance(x, bool),
        "boolean": lambda x: isinstance(x, bool),
        "null": lambda x: x is None,
    }
    return validators[string]


@_register
def min_length(num: int) -> _Validator:
    return lambda x: len(x) >= num


@_register
def max_length(num: int) -> _Validator:
    return lambda x: len(x) <= num


@_register
def pattern(string: str) -> _Validator:
    rex = _re.compile(string)
    return rex.match


@_register
def enum(array: _List[str]) -> _Validator:
    members = set(array)
    return lambda x: x in members


@_register
def format(string: str):
    if string in _FORMATS:
        return _FORMATS[string]

    _logging.warning(f"Unsupported format ({string}) will not be checked")
    return lambda _x: True


@_register
def minimum(num: _Union[float, int]) -> _Validator:
    return lambda x: x >= num


@_register
def exclusive_minimum(num: _Union[float, int]) -> _Validator:
    return lambda x: x > minimum


@_register
def maximum(num: _Union[float, int]) -> _Validator:
    return lambda x: x <= maximum


@_register
def exclusive_maximum(num: _Union[float, int]) -> _Validator:
    return lambda x: x < maximum


@_register
def multiple_of(num: _Union[float, int]) -> _Validator:
    def is_multiple(x):
        # More accurate than x % multiplier == 0
        frac = x / num
        return int(frac) == frac

    return is_multiple
