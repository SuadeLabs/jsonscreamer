from __future__ import annotations

import json as _json
import pathlib as _pathlib
from typing import TYPE_CHECKING as _TYPE_CHECKING

from . import array, basic, compile, logical, object_
from .format import FORMATS as _FORMATS
from .resolve import HANDLERS as _HANDLERS, RefTracker as _RefTracker
from .types import Context as _Context

if _TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from typing import Any

    from .types import Format, Json, Schema, ValidationError

    Handler = Callable[[str], Json]


class Validator:
    """Validates instances against a given schema.

    Usage:
        >>> validator = Validator(some_schema)
        >>> assert validator.is_valid(some_instance)
        >>> validator.validate(some_instance)
    """

    _metavalidator = None

    def __init__(
        self,
        schema: Schema | bool = True,
        formats: dict[str, Format] | bool = True,
        handlers: dict[str, Handler] | None = None,
        check_schema: bool = True,
    ) -> None:
        if check_schema:
            type(self).check_schema(schema)

        if formats is False:
            formats = {}  # completely disable format checking
        elif formats is True:
            formats = _FORMATS  # use default format checking
        else:
            formats = _FORMATS | formats  # extend with custom formats

        handlers = _HANDLERS | (handlers or {})
        tracker = _RefTracker(schema, handlers=handlers)
        self._context = _Context(formats=formats, tracker=tracker)

        # NOTE: if there were no $ref item in the schema, we wouldn't need a tracker,
        # it just obscures the logic. However, given that refs exist and can be circular
        # we have to track where we are and where we've been within the schemas:
        while tracker:
            uri = tracker.pop()
            with tracker._resolver.resolving(uri) as sub_defn:
                tracker.compiled[uri] = compile.compile_(sub_defn, self._context)

        self._validator = tracker.entrypoint

    # Simple validation functions:

    def is_valid(self, instance: Any) -> bool:
        """Check whether the given instance is valid."""
        return not any(self._validator(instance, []))

    def validate(self, instance: Any) -> None:
        """Validate the instance and raise a ValidationError if it is invalid."""
        for err in self._validator(instance, []):
            raise err

    def iter_errors(self, instance: Any) -> Iterator[ValidationError]:
        """Iterate over all validation errors for the instance."""
        yield from self._validator(instance, [])

    # These are a little more baroque - but basically aimed at loading / creating
    # a schema validator at most once:

    @classmethod
    def check_schema(cls, schema: Any) -> None:
        """Validate the schema and raise a ValidationError if it is invalid.

        Handles only the draft 07 spec.
        """
        return cls.metavalidator().validate(schema)

    @classmethod
    def metavalidator(cls) -> Validator:
        """Return the Validator for draft 07 schemas."""
        if cls._metavalidator is None:
            here = _pathlib.Path(__file__).parent
            with (here / "_metaschemas" / "draft07.json").open() as f:
                metaschema = _json.load(f)

            cls._metavalidator = cls(metaschema, check_schema=False)

        return cls._metavalidator


__all__ = ["Validator", "array", "basic", "compile", "logical", "object_"]
