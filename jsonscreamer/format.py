"""Format validators.

Example: ...
"""

from __future__ import annotations

import ipaddress as _ipaddress
import re as _re
from datetime import date as _date, datetime as _datetime
from uuid import UUID as _UUID


def is_date_time(x: str) -> bool:
    """Date-time, see RFC 3339, section 5.6"""
    try:
        _datetime.strptime(x, "%Y-%m-%dT%H:%M:%S%z")
        return True
    except ValueError:
        return False


def is_date_time_iso(x: str) -> bool:
    """Date-time, using python's fromisoformat, rather than RFC 3339.

    Typically this is 4x faster than the spec-compliant behaviour.
    """
    try:
        _datetime.fromisoformat(x)
        return True
    except ValueError:
        return False


def is_time(x: str) -> bool:
    return is_date_time("1970-01-01T" + x)


def is_date(x: str) -> bool:
    try:
        _date.fromisoformat(x)
        return True
    except ValueError:
        return False


_EMAIL_REX = _re.compile(r"^(?!.*\.\..*@)[^@.][^@]*(?<!\.)@[^@]+\.[^@]+\Z")


def is_email(x: str) -> bool:
    """Internet email address, see RFC 5322, section 3.4.1."""
    return bool(_EMAIL_REX.fullmatch(x))


def is_ipv4(x: str) -> bool:
    """IPv4 address, see RFC 2673, section 3.2."""
    try:
        _ipaddress.IPv4Address(x)
        return True
    except ValueError:
        return False


def is_ipv6(x: str) -> bool:
    """IPv6 address, see RFC 2373, section 2.2."""
    try:
        address = _ipaddress.IPv6Address(x)
        return not getattr(address, "scope_id", "")  # ???
    except ValueError:
        return False


def is_regex(x: str) -> bool:
    try:
        _re.compile(x)
        return True
    except _re.error:
        return False


def is_uuid(x: str) -> bool:
    try:
        _UUID(x)
    except ValueError:
        return False

    # Python doesn't require seperators, RFC does.
    return all(x[position] == "-" for position in (8, 13, 18, 23))


try:
    import idna as _idna
    import jsonpointer as _jsonpointer
    import rfc3987 as _rfc3987
    import uri_template as _uri_template
    from fqdn import FQDN as _FQDN

    def is_hostname(x: str) -> bool:
        """Internet host name, see RFC 1034, section 3.1."""
        try:
            return _FQDN(x).is_valid  # pyright: ignore[reportReturnType] (this is really a bool)
        except ValueError:
            return False

    def is_idn_host_name(x: str) -> bool:
        """Internationalized domain name, see RFC 5891."""
        try:
            _idna.encode(x)
            return True
        except ValueError:
            return False

    def is_uri(x: str) -> bool:
        """A universal resource identifier (URI), see RFC3986."""
        try:
            _rfc3987.parse(x, rule="URI")
            return True
        except ValueError:
            return False

    def is_uri_reference(x: str) -> bool:
        """A URI reference, see RFC3986, section 4.1."""
        try:
            _rfc3987.parse(x, rule="URI_reference")
            return True
        except ValueError:
            return False

    def is_iri(x: str) -> bool:
        """An internationalized resource identifier (IRI), see RFC3987."""
        try:
            _rfc3987.parse(x, rule="IRI")
            return True
        except ValueError:
            return False

    def is_iri_reference(x: str) -> bool:
        """An IRI reference, see RFC3987, section 2.2."""
        try:
            _rfc3987.parse(x, rule="IRI_reference")
            return True
        except ValueError:
            return False

    def is_json_pointer(x: str) -> bool:
        """A JSON pointer, see RFC 6901."""
        try:
            return bool(_jsonpointer.JsonPointer(x))
        except _jsonpointer.JsonPointerException:
            return False

    def is_uri_template(x: str) -> bool:
        try:
            return _uri_template.validate(x)
        except ValueError:
            return False

except ImportError:
    pass


def is_relative_json_pointer(x: str) -> bool:
    """A JSON pointer relative to the current document.

    See https://tools.ietf.org/html/draft-handrews-relative-json-pointer-01#section-3
    """
    non_negative_integer, rest = [], ""
    for i, character in enumerate(x):
        if character.isdigit():
            # digits with a leading "0" are not allowed
            if i > 0 and int(x[i - 1]) == 0:
                return False

            non_negative_integer.append(character)
            continue

        if not non_negative_integer:
            return False

        rest = x[i:]
        break

    return (rest == "#") or is_json_pointer(rest)


__duration_date_order = _re.compile("^P([0-9.,]+Y)?([0-9.,]+M)?([0-9.,]+D)?$")
__duration_time_order = _re.compile("^([0-9.,]+H)?([0-9.,]+M)?([0-9.,]+S)?$")
# Only the final part of the duration can be fractional
__duration_regular = "[0-9]+[A-Z]"
__duration_final = "[0-9]+([.,][0-9]+)?[A-Z]"
__duration_fraction_order = _re.compile(
    f"^P({__duration_regular})*T?({__duration_regular})*{__duration_final}$"
)


def is_duration(x: str) -> bool:
    if len(x) < 2 or x[0] != "P":
        return False

    if not __duration_fraction_order.fullmatch(x):
        return False

    pieces = x.split("T")
    if len(pieces) == 1:
        return bool(__duration_date_order.fullmatch(x))
    elif len(pieces) == 2:
        return bool(
            pieces[1]
            and __duration_date_order.fullmatch(pieces[0])
            and __duration_time_order.fullmatch(pieces[1])
        )
    else:
        return False


FORMATS = {}
for name, obj in list(locals().items()):
    if name == "is_date_time_iso":
        continue  # not loaded by default

    # is_some_thing is the "some-thing" validator
    pieces = name.split("_")
    if pieces[0] == "is":
        key = "-".join(pieces[1:])
        FORMATS[key] = obj
