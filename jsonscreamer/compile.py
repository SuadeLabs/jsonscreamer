from __future__ import annotations

from typing import TYPE_CHECKING as _TYPE_CHECKING

from .types import ValidationError

if _TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from typing import TypeVar

    from .types import Compiler, Context, Json, Path, Schema, Validator

    _CT = TypeVar("_CT", bound=Compiler)


_COMPILATION_FUNCTIONS: dict[str, Compiler] = {}
_TYPE_CHECKERS = {
    "object": lambda x: isinstance(x, dict),
    "array": lambda x: isinstance(x, list),
    "string": lambda x: isinstance(x, str),
    "number": lambda x: (isinstance(x, (float, int)) and not isinstance(x, bool)),
    "integer": lambda x: (
        (isinstance(x, int) and not isinstance(x, bool))
        or (isinstance(x, float) and x == int(x))
    ),
    "boolean": lambda x: isinstance(x, bool),
    "null": lambda x: x is None,
}


def type_(
    defn: Schema, context: Context
) -> Callable[[Json, Path], ValidationError | None]:
    """Create a validator to check the type of an item.

    Unlike other validators we do not yield a value, but return it, since we
    want to break early and not run the other validations if they type check fails.
    """
    required_type: str | list[str] = defn["type"]

    if isinstance(required_type, str):
        type_checker = _TYPE_CHECKERS[required_type]

        def validate(x: Json, path: Path) -> ValidationError | None:
            if not type_checker(x):
                return ValidationError(
                    tuple(path), f"{x} is not of type '{required_type}'", "type"
                )

    elif isinstance(required_type, list):
        type_checkers = [_TYPE_CHECKERS[v] for v in required_type]

        def validate(x: Json, path: Path) -> ValidationError | None:
            if not any(t(x) for t in type_checkers):
                return ValidationError(
                    tuple(path),
                    f"{x} is not any of the types '{required_type}'",
                    "type",
                )

    return validate


def register(validator: _CT) -> _CT:
    """Register a validator for compiling a given type."""
    _COMPILATION_FUNCTIONS[_name_from_validator(validator)] = validator
    return validator


def compile_(defn: Schema | bool, context: Context) -> Validator:
    if defn is True or defn == {}:
        return _true
    elif defn is False:
        return _false
    elif not isinstance(defn, dict):
        raise ValueError("definition must be a boolean or object")

    if "$ref" in defn:
        validate = compile_ref(defn, context)

    else:
        type_validator = None
        validators = []
        for key in defn:
            if key == "type":
                type_validator = type_(defn, context)
            elif key in _COMPILATION_FUNCTIONS:
                validator = _COMPILATION_FUNCTIONS[key](defn, context)
                if validator is not None:
                    validators.append(validator)

        if type_validator:

            def validate(x: Json, path: Path) -> Iterable[ValidationError]:
                if err := type_validator(x, path):
                    yield err
                else:
                    for v in validators:
                        yield from v(x, path)

        else:

            def validate(x: Json, path: Path) -> Iterable[ValidationError]:
                for v in validators:
                    yield from v(x, path)

    return validate


def compile_ref(defn: Schema, context: Context) -> Validator:
    tracker = context.tracker

    with tracker._resolver.in_scope(defn["$ref"]):
        uri = tracker._resolver.get_uri()
        if uri not in tracker._picked:
            tracker.queue(uri)

        def validate(x: Json, path: Path) -> Iterable[ValidationError]:
            yield from tracker.compiled[uri](x, path)

        return validate


def _name_from_validator(validator: Callable) -> str:
    pieces = validator.__name__.strip("_").split("_")
    # JSON Scheam uses camelCase
    for ix, piece in enumerate(pieces[1:]):
        pieces[ix + 1] = piece.capitalize()

    return "".join(pieces)


def _true(x: Json, path: Path) -> tuple[ValidationError, ...]:
    return ()


def _false(x: Json, path: Path) -> tuple[ValidationError]:
    return (ValidationError(tuple(path), f"{x} cannot satisfy false", "false"),)
