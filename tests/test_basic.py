import datetime

import pytest

from json_screamer.basic import (
    const,
    enum,
    format_,
    exclusive_maximum,
    exclusive_minimum,
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
    validator = type_({"type": typename})
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
        if isinstance(value, valid):
            assert validator(value), f"{value} should be a valid {typename}"
        else:
            assert not validator(value), f"{value} should not be a valid {typename}"

    for value in (True, False):
        if typename == "boolean":
            assert validator(value)
        else:
            assert not validator(value)


def test_min_max_length():
    defn = {"type": "string", "minLength": 3}
    validator = min_length(defn)

    assert not validator("fo")
    assert validator("foo")
    assert validator("fooooo")

    defn = {"type": "string", "maxLength": 3}
    validator = max_length(defn)

    assert validator("fo")
    assert validator("foo")
    assert not validator("fooooo")


def test_pattern():
    defn = {
        "type": "string",
        "minLength": 2,
        "maxLength": 20,
        "pattern": r"^([a-z]+)@([a-z]+)\.com$",
    }
    validator = pattern(defn)

    assert not validator("")
    assert validator("foo@bar.com")
    assert not validator(" foo@bar.com")
    assert not validator("foo@bar.com etc")


def test_min():
    defn = {"type": "number", "minimum": 3}
    validator = minimum(defn)
    assert not validator(0)
    assert validator(3)
    assert validator(5)
    assert validator(7)
    assert validator(10)

    defn = {"type": "number", "exclusiveMinimum": 3}
    validator = exclusive_minimum(defn)
    assert not validator(0)
    assert not validator(3)
    assert validator(5)
    assert validator(7)
    assert validator(10)


def test_max():
    defn = {"type": "number", "maximum": 7}
    validator = maximum(defn)
    assert validator(0)
    assert validator(3)
    assert validator(5)
    assert validator(7)
    assert not validator(10)

    defn = {"type": "number", "exclusiveMaximum": 7}
    validator = exclusive_maximum(defn)
    assert validator(0)
    assert validator(3)
    assert validator(5)
    assert not validator(7)
    assert not validator(10)


def test_multiple():
    defn = {"type": "number", "multipleOf": 3}
    validator = multiple_of(defn)

    assert validator(6)
    assert not validator(1)
    assert validator(-9)
    assert not validator(-7)

    defn = {"type": "number", "multipleOf": 3.14}
    validator = multiple_of(defn)

    assert validator(6.28)
    assert not validator(1)
    assert validator(-9.42)
    assert not validator(-7)


def test_enum():
    defn = {"type": "string", "enum": list("ab")}
    validator = enum(defn)

    assert validator("a")
    assert validator("b")
    assert not validator("c")


def test_const():
    defn = {"type": "string", "const": "a"}
    validator = const(defn)
    assert validator("a")
    assert not validator("b")

    defn = {"type": "integer", "const": 3}
    validator = const(defn)
    assert validator(3)
    assert not validator(5)


def test_format():
    defn = {"type": "string", "format": "date"}
    validator = format_(defn)

    assert validator("2020-01-01")
    assert not validator("oops")

    # Unkown format ignored
    defn = {"type": "string", "format": "oops"}
    validator = format_(defn)
    assert validator("literally anything")
