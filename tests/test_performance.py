from __future__ import annotations

import time

import pytest

from jsonscreamer import Validator

from .test_complex import POST_BODY, SCHEMA


@pytest.mark.parametrize(
    "variant",
    (
        "jsonschema",
        "jsonscreamer",
        "fastjsonschema",
    ),
)
def test_validate(variant: str):
    if variant == "jsonscreamer":
        validator = Validator(SCHEMA)

    elif variant == "jsonschema":
        from jsonschema import Draft7Validator

        Draft7Validator.check_schema(SCHEMA)

        validator = Draft7Validator(SCHEMA)
    else:
        import fastjsonschema

        class FastValidator:
            def __init__(self):
                self._validator = fastjsonschema.compile(SCHEMA)

            def is_valid(self, item):
                try:
                    self._validator(item)  # type: ignore
                    return True
                except Exception:
                    return False

        validator = FastValidator()

    t0 = time.monotonic()
    for _ in range(10_000):
        validator.is_valid(POST_BODY)
    print(time.monotonic() - t0)
