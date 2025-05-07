from __future__ import annotations

from jsonscreamer.compile import _name_from_validator


def test_name_from_validator() -> None:

    def not_():
        pass

    def a_long_name():
        pass

    def x_123_a():
        pass

    assert _name_from_validator(not_) == "not"
    assert _name_from_validator(a_long_name) == "aLongName"
    assert _name_from_validator(x_123_a) == "x123A"
