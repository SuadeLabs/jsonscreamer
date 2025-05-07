import re as _re
from typing import Dict as _Dict
from typing import Optional as _Optional
from typing import Iterable as _Iterable
from typing import TypeVar as _TypeVar

from ._types import _Result, _Schema, _Validator, _Error
from .basic import _max_len_validator, _min_len_validator, _object_guard
from .compile import compile_ as _compile
from .compile import register as _register

_VT = _TypeVar("_VT")


@_register
def max_properties(defn: _Schema, record_path: bool) -> _Validator:
    value: int = defn["maxProperties"]
    guard = _object_guard(defn)
    return guard(_max_len_validator(value, record_path))


@_register
def min_properties(defn: _Schema, record_path: bool) -> _Validator:
    value: int = defn["minProperties"]
    guard = _object_guard(defn)
    return guard(_min_len_validator(value, record_path))


@_register
def property_names(defn: _Schema, record_path: bool) -> _Validator:
    validator = _compile(defn["propertyNames"], record_path=False)

    @_object_guard(defn)
    def validate(x, path):
        for key in x:
            result = validator(key, path)
            if not result[0]:
                return result
        return True, None

    return validate


@_register
def required(defn: _Schema, record_path: bool) -> _Optional[_Validator]:
    value: list[str] = defn["required"]
    if value:

        @_object_guard(defn)
        def validate(x, path):
            for v in value:
                if v not in x:
                    return False, _Error(path, f"{v} is a required property")
            return True, None

        return validate

    return None


@_register
def dependencies(defn: _Schema, record_path: bool) -> _Optional[_Validator]:
    value: _Dict[str, list[str] | _Schema] = defn["dependencies"]
    if not value:
        return None

    checkers = {}

    for dependent, requirement in value.items():
        if isinstance(requirement, list):
            # Has the effect of 'activating' a required directive
            fake_schema = {"required": requirement}
            if "type" in defn:
                fake_schema["type"] = defn["type"]

            checker = required(fake_schema, record_path=False)
        else:
            checker = _compile(requirement, record_path=False)

        if checker is not None:
            checkers[dependent] = checker

    @_object_guard(defn)
    def validate(x, path):
        for dependent, checker in checkers.items():
            if dependent in x:
                valid, error = checker(x, path)
                if not valid:
                    return valid, _Error(
                        path,
                        f"dependency for {dependent} not satisfied: {error.message}",
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


def _no_op_iterator(
    path: list[str | int], obj: dict[str, _VT]
) -> _Iterable[tuple[str, _VT]]:
    return obj.items()


@_register
def properties(defn: _Schema, record_path: bool) -> _Validator:
    value = defn["properties"]
    validators = {k: _compile(v, record_path) for k, v in value.items()}

    if record_path:
        iterator = _path_push_iterator
    else:
        iterator = _no_op_iterator

    @_object_guard(defn)
    def validate(x: _Schema, path) -> _Result:
        for k, v in iterator(path, x):
            if k in validators:
                result = validators[k](v, path)
                if not result[0]:
                    return result

        return True, None

    return validate


@_register
def pattern_properties(defn: _Schema, record_path: bool) -> _Validator:
    value = defn["patternProperties"]
    validators = [(_re.compile(k), _compile(v, record_path)) for k, v in value.items()]

    if record_path:
        iterator = _path_push_iterator
    else:
        iterator = _no_op_iterator

    @_object_guard(defn)
    def validate(x: _Schema, path: list[str | int]) -> _Result:
        # ugh...
        for rex, val in validators:
            for k, v in iterator(path, x):
                if rex.search(k):
                    result = val(v, path)
                    if not result[0]:
                        return result

        return True, None

    return validate


@_register
def additional_properties(defn: _Schema, record_path: bool) -> _Validator:
    value = defn["additionalProperties"]
    simple_validator = _compile(value, record_path)

    excluded_names = set(defn.get("properties", ()))
    excluded_rexes = [_re.compile(k) for k in defn.get("patternProperties", ())]

    if record_path:
        iterator = _path_push_iterator
    else:
        iterator = _no_op_iterator

    @_object_guard(defn)
    def validate(x: _Schema, path: list[str | int]) -> _Result:
        for k, v in iterator(path, x):
            if k in excluded_names:
                continue
            if any(r.match(k) for r in excluded_rexes):
                continue
            result = simple_validator(v, path)
            if not result[0]:
                return result

        return True, None

    return validate
