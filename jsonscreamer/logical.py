"""Logical combinators and modifiers of schemas."""

from ._types import _Schema, _Validator, _Error
from .compile import compile_one as _compile
from .compile import register as _register


@_register
def not_(defn: _Schema, tracker) -> _Validator:
    validator = _compile(defn["not"], tracker)

    def validate(x, path):
        if not validator(x, path)[0]:
            return True, None
        return False, _Error(path, f"{x} should not satisfy the nested condition")

    return validate


@_register
def all_of(defn: _Schema, tracker) -> _Validator:
    validators = [_compile(s, tracker) for s in defn["allOf"]]

    def validate(x, path):
        for v in validators:
            result = v(x, path)
            if not result[0]:
                return result

        return True, None

    return validate


@_register
def any_of(defn: _Schema, tracker) -> _Validator:
    validators = [_compile(s, tracker) for s in defn["anyOf"]]

    def validate(x, path):
        for v in validators:
            if v(x, path)[0]:
                return True, None

        return False, _Error(path, f"{x} satisfied none of the conditions")

    return validate


@_register
def one_of(defn: _Schema, tracker) -> _Validator:
    validators = [_compile(s, tracker) for s in defn["oneOf"]]

    def validate(x, path):
        passed = 0

        for v in validators:
            if v(x, path)[0]:
                passed += 1

        if passed == 1:
            return True, None

        return False, _Error(path, f"{x} satisfied {passed} of the oneOf conditions")

    return validate


@_register
def if_(defn: _Schema, tracker) -> _Validator | None:
    if_schema = defn["if"]
    then_schema = defn.get("then", True)
    else_schema = defn.get("else", True)

    if then_schema is True and else_schema is True:
        return None

    if_validator = _compile(if_schema, tracker)
    then_validator = _compile(then_schema, tracker)
    else_validator = _compile(else_schema, tracker)

    def validate(x, path):
        if if_validator(x, path)[0]:
            return then_validator(x, path)
        return else_validator(x, path)

    return validate
