import datetime

import pytest

from json_screamer.basic import _numeric, boolean, integer, null, number, string

TYPENAMES = ("boolean", "integer", "null", "number", "string", "zzzzzz")


class CompilerBaseTestCase:

    compiler = None
    type_name = None
    valid_types = ()

    def test_raises_on_invalid_type_defn(self):

        for type_ in TYPENAMES:
            if type_ != self.type_name:
                with pytest.raises(AssertionError):
                    self.compiler({"type": type_})

    def test_validate_type(self):
        validator = self.compiler({"type": self.type_name})

        values = [
            True,
            False,
            -100,
            0,
            100,
            None,
            -1.1,
            3.14,
            "lol",
            "",
            datetime.datetime(2018, 1, 1),
        ]

        for value in values:
            if type(value) in self.valid_types:
                assert validator(value), f"{value} should be valid"

            else:
                assert not validator(value), f"{value} should be invalid"


class TestBooleanCompiler(CompilerBaseTestCase):
    compiler = staticmethod(boolean)
    type_name = "boolean"
    valid_types = (bool,)


class TestIntegerCompiler(CompilerBaseTestCase):
    compiler = staticmethod(integer)
    type_name = "integer"
    valid_types = (int,)


class TestNullCompiler(CompilerBaseTestCase):
    compiler = staticmethod(null)
    type_name = "null"
    valid_types = (type(None),)


class TestNumberCompiler(CompilerBaseTestCase):
    compiler = staticmethod(number)
    type_name = "number"
    valid_types = (float, int)


class TestStringCompiler(CompilerBaseTestCase):
    compiler = staticmethod(string)
    type_name = "string"
    valid_types = (str,)

    def test_min_max_length(self):
        defn = {"type": "string", "minLength": 3}
        validator = string(defn)

        assert not validator("fo")
        assert validator("foo")
        assert validator("fooooo")

        defn = {"type": "string", "maxLength": 3}
        validator = string(defn)

        assert validator("fo")
        assert validator("foo")
        assert not validator("fooooo")

        defn = {"type": "string", "minLength": 3, "maxLength": 3}
        validator = string(defn)

        assert not validator("fo")
        assert validator("foo")
        assert not validator("fooooo")

    def test_pattern(self):
        defn = {
            "type": "string",
            "minLength": 2,
            "maxLength": 20,
            "pattern": r"^([a-z]+)@([a-z]+)\.com$",
        }
        validator = string(defn)

        assert not validator("")
        assert validator("foo@bar.com")
        assert not validator(" foo@bar.com")
        assert not validator("foo@bar.com etc")


class TestNumeric:
    def test_min(self):
        defn = {"type": "number", "minimum": 3}
        validator = _numeric(defn)
        assert not validator(0)
        assert validator(3)
        assert validator(5)
        assert validator(7)
        assert validator(10)

        defn = {"type": "number", "minimum": 3, "exclusiveMinimum": False}
        validator = _numeric(defn)
        assert not validator(0)
        assert validator(3)
        assert validator(5)
        assert validator(7)
        assert validator(10)

        defn = {"type": "number", "minimum": 3, "exclusiveMinimum": True}
        validator = _numeric(defn)
        assert not validator(0)
        assert not validator(3)
        assert validator(5)
        assert validator(7)
        assert validator(10)

    def test_max(self):
        defn = {"type": "number", "maximum": 7}
        validator = _numeric(defn)
        assert validator(0)
        assert validator(3)
        assert validator(5)
        assert validator(7)
        assert not validator(10)

        defn = {"type": "number", "maximum": 7, "exclusiveMaximum": False}
        validator = _numeric(defn)
        assert validator(0)
        assert validator(3)
        assert validator(5)
        assert validator(7)
        assert not validator(10)

        defn = {"type": "number", "maximum": 7, "exclusiveMaximum": True}
        validator = _numeric(defn)
        assert validator(0)
        assert validator(3)
        assert validator(5)
        assert not validator(7)
        assert not validator(10)

    def test_min_max(self):
        defn = {"type": "number", "minimum": 3, "maximum": 7}
        validator = _numeric(defn)
        assert not validator(0)
        assert validator(3)
        assert validator(5)
        assert validator(7)
        assert not validator(10)

        defn = {
            "type": "number",
            "minimum": 3,
            "maximum": 7,
            "exclusiveMinimum": True,
        }
        validator = _numeric(defn)
        assert not validator(0)
        assert not validator(3)
        assert validator(5)
        assert validator(7)
        assert not validator(10)

        defn = {
            "type": "number",
            "minimum": 3,
            "maximum": 7,
            "exclusiveMinimum": True,
            "exclusiveMaximum": True,
        }
        validator = _numeric(defn)
        assert not validator(0)
        assert not validator(3)
        assert validator(5)
        assert not validator(7)
        assert not validator(10)

    def test_multiple(self):
        defn = {"type": "number", "multipleOf": 3}
        validator = _numeric(defn)

        assert validator(6)
        assert not validator(1)
        assert validator(-9)
        assert not validator(-7)

        defn = {"type": "number", "multipleOf": 3.14}
        validator = _numeric(defn)

        assert validator(6.28)
        assert not validator(1)
        assert validator(-9.42)
        assert not validator(-7)
