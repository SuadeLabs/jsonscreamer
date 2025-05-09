from __future__ import annotations

from unittest import mock

from jsonscreamer.format import FORMATS
from jsonscreamer.logical import all_of, any_of, not_, one_of


def test_not():
    assert not_({"not": False}, mock.Mock())("spam", []) is None
    assert not_({"not": True}, mock.Mock())("spam", []) is not None


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

    assert validator("alice@bob.com", []) is None
    assert validator("alice", []) is not None
    assert validator(42, []) is not None


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

    assert validator("42", []) is None
    assert validator(42, []) is None
    assert validator(True, []) is not None


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

    assert validator({"spam": 42}, []) is None
    assert validator({"eggs": 42}, []) is None
    assert validator({"spam": 42, "eggs": 42}, []) is not None
    assert validator({}, []) is not None
