from typing import Any as _Any
from typing import List as _List

from ._types import _Schema, _Validator
from .compile import compile_ as _compile
from .compile import register as _register


@_register
def min_items(defn: _Schema) -> _Validator:
    value: int = defn["minItems"]
    return lambda x: len(x) >= value


@_register
def max_items(defn: _Schema) -> _Validator:
    value: int = defn["maxItems"]
    return lambda x: len(x) >= value


def _unique_checker(x: _List[_Any]) -> bool:
    try:
        return len(x) == len(set(x))
    except TypeError:
        # No choice but to fall back to O(n^2) algorithm
        seen = []
        for item in x:
            if item in seen:
                return False
            seen.append(item)
        return True


@_register
def unique_items(defn: _Schema) -> _Validator:
    if defn["uniqueItems"]:
        return _unique_checker
    return lambda x: True


@_register
def prefix_items(defn: _Schema) -> _Validator:
    value: _List[_Schema] = defn["prefixItems"]
    validators = [_compile(d) for d in value]
    return lambda x: all(v(i) for v, i in zip(validators, x))


@_register
def items(defn: _Schema) -> _Validator:
    offset = len(defn.get("prefixItems", ()))
    validator = _compile(defn["items"])
    return lambda x: all(validator(i) for i in x[offset:])


@_register
def contains(defn: _Schema) -> _Validator:
    validator = _compile(defn["contains"])
    return lambda x: any(validator(i) for i in x)


@_register
def max_contains(defn: _Schema) -> _Validator:
    if "contains" not in defn:
        return lambda x: True

    validator = _compile(defn["contains"])
    value: int = defn["maxContains"]
    return lambda x: sum(1 for i in x if validator(i)) <= value


@_register
def min_contains(defn: _Schema) -> _Validator:
    if "contains" not in defn:
        return lambda x: True

    validator = _compile(defn["contains"])
    value: int = defn["minContains"]
    return lambda x: sum(1 for i in x if validator(i)) >= value
