from __future__ import annotations

import pytest

from jsonscreamer import format

_TEST_CASES = {
    "is_date_time": [
        ("2020-01-02T03:04:05+00:00", True),
        ("2020-01-02T03:04:05Z", True),
        ("2020-02-29T03:04:05-03:00", True),
        ("2021-02-29T03:04:05-03:00", False),
        ("2020-01-01 01:01:01Z", False),
        ("2020-01-02", False),
        ("blorp", False),
    ],
    "is_date": [
        ("2020-01-02", True),
        ("2020-01-02Z", False),
        ("2020-02-29", True),
        ("2021-02-29", False),
        ("2020-01", False),
        ("blorp", False),
    ],
    "is_time": [
        ("03:04:05+00:00", True),
        ("03:04:05Z", True),
        ("03:04:05-03:00", True),
        ("T03:04:05-03:00", False),
        (" 01:01:01Z", False),
        ("2020-01-02T03:04:05Z", False),
        ("blorp", False),
    ],
    "is_uuid": [
        ("6e6659ec-4503-4428-9f03-2e2ea4d6c278", True),
        ("6e6659ez-4503-4428-9f03-2e2ea4d6c278", False),
        ("6e6659ec450344289f032e2ea4d6c278", False),
        ("blorp", False),
    ],
    "is_email": [
        ("bob@something.org", True),
        ("bob", False),
    ],
    "is_hostname": [
        ("bla.net", True),
        ("google.com", True),
        ("ドメイン.テスト", False),
        ("", False),
        ("a*", False),
        ("blorp", False),  # FIXME: see below
        ("🐵.com", False),
    ],
    "is_idn_host_name": [
        ("bla.net", True),
        ("google.com", True),
        ("ドメイン.テスト", True),
        ("", False),
        ("a*", False),
        ("blorp", True),  # FIXME: this differs from fqdn - one must be wrong?
        ("🐵.com", False),
    ],
    "is_uri_template": [
        ("https://bla.bla.com/user", True),
        ("https://bla.bla.com/user{/login}", True),
        ("https://bla.bla.com/user{/login", False),
        ("https://bla.bla.com/user{}", False),
    ],
    "is_duration": [
        ("P1000Y12M08DT55H13M56S", True),
        ("P1000Y12M08DT55H13M56.2S", True),
        ("P1000Y12M08DT55H13M56,2S", True),
        ("P10Y10DT10M", True),
        ("P1000Y", True),
        ("PT10M", True),
        ("PT0.5M", True),
        ("P0,5M", True),
        ("P10D10M", False),
        ("PT2S2H", False),
        ("P0,5YT0,5H", False),
        ("P1,000Y0,5M", False),
        ("1Y", False),
        ("P", False),
    ],
    "is_ipv4": [
        ("blorp", False),
        ("10.10.10.10", True),
    ],
    "is_ipv6": [
        ("blorp", False),
        ("10.10.10.10", False),
        ("2001:db8::1000", True),
    ],
    "is_regex": [
        ("(", False),
        ("blorp", True),
        (r"\((.+)", True),
    ],
    "is_uri": [
        ("http://xn--rsum-bpad.example.org", True),
        ("http://ドメイン.テスト", False),
        ("//lol", False),
    ],
    "is_uri_reference": [
        ("//bla", True),
        ("ha ha", False),
        ("//テスト", False),
    ],
    "is_iri": [
        ("http://xn--rsum-bpad.example.org", True),
        ("http://ドメイン.テスト", True),
        ("lol", False),
    ],
    "is_iri_reference": [
        ("//bla", True),
        ("//テスト", True),
        ("ha ha", False),
    ],
    "is_json_pointer": [
        ("/bla/0", True),
        ("/", True),
        ("", True),
        ("1/bob", False),
        ("bob", False),
    ],
    "is_relative_json_pointer": [
        ("1/bla/0", True),
        ("2/", True),
        ("3#", True),  # FIXME: I don't think this is allowed
        ("4", True),
        ("0/", True),
        ("01/", False),
        ("-2/", False),
        ("bob", False),
    ],
}


def get_test_cases():
    for func_name, test_cases in _TEST_CASES.items():
        for value, valid in test_cases:
            yield func_name, value, valid


@pytest.mark.parametrize("func_name,value,valid", get_test_cases())
def test_format(func_name, value, valid):
    func = getattr(format, func_name)
    if valid:
        assert func(value)
    else:
        assert not func(value)


def test_format_lookup():
    assert format.FORMATS["date-time"] == format.is_date_time
    assert format.FORMATS["uuid"] == format.is_uuid


def test_tests():
    # A meta-test to test we're testing all of the formats
    for func in format.FORMATS.values():
        assert _TEST_CASES.get(
            func.__name__
        ), f"You need to write a test for {func.__name__}"
