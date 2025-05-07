from ._types import _Schema, _Validator
from .compile import compile_ as _compile, register as _register


@_register
def not_(defn: _Schema) -> _Validator:
    validator = _compile(defn["not"])
    return lambda x: not validator(x)


@_register
def all_of(defn: _Schema) -> _Validator:
    validators = [_compile(s) for s in defn["allOf"]]
    return lambda x: all(v(x) for v in validators)


@_register
def any_of(defn: _Schema) -> _Validator:
    validators = [_compile(s) for s in defn["anyOf"]]
    return lambda x: any(v(x) for v in validators)


@_register
def one_of(defn: _Schema) -> _Validator:
    validators = [_compile(s) for s in defn["oneOf"]]
    return lambda x: sum(v(x) for v in validators) == 1
