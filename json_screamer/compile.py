from typing import Dict as _Dict

from ._types import _Schema, _Validator

__COMPILATION_FUNCTIONS: _Dict[str, _Validator] = {}


def register(validator: _Validator) -> _Validator:
    """Register a validator for compiling a given type."""
    pieces = validator.__name__.rstrip("_").split("_")
    # JSON Scheam uses camelCase
    for k, piece in enumerate(pieces):
        if k > 0:
            pieces[k] = piece.capitalize()

    name = "".join(pieces)

    __COMPILATION_FUNCTIONS[name] = validator
    return validator


def compile(defn: _Schema):
    if defn in ({}, True):
        return lambda x: True
    elif defn is False:
        return lambda x: False

    else:
        validators = []
        for k, v in defn.items():
            if k in __COMPILATION_FUNCTIONS:
                validators.append(__COMPILATION_FUNCTIONS[k](v))

        return lambda x: all(v(x) for v in validators)
