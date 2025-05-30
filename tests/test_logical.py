from __future__ import annotations

from unittest import mock

from jsonscreamer.format import FORMATS
from jsonscreamer.logical import all_of, any_of, not_, one_of


def test_not():
    assert list(not_({"not": False}, mock.Mock())("spam", [])) == []
    assert list(not_({"not": True}, mock.Mock())("spam", []))


def test_all_of():
    validator = all_of(
        {
            "allOf": [
                {"type": "string"},
                {"format": "email"},
                True,
            ],
        },
        mock.Mock(formats=FORMATS),
    )

    assert list(validator("alice@bob.com", [])) == []
    assert list(validator("alice", []))
    assert list(validator(42, []))


def test_any_of():
    validator = any_of(
        {
            "anyOf": [
                {"type": "string"},
                {"type": "integer"},
                False,
            ]
        },
        mock.Mock(),
    )

    assert list(validator("42", [])) == []
    assert list(validator(42, [])) == []
    assert list(validator(True, []))


def test_one_of():
    validator = one_of(
        {
            "oneOf": [
                {"required": ["spam"]},
                {"required": ["eggs"]},
            ]
        },
        mock.Mock(),
    )

    assert list(validator({"spam": 42}, [])) == []
    assert list(validator({"eggs": 42}, [])) == []
    assert list(validator({"spam": 42, "eggs": 42}, []))
    assert list(validator({}, []))
