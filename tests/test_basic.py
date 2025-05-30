from __future__ import annotations

import datetime
from unittest import mock

import pytest

from jsonscreamer import Validator
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
)
from jsonscreamer.compile import type_
from jsonscreamer.format import FORMATS

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
        result = validator(value, list("xy"))  # pyright: ignore[reportArgumentType]

        if isinstance(value, valid):
            assert not result, f"{value} should be a valid {typename}"
        else:
            assert result, f"{value} should not be a valid {typename}"

    for value in (True, False):
        result = validator(value, list("xy"))
        if typename == "boolean":
            assert not result
        else:
            assert result


def test_min_max_length():
    defn = {"type": "string", "minLength": 3}
    validator = min_length(defn, mock.Mock())
    assert validator

    assert list(validator("fo", []))
    assert list(validator("foo", [])) == []
    assert list(validator("fooooo", [])) == []

    defn = {"type": "string", "maxLength": 3}
    validator = max_length(defn, mock.Mock())
    assert validator

    assert list(validator("fo", [])) == []
    assert list(validator("foo", [])) == []
    assert list(validator("fooooo", []))


def test_pattern():
    defn = {
        "type": "string",
        "minLength": 2,
        "maxLength": 20,
        "pattern": r"^([a-z]+)@([a-z]+)\.com$",
    }
    validator = pattern(defn, mock.Mock())
    assert validator

    assert list(validator("", []))
    assert list(validator("foo@bar.com", [])) == []
    assert list(validator(" foo@bar.com", []))
    assert list(validator("foo@bar.com etc", []))


def test_min():
    defn = {"type": "number", "minimum": 3}
    validator = minimum(defn, mock.Mock())
    assert validator
    assert list(validator(0, []))
    assert list(validator(3, [])) == []
    assert list(validator(5, [])) == []
    assert list(validator(7, [])) == []
    assert list(validator(10, [])) == []

    defn = {"type": "number", "exclusiveMinimum": 3}
    validator = exclusive_minimum(defn, mock.Mock())
    assert validator
    assert list(validator(0, []))
    assert list(validator(3, []))
    assert list(validator(5, [])) == []
    assert list(validator(7, [])) == []
    assert list(validator(10, [])) == []


def test_max():
    defn = {"type": "number", "maximum": 7}
    validator = maximum(defn, mock.Mock())
    assert validator
    assert list(validator(0, [])) == []
    assert list(validator(3, [])) == []
    assert list(validator(5, [])) == []
    assert list(validator(7, [])) == []
    assert list(validator(10, []))

    defn = {"type": "number", "exclusiveMaximum": 7}
    validator = exclusive_maximum(defn, mock.Mock())
    assert validator
    assert list(validator(0, [])) == []
    assert list(validator(3, [])) == []
    assert list(validator(5, [])) == []
    assert list(validator(7, []))
    assert list(validator(10, []))


def test_multiple():
    defn = {"type": "number", "multipleOf": 3}
    validator = multiple_of(defn, mock.Mock())

    assert validator
    assert list(validator(6, [])) == []
    assert list(validator(1, []))
    assert list(validator(-9, [])) == []
    assert list(validator(-7, []))

    defn = {"type": "number", "multipleOf": 3.14}
    validator = multiple_of(defn, mock.Mock())

    assert validator
    assert list(validator(6.28, [])) == []
    assert list(validator(1, []))
    assert list(validator(-9.42, [])) == []
    assert list(validator(-7, []))


def test_enum():
    defn = {"type": "string", "enum": list("ab")}
    validator = enum(defn, mock.Mock())

    assert list(validator("a", [])) == []
    assert list(validator("b", [])) == []
    assert list(validator("c", []))


def test_const():
    defn = {"type": "string", "const": "a"}
    validator = const(defn, mock.Mock())
    assert list(validator("a", [])) == []
    assert list(validator("b", []))

    defn = {"type": "integer", "const": 3}
    validator = const(defn, mock.Mock())
    assert list(validator(3, [])) == []
    assert list(validator(5, []))


def test_format():
    defn = {"type": "string", "format": "date"}
    validator = format_(defn, mock.Mock(formats=FORMATS))

    assert validator
    assert list(validator("2020-01-01", [])) == []
    assert list(validator("oops", []))

    # Unkown format ignored
    defn = {"type": "string", "format": "oops"}
    validator = format_(defn, mock.Mock(formats=FORMATS))
    assert validator is None


def test_format_overrides():
    defn = {
        "properties": {
            "squishy": {"type": "string", "format": "squishy"},
            "date": {"type": "string", "format": "date"},
            "email": {"type": "string", "format": "email"},
        }
    }

    def is_squishy(x: str) -> bool:
        return "squishy" in x

    validator = Validator(defn, formats={"date": is_squishy, "squishy": is_squishy})
    # new format is respected
    assert validator.is_valid({"squishy": "squishy!"})
    assert not validator.is_valid({"squishy": "2020-01-01"})
    # override is respected
    assert validator.is_valid({"date": "squishy!"})
    assert not validator.is_valid({"date": "2020-01-01"})
    # other formats are retained
    assert validator.is_valid({"email": "x@y.z"})
    assert not validator.is_valid({"email": "squishy!"})

    # override is not permanent
    validator = Validator(defn)
    assert validator.is_valid({"date": "2020-01-01"})


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
