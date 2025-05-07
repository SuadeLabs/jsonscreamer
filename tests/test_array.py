from jsonscreamer import Validator


def test_contains():
    schema = {"contains": {"type": "integer"}}
    validator = Validator(schema)

    assert not validator.is_valid([{}])
    assert not validator.is_valid([{}, "1"])
    assert validator.is_valid([{}, False, 1])


def test_max_contains():
    schema = {
        "contains": {"type": "integer"},
        "maxContains": 2,
    }
    validator = Validator(schema)

    assert not validator.is_valid([[], False])
    assert validator.is_valid([1])
    assert validator.is_valid([1, 2])
    assert not validator.is_valid([1, 2, 3])
