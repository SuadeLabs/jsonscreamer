from __future__ import annotations

from typing import TYPE_CHECKING

from .types import ValidationError

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import TypeVar

    from .types import Compiler, Context, Schema

    _CT = TypeVar("_CT", bound=Compiler)


_COMPILATION_FUNCTIONS: dict[str, Compiler] = {}


def active_properties():
    return frozenset(_COMPILATION_FUNCTIONS)


def register(validator: _CT) -> _CT:
    """Register a validator for compiling a given type."""
    _COMPILATION_FUNCTIONS[_name_from_validator(validator)] = validator
    return validator


def compile_(defn: Schema | bool, context: Context):
    if defn is True or defn == {}:
        return _true
    elif defn is False:
        return _false
    elif not isinstance(defn, dict):
        raise ValueError("definition must be a boolean or object")

    if "$ref" in defn:
        validate = compile_ref(defn, context)

    else:
        validators = []
        for key in defn:
            if key in _COMPILATION_FUNCTIONS:
                validator = _COMPILATION_FUNCTIONS[key](defn, context)
                if validator is not None:
                    validators.append(validator)

        def validate(x, path):
            for v in validators:
                yield from v(x, path)

    return validate


def compile_ref(defn: Schema, context: Context):
    tracker = context.tracker

    with tracker._resolver.in_scope(defn["$ref"]):
        uri = tracker._resolver.get_uri()
        if uri not in tracker._picked:
            tracker.queue(uri)

        def validate(x, path):
            yield from tracker.compiled[uri](x, path)

        return validate


def _name_from_validator(validator: Callable) -> str:
    pieces = validator.__name__.strip("_").split("_")
    # JSON Scheam uses camelCase
    for ix, piece in enumerate(pieces[1:]):
        pieces[ix + 1] = piece.capitalize()

    return "".join(pieces)


def _true(x, path):
    return ()


def _false(x, path):
    return (ValidationError(path, f"{x} cannot satisfy false", "false"),)
