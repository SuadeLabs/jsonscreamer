"""Logical combinators and modifiers of schemas."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._types import ValidationError
from .compile import compile_ as _compile, register as _register

if TYPE_CHECKING:
    from ._types import _Schema, _Validator


@_register
def not_(defn: _Schema, tracker) -> _Validator:
    validator = _compile(defn["not"], tracker)

    def validate(x, path):
        if not validator(x, path):
            return ValidationError(path, f"{x} should not satisfy {defn['not']}", "not")

    return validate


@_register
def all_of(defn: _Schema, tracker) -> _Validator:
    validators = [_compile(s, tracker) for s in defn["allOf"]]

    def validate(x, path):
        for v in validators:
            err = v(x, path)
            if err:
                return err

    return validate


@_register
def any_of(defn: _Schema, tracker) -> _Validator:
    validators = [_compile(s, tracker) for s in defn["anyOf"]]

    def validate(x, path):
        messages = []
        for v in validators:
            err = v(x, path)
            if err is None:
                return None
            messages.append(err.message)

        failures = ", ".join(messages)
        return ValidationError(path, f"{x} failed all conditions: {failures}", "anyOf")

    return validate


@_register
def one_of(defn: _Schema, tracker) -> _Validator:
    validators = [_compile(s, tracker) for s in defn["oneOf"]]

    def validate(x, path):
        passed = 0

        for v in validators:
            err = v(x, path)
            if err is None:
                passed += 1

        if passed != 1:
            return ValidationError(
                path, f"{x} satisfied {passed} (!= 1) of the conditions", "oneOf"
            )

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
        if not if_validator(x, path):  # XXX: no errors => if condition true
            return then_validator(x, path)
        return else_validator(x, path)

    return validate
