from __future__ import annotations

import time

import pytest

from jsonscreamer import Validator
from jsonscreamer.compile import compile_
from jsonscreamer.resolve import RefTracker

POST_BODY = {
    "id": 0,
    "category": {"id": 0, "name": "string"},
    "name": "doggie",
    "photoUrls": ["string"],
    "tags": [{"id": 0, "name": "string"}],
    "status": "available",
}


SCHEMA = {
    "type": "object",
    "required": ["name", "photoUrls"],
    "properties": {
        "id": {
            "type": "integer",
        },
        "name": {
            "type": "string",
        },
        "category": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
            },
            "required": ["id", "name"],
        },
        "photoUrls": {
            "type": "array",
            "items": {"type": "string"},
        },
        "tags": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                },
                "required": ["id", "name"],
            },
        },
        "status": {
            "type": "string",
            "enum": [
                "available",
                "pending",
                "sold",
            ],
        },
    },
}


def test_complex():
    validator = compile_(SCHEMA, RefTracker(SCHEMA))

    assert validator("fish", []) is not None
    assert validator({}, []) is not None
    assert validator(POST_BODY, []) is None
    assert validator({**POST_BODY, "name": 3}, []) is not None
    assert validator({**POST_BODY, "category": {"name": "fish"}}, []) is not None


@pytest.mark.parametrize(
    "variant",
    (
        "jsonschema",
        "jsonscreamer",
        "fastjsonschema",
    ),
)
def test_validate(variant: str):
    if variant == "jsonscreamer":
        validator = Validator(SCHEMA)

    elif variant == "jsonschema":
        from jsonschema import Draft7Validator

        Draft7Validator.check_schema(SCHEMA)

        validator = Draft7Validator(SCHEMA)
    else:
        import fastjsonschema

        class FastValidator:
            def __init__(self):
                self._validator = fastjsonschema.compile(SCHEMA)

            def is_valid(self, item):
                try:
                    self._validator(item)  # type: ignore
                    return True
                except Exception:
                    return False

        validator = FastValidator()

    t0 = time.monotonic()
    for _ in range(10_000):
        validator.is_valid(POST_BODY)
    print(time.monotonic() - t0)
