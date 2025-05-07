from typing import Dict as _Dict, Union as _Union

from ._types import _Schema, _Compiler
from .resolve import resolve_refs

__COMPILATION_FUNCTIONS: _Dict[str, _Compiler] = {}


def register(validator: _Compiler) -> _Compiler:
    """Register a validator for compiling a given type."""
    pieces = validator.__name__.rstrip("_").split("_")
    # JSON Scheam uses camelCase
    for k, piece in enumerate(pieces):
        if k > 0:
            pieces[k] = piece.capitalize()

    name = "".join(pieces)

    __COMPILATION_FUNCTIONS[name] = validator
    return validator


def compile_(defn: _Union[_Schema, bool]):
    if defn in ({}, True):
        return lambda x: True
    elif defn is False:
        return lambda x: False

    res: _Schema = resolve_refs(defn, defn)

    validators = []
    for k in res:
        if k in __COMPILATION_FUNCTIONS:
            validator = __COMPILATION_FUNCTIONS[k](res)
            if validator is not None:
                validators.append(validator)

    return lambda x: all(v(x) for v in validators)
