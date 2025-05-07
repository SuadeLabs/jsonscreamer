import time
import pytest

from jsonscreamer.compile import compile_
from jsonscreamer.resolve import RefTracker
from jsonscreamer import Validator

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

    assert not validator("fish", [])[0]
    assert not validator({}, [])[0]
    assert validator(POST_BODY, [])[0]
    assert not validator({**POST_BODY, "name": 3}, [])[0]
    assert not validator({**POST_BODY, "category": {"name": "fish"}}, [])[0]


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
        fjs_validator = fastjsonschema.compile(SCHEMA)

        class validator:
            @classmethod
            def is_valid(cls, item):
                try:
                    fjs_validator(item)
                    return True
                except Exception:
                    return False

    t0 = time.monotonic()
    for _ in range(10_000):
        validator.is_valid(POST_BODY)
    print(time.monotonic() - t0)
