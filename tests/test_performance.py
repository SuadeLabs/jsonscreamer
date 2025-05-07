import time
import pytest

from json_screamer.compile import compile_
from json_screamer import Validator

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
    validator = compile_(SCHEMA, record_path=True)

    assert not validator("fish", [])[0]
    assert not validator({}, [])[0]
    assert validator(POST_BODY, [])[0]
    assert not validator({**POST_BODY, "name": 3}, [])[0]
    assert not validator({**POST_BODY, "category": {"name": "fish"}}, [])[0]


@pytest.mark.parametrize(
    "variant,record_path",
    (
        ("old", True),
        ("new", True),
        ("new", False),
    ),
)
def test_validate(variant: str, record_path: bool):
    if variant == "new":
        validator = Validator(SCHEMA, record_path=record_path)
    else:
        from jsonschema import Draft7Validator

        Draft7Validator.check_schema(SCHEMA)

        validator = Draft7Validator(SCHEMA)

    t0 = time.monotonic()
    for _ in range(10_000):
        validator.is_valid(POST_BODY)
    print(time.monotonic() - t0)
