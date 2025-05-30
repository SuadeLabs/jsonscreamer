from __future__ import annotations

import functools
from typing import TYPE_CHECKING as _TYPE_CHECKING

from .basic import (
    _max_len_validator,
    _min_len_validator,
    _strict_bool_nested,
    _type_guard,
)
from .compile import compile_ as _compile, register as _register
from .types import ValidationError

if _TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import TypeVar

    from .types import Context, Json, Path, Schema, Validator

    _T = TypeVar("_T")


_array_guard = functools.partial(_type_guard, schema_types=("array",), py_types=list)


@_register
def min_items(defn: Schema, context: Context) -> Validator | None:
    value: int = defn["minItems"]
    guard = _array_guard(defn)
    return guard(_min_len_validator(value, "minItems"))


@_register
def max_items(defn: Schema, context: Context) -> Validator | None:
    value: int = defn["maxItems"]
    guard = _array_guard(defn)
    return guard(_max_len_validator(value, "maxItems"))


def _unique_checker(
    x: Json, path: list[str | int], _second_run: bool = False
) -> Iterable[ValidationError]:
    # Happy path first, then fall back to more expensive expressions
    if _second_run:
        x = _strict_bool_nested(x)  # type: ignore

    ok = True
    try:
        ok = len(x) == len(set(x))  # type: ignore (guarded)
    except TypeError:
        # No choice but to fall back to O(n^2) algorithm
        seen = []
        for item in x:  # type: ignore (guarded)
            if item in seen:
                ok = False
                break
            seen.append(item)

    if not ok and not _second_run:
        # Edge case: both booleans and integers in the array
        # checking this false positive will be slower..
        ok = not any(_unique_checker(x, path, _second_run=True))

    if not ok:
        yield ValidationError(tuple(path), f"{x} has repeated items", "uniqueItems")


@_register
def unique_items(defn: Schema, context: Context) -> Validator | None:
    if defn["uniqueItems"]:
        guard = _array_guard(defn)
        return guard(_unique_checker)


def _path_push_iterator(
    path: Path, iterable: Iterable[_T], offset: int = 0
) -> Iterable[_T]:
    path.append(0)  # front-load memory allocation
    try:
        for ix, item in enumerate(iterable):
            path[-1] = ix + offset
            yield item
    finally:
        path.pop()


@_register
def items(defn: Schema, context: Context) -> Validator | None:
    value: list[Schema] | Schema = defn["items"]
    if isinstance(value, list):
        validators = [_compile(d, context) for d in value]

        @_array_guard(defn)
        def validate(x: list[Json], path: Path) -> Iterable[ValidationError]:
            for v, i in _path_push_iterator(path, zip(validators, x)):
                yield from v(i, path)

    else:
        validator = _compile(value, context)

        @_array_guard(defn)
        def validate(x: list[Json], path: Path) -> Iterable[ValidationError]:
            for i in _path_push_iterator(path, x):
                yield from validator(i, path)

    return validate


@_register
def additional_items(defn: Schema, context: Context) -> Validator | None:
    item_spec: dict | list = defn.get("items", {})
    if isinstance(item_spec, dict):
        # this is a no-op
        return None

    offset = len(item_spec)
    validator = _compile(defn["additionalItems"], context)

    @_array_guard(defn)
    def validate(x: list[Json], path: Path) -> Iterable[ValidationError]:
        for i in _path_push_iterator(path, x[offset:], offset):
            yield from validator(i, path)

    return validate


@_register
def contains(defn: Schema, context: Context) -> Validator | None:
    validator = _compile(defn["contains"], context)
    if validator is None:
        return None

    @_array_guard(defn)
    def validate(x: list[Json], path: Path) -> Iterable[ValidationError]:
        for i in x:
            if not any(validator(i, path)):  # XXX: no error => item is in list
                return ()

        return (
            ValidationError(
                tuple(path),
                f"{x} did not contain any items satisfying {defn['contains']}",
                "contains",
            ),
        )

    return validate


@_register
def max_contains(defn: Schema, context: Context) -> Validator | None:
    if "contains" not in defn:
        return None

    validator = _compile(defn["contains"], context)
    value: int = defn["maxContains"]

    @_array_guard(defn)
    def validate(x: list[Json], path: Path) -> Iterable[ValidationError]:
        total = sum(not any(validator(i, path)) for i in x)
        if total <= value:
            return ()

        return (
            ValidationError(
                tuple(path),
                f"{x} contains more than {value} items satisfying {defn['contains']}",
                "maxContains",
            ),
        )

    return validate


@_register
def min_contains(defn: Schema, context: Context) -> Validator | None:
    if "contains" not in defn:
        return None

    validator = _compile(defn["contains"], context)
    value: int = defn["minContains"]

    @_array_guard(defn)
    def validate(x: list[Json], path: Path) -> Iterable[ValidationError]:
        total = sum(not any(validator(i, path)) for i in x)
        if total >= value:
            return ()

        return (
            ValidationError(
                tuple(path),
                f"{x} contains less than {value} items satisfying {defn['contains']}",
                "minContains",
            ),
        )

    return validate
