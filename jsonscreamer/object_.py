from __future__ import annotations

import functools as _functools
import re as _re
from typing import TYPE_CHECKING

from .basic import _max_len_validator, _min_len_validator, _type_guard
from .compile import compile_ as _compile, register as _register
from .types import ValidationError

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import TypeVar

    from .types import Context, Json, Path, Schema, Validator

    _VT = TypeVar("_VT")

_object_guard = _functools.partial(_type_guard, schema_types=("object",), py_types=dict)


@_register
def max_properties(defn: Schema, context: Context) -> Validator:
    value: int = defn["maxProperties"]
    guard = _object_guard(defn)
    return guard(_max_len_validator(value, "maxProperties"))


@_register
def min_properties(defn: Schema, context: Context) -> Validator:
    value: int = defn["minProperties"]
    guard = _object_guard(defn)
    return guard(_min_len_validator(value, "minProperties"))


@_register
def property_names(defn: Schema, context: Context) -> Validator:
    validator = _compile(defn["propertyNames"], context)

    @_object_guard(defn)
    def validate(x: dict[str, Json], path: Path) -> ...:
        for key in x:
            yield from validator(key, path)

    return validate


@_register
def required(defn: Schema, context: Context) -> Validator | None:
    value: list[str] = defn["required"]
    if value:

        @_object_guard(defn)
        def validate(x: dict[str, Json], path: Path) -> ...:
            for v in value:
                if v not in x:
                    yield ValidationError(
                        tuple(path), f"{v} is a required property", "required"
                    )

        return validate

    return None


@_register
def dependencies(defn: Schema, context: Context) -> Validator | None:
    value: dict[str, list[str] | Schema] = defn["dependencies"]
    if not value:
        return None

    checkers = {}

    for dependent, requirement in value.items():
        if isinstance(requirement, list):
            # Has the effect of 'activating' a required directive
            fake_schema = {"required": requirement}
            if "type" in defn:
                fake_schema["type"] = defn["type"]

            checker = required(fake_schema, context)
        else:
            checker = _compile(requirement, context)

        if checker is not None:
            checkers[dependent] = checker

    @_object_guard(defn)
    def validate(x: dict[str, Json], path: Path) -> ...:
        for dependent, checker in checkers.items():
            if dependent in x:
                for err in checker(x, path):
                    yield ValidationError(
                        tuple(path),
                        f"dependency for {dependent} not satisfied: {err.message}",
                        "dependencies",
                    )

        return None

    return validate


def _path_push_iterator(
    path: list[str | int], obj: dict[str, _VT]
) -> Iterable[tuple[str, _VT]]:
    path.append("")  # front-load memory allocation
    try:
        for key, value in obj.items():
            path[-1] = key
            yield key, value
    finally:
        path.pop()


@_register
def properties(defn: Schema, context: Context) -> Validator:
    value = defn["properties"]
    validators = {k: _compile(v, context) for k, v in value.items()}

    @_object_guard(defn)
    def validate(x: dict[str, Json], path: Path) -> Iterable[ValidationError]:
        for k, v in _path_push_iterator(path, x):
            if k in validators:
                yield from validators[k](v, path)

    return validate


@_register
def pattern_properties(defn: Schema, context: Context) -> Validator:
    value = defn["patternProperties"]
    validators = [(_re.compile(k), _compile(v, context)) for k, v in value.items()]

    @_object_guard(defn)
    def validate(x: dict[str, Json], path: Path) -> Iterable[ValidationError]:
        # ugh...
        for rex, val in validators:
            for k, v in _path_push_iterator(path, x):
                if rex.search(k):
                    yield from val(v, path)

    return validate


@_register
def additional_properties(defn: Schema, context: Context) -> Validator:
    value = defn["additionalProperties"]
    simple_validator = _compile(value, context)

    excluded_names = set(defn.get("properties", ()))
    excluded_rexes = [_re.compile(k) for k in defn.get("patternProperties", ())]

    @_object_guard(defn)
    def validate(x: dict[str, Json], path: Path) -> Iterable[ValidationError]:
        for k, v in _path_push_iterator(path, x):
            if k in excluded_names:
                continue
            if any(r.match(k) for r in excluded_rexes):
                continue
            yield from simple_validator(v, path)

    return validate
