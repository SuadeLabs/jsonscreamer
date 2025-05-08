from __future__ import annotations

import datetime
from unittest import mock

import pytest

from jsonscreamer.basic import (
    _StrictBool,
    const,
    enum,
    exclusive_maximum,
    exclusive_minimum,
    format_,
    max_length,
    maximum,
    min_length,
    minimum,
    multiple_of,
    pattern,
    type_,
)

TYPENAMES = ("boolean", "integer", "null", "number", "string", "zzzzzz")
_VALID = {
    "boolean": (bool,),
    "integer": (int,),
    "null": (type(None),),
    "number": (float, int),
    "string": (str,),
    "array": (list,),
    "object": (dict,),
}


@pytest.mark.parametrize("typename", _VALID)
def test_validate_type(typename):
    validator = type_({"type": typename}, mock.Mock())
    valid = _VALID[typename]

    for value in [
        -100,
        0,
        100,
        None,
        -1.1,
        3.14,
        "lol",
        "",
        datetime.datetime(2018, 1, 1),
        {},
        [],
    ]:
        result = validator(value, path=list("xy"))  # pyright: ignore[reportArgumentType]

        if isinstance(value, valid):
            assert result[0], f"{value} should be a valid {typename}"
        else:
            assert not result[0], f"{value} should not be a valid {typename}"

    for value in (True, False):
        result = validator(value, path=list("xy"))
        if typename == "boolean":
            assert result[0]
        else:
            assert not result[0]


def test_min_max_length():
    defn = {"type": "string", "minLength": 3}
    validator = min_length(defn, mock.Mock())
    assert validator

    assert not validator("fo", [])[0]
    assert validator("foo", [])[0]
    assert validator("fooooo", [])[0]

    defn = {"type": "string", "maxLength": 3}
    validator = max_length(defn, mock.Mock())
    assert validator

    assert validator("fo", [])[0]
    assert validator("foo", [])[0]
    assert not validator("fooooo", [])[0]


def test_pattern():
    defn = {
        "type": "string",
        "minLength": 2,
        "maxLength": 20,
        "pattern": r"^([a-z]+)@([a-z]+)\.com$",
    }
    validator = pattern(defn, mock.Mock())
    assert validator

    assert not validator("", [])[0]
    assert validator("foo@bar.com", [])[0]
    assert not validator(" foo@bar.com", [])[0]
    assert not validator("foo@bar.com etc", [])[0]


def test_min():
    defn = {"type": "number", "minimum": 3}
    validator = minimum(defn, mock.Mock())
    assert validator
    assert not validator(0, [])[0]
    assert validator(3, [])[0]
    assert validator(5, [])[0]
    assert validator(7, [])[0]
    assert validator(10, [])[0]

    defn = {"type": "number", "exclusiveMinimum": 3}
    validator = exclusive_minimum(defn, mock.Mock())
    assert validator
    assert not validator(0, [])[0]
    assert not validator(3, [])[0]
    assert validator(5, [])[0]
    assert validator(7, [])[0]
    assert validator(10, [])[0]


def test_max():
    defn = {"type": "number", "maximum": 7}
    validator = maximum(defn, mock.Mock())
    assert validator
    assert validator(0, [])[0]
    assert validator(3, [])[0]
    assert validator(5, [])[0]
    assert validator(7, [])[0]
    assert not validator(10, [])[0]

    defn = {"type": "number", "exclusiveMaximum": 7}
    validator = exclusive_maximum(defn, mock.Mock())
    assert validator
    assert validator(0, [])[0]
    assert validator(3, [])[0]
    assert validator(5, [])[0]
    assert not validator(7, [])[0]
    assert not validator(10, [])[0]


def test_multiple():
    defn = {"type": "number", "multipleOf": 3}
    validator = multiple_of(defn, mock.Mock())

    assert validator
    assert validator(6, [])[0]
    assert not validator(1, [])[0]
    assert validator(-9, [])[0]
    assert not validator(-7, [])[0]

    defn = {"type": "number", "multipleOf": 3.14}
    validator = multiple_of(defn, mock.Mock())

    assert validator
    assert validator(6.28, [])[0]
    assert not validator(1, [])[0]
    assert validator(-9.42, [])[0]
    assert not validator(-7, [])[0]


def test_enum():
    defn = {"type": "string", "enum": list("ab")}
    validator = enum(defn, mock.Mock())

    assert validator("a", [])[0]
    assert validator("b", [])[0]
    assert not validator("c", [])[0]


def test_const():
    defn = {"type": "string", "const": "a"}
    validator = const(defn, mock.Mock())
    assert validator("a", [])[0]
    assert not validator("b", [])[0]

    defn = {"type": "integer", "const": 3}
    validator = const(defn, mock.Mock())
    assert validator(3, [])[0]
    assert not validator(5, [])[0]


def test_format():
    defn = {"type": "string", "format": "date"}
    validator = format_(defn, mock.Mock())

    assert validator
    assert validator("2020-01-01", [])[0]
    assert not validator("oops", [])[0]

    # Unkown format ignored
    defn = {"type": "string", "format": "oops"}
    validator = format_(defn, mock.Mock())
    assert validator
    assert validator("literally anything", [])[0]


@pytest.mark.parametrize("wrap_testcase", (True, False))
@pytest.mark.parametrize(
    "wrapped,testcase,equal",
    (
        (True, True, True),
        (True, False, False),
        (True, 1, False),
        (True, 0, False),
        (False, False, True),
        (False, 0, False),
        (1, 1, True),
        (1, True, False),
        (1, 5, False),
        (0, 0, True),
        (0, False, False),
        (0, True, False),
        (0, 1, False),
    ),
)
def test_strict_bool(wrapped, testcase, equal, wrap_testcase):
    if wrap_testcase:
        testcase = _StrictBool(testcase)

    if equal:
        assert _StrictBool(wrapped) == testcase
        assert len({_StrictBool(wrapped), testcase}) == 1
    else:
        assert _StrictBool(wrapped) != testcase
        assert len({_StrictBool(wrapped), testcase}) == 2
