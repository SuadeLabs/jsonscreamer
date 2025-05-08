from __future__ import annotations

import json
import os
import pathlib

import pytest

from jsonscreamer import Validator

HERE = pathlib.Path(__file__).parent
TEST_SUITE = HERE / "JSON-Schema-Test-Suite" / "tests"
DRAFT7 = TEST_SUITE / "draft7"
TEST_FILES = tuple(fn for fn in os.listdir(DRAFT7) if fn.endswith(".json"))


def _enumerate_test_cases():
    for filename in TEST_FILES:
        with (DRAFT7 / filename).open() as f:
            test_cases = json.load(f)

        for test_case in test_cases:
            yield pytest.param(test_case, id=test_case["description"])


@pytest.mark.usefixtures("_remote_ref_server")
@pytest.mark.parametrize("test_case", _enumerate_test_cases())
def test_draft7(test_case):
    print(test_case["description"])
    schema = test_case["schema"]
    validator = Validator(schema)

    for test in test_case["tests"]:
        if test["valid"]:
            assert validator.is_valid(test["data"]), test["description"]
        else:
            assert not validator.is_valid(test["data"]), test["description"]
