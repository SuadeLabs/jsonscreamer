from __future__ import annotations

import functools
import re as _re
from typing import TYPE_CHECKING

from ._types import ValidationError
from .basic import _guard, _max_len_validator, _min_len_validator
from .compile import compile_ as _compile, register as _register

if TYPE_CHECKING:
    from collections.abc import Iterable as _Iterable
    from typing import TypeVar as _TypeVar

    from ._types import _Json, _Path, _Result, _Schema, _Validator

    _VT = _TypeVar("_VT")


_object_guard = functools.partial(_guard, js_types={"object"}, py_types=dict)


@_register
def max_properties(defn: _Schema, tracker) -> _Validator | None:
    value: int = defn["maxProperties"]
    guard = _object_guard(defn)
    return guard(_max_len_validator(value, "maxProperties"))


@_register
def min_properties(defn: _Schema, tracker) -> _Validator | None:
    value: int = defn["minProperties"]
    guard = _object_guard(defn)
    return guard(_min_len_validator(value, "minProperties"))


@_register
def property_names(defn: _Schema, tracker) -> _Validator | None:
    validator = _compile(defn["propertyNames"], tracker)

    @_object_guard(defn)
    def validate(x, path):
        for key in x:
            result = validator(key, path)
            if not result[0]:
                return result
        return True, None

    return validate


@_register
def required(defn: _Schema, tracker) -> _Validator | None:
    value: list[str] = defn["required"]
    if value:

        @_object_guard(defn)
        def validate(x, path):
            for v in value:
                if v not in x:
                    return False, ValidationError(path, f"{v} is a required property", "required")
            return True, None

        return validate

    return None


@_register
def dependencies(defn: _Schema, tracker) -> _Validator | None:
    value: dict[str, list[str] | _Schema] = defn["dependencies"]
    if not value:
        return None

    checkers = {}

    for dependent, requirement in value.items():
        if isinstance(requirement, list):
            # Has the effect of 'activating' a required directive
            fake_schema = {"required": requirement}
            if "type" in defn:
                fake_schema["type"] = defn["type"]

            checker = required(fake_schema, tracker)
        else:
            checker = _compile(requirement, tracker)

        if checker is not None:
            checkers[dependent] = checker

    @_object_guard(defn)
    def validate(x, path):
        for dependent, checker in checkers.items():
            if dependent in x:
                valid, error = checker(x, path)
                if not valid:
                    return valid, ValidationError(
                        path,
                        f"dependency for {dependent} not satisfied: {error.message}",
                        "dependencies",
                    )

        return True, None

    return validate


def _path_push_iterator(
    path: list[str | int], obj: dict[str, _VT]
) -> _Iterable[tuple[str, _VT]]:
    path.append("")  # front-load memory allocation
    try:
        for key, value in obj.items():
            path[-1] = key
            yield key, value
    finally:
        path.pop()


@_register
def properties(defn: _Schema, tracker) -> _Validator | None:
    value = defn["properties"]
    validators = {k: _compile(v, tracker) for k, v in value.items()}

    @_object_guard(defn)
    def validate(x: _Json, path: _Path) -> _Result:
        for k, v in _path_push_iterator(path, x):  # pyright: ignore[reportArgumentType] (guarded)
            if k in validators:
                result = validators[k](v, path)
                if not result[0]:
                    return result

        return True, None

    return validate


@_register
def pattern_properties(defn: _Schema, tracker) -> _Validator | None:
    value = defn["patternProperties"]
    validators = [(_re.compile(k), _compile(v, tracker)) for k, v in value.items()]

    @_object_guard(defn)
    def validate(x: _Json, path: _Path) -> _Result:
        # ugh...
        for rex, val in validators:
            for k, v in _path_push_iterator(path, x):  # pyright: ignore[reportArgumentType] (guarded)
                if rex.search(k):
                    result = val(v, path)
                    if not result[0]:
                        return result

        return True, None

    return validate


@_register
def additional_properties(defn: _Schema, tracker) -> _Validator | None:
    value = defn["additionalProperties"]
    simple_validator = _compile(value, tracker)

    excluded_names = set(defn.get("properties", ()))
    excluded_rexes = [_re.compile(k) for k in defn.get("patternProperties", ())]

    @_object_guard(defn)
    def validate(x: _Json, path: _Path) -> _Result:
        for k, v in _path_push_iterator(path, x):  # pyright: ignore[reportArgumentType] (guarded)
            if k in excluded_names:
                continue
            if any(r.match(k) for r in excluded_rexes):
                continue
            result = simple_validator(v, path)
            if not result[0]:
                return result

        return True, None

    return validate
