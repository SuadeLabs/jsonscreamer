from collections.abc import Callable as _Callable
from typing import Dict as _Dict
from typing import Union as _Union
from typing import TypeVar as _TypeVar

from ._types import _Compiler, _Schema, _Validator, _Error
from .resolve import resolve_refs, register_ids

_CT = _TypeVar("_CT", bound=_Compiler)

__COMPILATION_FUNCTIONS: _Dict[str, _Compiler] = {}


def register(validator: _CT) -> _CT:
    """Register a validator for compiling a given type."""
    __COMPILATION_FUNCTIONS[_name_from_validator(validator)] = validator
    return validator


def _name_from_validator(validator: _Callable) -> str:
    pieces = validator.__name__.strip("_").split("_")
    # JSON Scheam uses camelCase
    for ix, piece in enumerate(pieces[1:]):
        pieces[ix + 1] = piece.capitalize()

    return "".join(pieces)


def compile_(defn: _Union[_Schema, bool], record_path: bool) -> _Validator:
    """Given a schema definition compile a validator function for that schema."""
    if defn is True or defn == {}:
        return lambda x, path: (True, None)
    elif defn is False:
        return lambda x, path: (
            False,
            _Error(path, f"{x} cannot satisfy the false schema"),
        )

    register_ids(defn)
    res: _Schema = resolve_refs(defn, defn)

    validators = []
    for k in res:
        if k in __COMPILATION_FUNCTIONS:
            validator = __COMPILATION_FUNCTIONS[k](res, record_path)
            if validator is not None:
                validators.append(validator)

    def validate(x, path):
        for v in validators:
            result = v(x, path)
            if not result[0]:
                return result

        return True, None

    return validate
