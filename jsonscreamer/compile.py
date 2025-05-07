from collections.abc import Callable as _Callable
from typing import Dict as _Dict
from typing import TypeVar as _TypeVar

from ._types import _Compiler, _Schema, _Error
from .resolve import RefTracker

_CT = _TypeVar("_CT", bound=_Compiler)

_COMPILATION_FUNCTIONS: _Dict[str, _Compiler] = {}


def active_properties():
    return frozenset(_COMPILATION_FUNCTIONS)


def register(validator: _CT) -> _CT:
    """Register a validator for compiling a given type."""
    _COMPILATION_FUNCTIONS[_name_from_validator(validator)] = validator
    return validator



def compile_(defn: _Schema | bool, tracker: RefTracker):
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
            if key in _COMPILATION_FUNCTIONS:
                validator = _COMPILATION_FUNCTIONS[key](defn, tracker)
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
        uri = tracker._resolver.get_uri()
        if uri not in tracker._picked:
            tracker.queue(uri)

        def validate(x, path):
            return tracker.compiled[uri](x, path)

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
