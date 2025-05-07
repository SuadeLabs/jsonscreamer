from collections.abc import Callable as _Callable
from typing import Dict as _Dict
from typing import Union as _Union
from typing import TypeVar as _TypeVar

from ._types import _Compiler, _Schema, _Validator, _Error
from .resolve import RefTracker

_CT = _TypeVar("_CT", bound=_Compiler)

__COMPILATION_FUNCTIONS: _Dict[str, _Compiler] = {}


def active_properties():
    return frozenset(__COMPILATION_FUNCTIONS)


def register(validator: _CT) -> _CT:
    """Register a validator for compiling a given type."""
    __COMPILATION_FUNCTIONS[_name_from_validator(validator)] = validator
    return validator


def compile_(defn: _Union[_Schema, bool], tracker: RefTracker) -> _Validator:
    """Given a schema definition compile a validator function for that schema."""
    while tracker.queued:
        uri, name = tracker.queued.pop()
        tracker._picked.add(uri)

        with tracker._resolver.resolving(uri) as sub_defn:
            tracker._compiled[uri] = compile_one(sub_defn, tracker)

    return tracker.entrypoint


def compile_one(defn, tracker):
    if defn is True or defn == {}:
        return _true
    elif defn is False:
        return _false
    elif not isinstance(defn, dict):
        raise ValueError("definition must be a boolean or object")

    if "$ref" in defn:
        validate = compile_ref(defn, tracker)

    else:
        validators = []
        for key in defn:
            if key in __COMPILATION_FUNCTIONS:
                validator = __COMPILATION_FUNCTIONS[key](defn, tracker)
                if validator is not None:
                    validators.append(validator)

        def validate(x, path):
            for v in validators:
                result = v(x, path)
                if not result[0]:
                    return result
            return True, None

    return validate


def compile_ref(defn: _Schema, tracker: RefTracker):
    with tracker._resolver.in_scope(defn['$ref']):
        name = tracker._resolver.get_scope_name()
        uri = tracker._resolver.get_uri()
        if uri not in tracker._picked:
            tracker.queued.append((uri, name))

        def validate(x, path):
            return tracker._compiled[uri](x, path)

        return validate


def _name_from_validator(validator: _Callable) -> str:
    pieces = validator.__name__.strip("_").split("_")
    # JSON Scheam uses camelCase
    for ix, piece in enumerate(pieces[1:]):
        pieces[ix + 1] = piece.capitalize()

    return "".join(pieces)


def _true(x, path):
    return True, None


def _false(x, path):
    return False, _Error(path, "cannot satisfy the false schema")
