from __future__ import annotations

from jsonscreamer import Validator
from jsonscreamer.compile import compile_
from jsonscreamer.resolve import RefTracker
from jsonscreamer.types import Context

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
    validator = compile_(SCHEMA, Context({}, RefTracker(SCHEMA, {})))

    assert list(validator("fish", []))
    assert list(validator({}, []))
    assert list(validator(POST_BODY, [])) == []
    assert list(validator({**POST_BODY, "name": 3}, []))
    assert list(validator({**POST_BODY, "category": {"name": "fish"}}, []))


def test_iter_errors():
    bad_instance = {
        "id": "bad",  # error 1
        "name": 42,  # error 2
        "category": {"id": "nested-bad"},  # errors 3 & 4
        "photoUrls": [1, 2],  # errors 5 and 6
        "tags": [{}, {"id": "spam", "name": "spam"}],  # errors 7, 8, 9
        "status": "sold",
    }
    validator = Validator(SCHEMA)

    errors = list(validator.iter_errors(bad_instance))
    assert len(errors) == 9

    actual_errors = [(e.absolute_path, e.type) for e in errors]
    expected_errors = [
        (("id",), "type"),
        (("name",), "type"),
        (("category", "id"), "type"),
        (("category",), "required"),
        (("photoUrls", 0), "type"),
        (("photoUrls", 1), "type"),
        (("tags", 0), "required"),
        (("tags", 0), "required"),
        (("tags", 1, "id"), "type"),
    ]

    for actual, expected in zip(actual_errors, expected_errors):
        assert actual == expected
