from __future__ import annotations

from unittest import mock

from jsonscreamer.logical import all_of, any_of, not_, one_of


def test_not():
    assert not_({"not": False}, mock.Mock())("spam", [])[0] is True
    assert not_({"not": True}, mock.Mock())("spam", [])[0] is False


def test_all_of():
    validator = all_of(
        {
            "allOf": [
                {"type": "string"},
                {"format": "email"},
                True,
            ],
        },
        mock.Mock(),
    )

    assert validator("alice@bob.com", [])[0]
    assert not validator("alice", [])[0]
    assert not validator(42, [])[0]


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

    assert validator("42", [])[0]
    assert validator(42, [])[0]
    assert not validator(True, [])[0]


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

    assert validator({"spam": 42}, [])[0]
    assert validator({"eggs": 42}, [])[0]
    assert not validator({"spam": 42, "eggs": 42}, [])[0]
    assert not validator({}, [])[0]
