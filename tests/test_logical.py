from json_screamer.logical import all_of, any_of, not_, one_of


def test_not():
    assert not_({"not": False}, True)("spam", [])[0] is True
    assert not_({"not": True}, True)("spam", [])[0] is False


def test_all_of():
    validator = all_of(
        {
            "allOf": [
                {"type": "string"},
                {"format": "email"},
                True,
            ],
        },
        record_path=True,
    )

    assert validator("alice@bob.com", [])[0]
    assert not validator("alice", [])[0]
    assert not validator(42, [])[0]


def test_any_of():
    validator = any_of(
        {
            "anyOf": [
                {"type": "string"},
                {"type": "integer"},
                False,
            ]
        },
        record_path=True,
    )

    assert validator("42", [])[0]
    assert validator(42, [])[0]
    assert not validator(True, [])[0]


def test_one_of():
    validator = one_of(
        {
            "oneOf": [
                {"required": ["spam"]},
                {"required": ["eggs"]},
            ]
        },
        record_path=True,
    )

    assert validator({"spam": 42}, [])[0]
    assert validator({"eggs": 42}, [])[0]
    assert not validator({"spam": 42, "eggs": 42}, [])[0]
    assert not validator({}, [])[0]
