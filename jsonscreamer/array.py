from typing import Optional as _Optional
from typing import Iterable as _Iterable
from typing import TypeVar as _TypeVar

from ._types import _Result, _Schema, _Validator, _Error
from .basic import (
    _max_len_validator,
    _min_len_validator,
    _strict_bool_nested,
    _array_guard,
)
from .compile import compile_one as _compile
from .compile import register as _register

_T = _TypeVar("_T")


@_register
def min_items(defn: _Schema, tracker) -> _Validator:
    value: int = defn["minItems"]
    guard = _array_guard(defn)
    return guard(_min_len_validator(value))


@_register
def max_items(defn: _Schema, tracker) -> _Validator:
    value: int = defn["maxItems"]
    guard = _array_guard(defn)
    return guard(_max_len_validator(value))


def _unique_checker(x: list[object], path: list[str | int], _second_run=False) -> _Result:
    # Happy path first, then fall back to more expensive expressions
    if _second_run:
        x = _strict_bool_nested(x)

    result = True
    try:
        result = len(x) == len(set(x))
    except TypeError:
        # No choice but to fall back to O(n^2) algorithm
        seen = []
        for item in x:
            if item in seen:
                result = False
                break
            seen.append(item)

    if not result and not _second_run:
        # Edge case: both booleans and integers in the array
        # checking this false positive will be slower..
        result, _ = _unique_checker(x, path, _second_run=True)

    error = None if result else _Error(path, f"{x} has repeated items")
    return result, error


@_register
def unique_items(defn: _Schema, tracker) -> _Optional[_Validator]:
    if defn["uniqueItems"]:
        guard = _array_guard(defn)
        return guard(_unique_checker)
    return None


def _path_push_iterator(
    path: list[str | int], iterable: _Iterable[_T], offset: int = 0
) -> _Iterable[_T]:
    path.append(0)  # front-load memory allocation
    try:
        for ix, item in enumerate(iterable):
            path[-1] = ix + offset
            yield item
    finally:
        path.pop()


@_register
def items(defn: _Schema, tracker) -> _Validator:
    value: list[_Schema] | _Schema = defn["items"]
    if isinstance(value, list):
        validators = [_compile(d, tracker) for d in value]

        @_array_guard(defn)
        def validate(x, path):
            for v, i in _path_push_iterator(path, zip(validators, x)):
                result = v(i, path)
                if not result[0]:
                    return result

            return True, None

    else:
        validator = _compile(value, tracker)

        @_array_guard(defn)
        def validate(x, path):
            for i in _path_push_iterator(path, x):
                result = validator(i, path)
                if not result[0]:
                    return result

            return True, None

    return validate


@_register
def additional_items(defn: _Schema, tracker) -> _Validator:
    item_spec: dict | list = defn.get("items", {})
    if isinstance(item_spec, dict):
        # this is a no-op
        return lambda x, path: (True, None)

    offset = len(item_spec)
    validator = _compile(defn["additionalItems"], tracker)

    @_array_guard(defn)
    def validate(x, path):
        for i in _path_push_iterator(path, x[offset:], offset):
            result = validator(i, path)
            if not result[0]:
                return result

        return True, None

    return validate


@_register
def contains(defn: _Schema, tracker) -> _Validator:
    validator = _compile(defn["contains"], tracker)

    @_array_guard(defn)
    def validate(x, path):
        for i in x:
            if validator(i, path)[0]:
                return True, None

        return False, _Error(
            path, f"{x} did not contain any items satisfying the condition"
        )

    return validate


@_register
def max_contains(defn: _Schema, tracker) -> _Optional[_Validator]:
    if "contains" not in defn:
        return None

    validator = _compile(defn["contains"], tracker)
    value: int = defn["maxContains"]

    @_array_guard(defn)
    def validate(x, path):
        total = sum(1 for i in x if validator(i, path)[0])
        if total <= value:
            return True, None

        return False, _Error(
            path, f"{x} contains more than {value} items satisfying the condition"
        )

    return validate


@_register
def min_contains(defn: _Schema, tracker) -> _Optional[_Validator]:
    if "contains" not in defn:
        return None

    validator = _compile(defn["contains"], tracker)
    value: int = defn["minContains"]

    @_array_guard(defn)
    def validate(x, path):
        total = sum(1 for i in x if validator(i, path)[0])
        if total >= value:
            return True

        return False, _Error(
            path, f"{x} contains less than {value} items satisfying the condition"
        )

    return validate
