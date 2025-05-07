import json
import os
import pathlib

import pytest

from jsonscreamer import Validator


HERE = pathlib.Path(__file__).parent
TEST_SUITE = HERE / "JSON-Schema-Test-Suite" / "tests"
DRAFT7 = TEST_SUITE / "draft7"
TEST_FILES = tuple(fn for fn in os.listdir(DRAFT7) if fn.endswith(".json"))


@pytest.mark.parametrize("record_path", (True,))  # False))
@pytest.mark.parametrize("filename", TEST_FILES)
def test_all(filename: str, record_path: bool, _remote_ref_server: None):
    with open(DRAFT7 / filename) as f:
        test_cases = json.load(f)

    for test_case in test_cases:
        print(test_case["description"])
        schema = test_case["schema"]
        validator = Validator(schema, record_path)

        for test in test_case["tests"]:
            if test["valid"]:
                assert validator.is_valid(test["data"]), test["description"]
            else:
                assert not validator.is_valid(test["data"]), test["description"]
