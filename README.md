![Build Status](https://github.com/SuadeLabs/jsonscreamer/actions/workflows/ci-pipeline.yml/badge.svg)
![MIT License](https://img.shields.io/badge/LICENSE-MIT-yellow.svg)
![PyPI](https://img.shields.io/pypi/v/jsonscreamer.svg)
![Pythons](https://img.shields.io/pypi/pyversions/jsonscreamer.svg)

![logo-jsonscreamer](https://repository-images.githubusercontent.com/979927857/0a75e558-981a-4d73-8f11-f35f0492e6fe)

Json Screamer is a fast JSON Schema validation library built with a few goals in mind:

1. fast - up to 10x faster than the de-facto standard [jsonschema](https://github.com/python-jsonschema/jsonschema) library
2. correct - full compliance with the json schema test suite, except some gnarly `$ref` edge cases
3. easy to maintain - pure python code, regular function calls etc.

Currently it only handles the Draft 7 spec. If you want a more battle-tested and robust implementation, use [jsonschema](https://github.com/python-jsonschema/jsonschema). If you want an even faster implementation use [fastjsonschema](https://github.com/horejsek/python-fastjsonschema) (up to 2x quicker). The jsonscreamer library sits somewhere in between: more correct than fastjsonschema (e.g. counting `[0, False]` as having unique items) and faster than jsonschema.

Our primary motivations for not using fastjsonschema were correctness, security and ability to customise by writing regular python code. If the idea of dynamically creating source code and calling `exec` on it makes you (or your security team) uncomfortable that's probably a big reason not to use fastjsonschema.


## Benchmarks

The small benchmark from our test suite gives the following numbers (under python3.11):

| library | time | speedup |
| --- | --- | --- |
| jsonschema | 0.568s | 1.0x |
| jsonscreamer | 0.056s | 10.1x |
| fastjsonschema | 0.028s | 20.4x |

In real-world usage with [large schemas](https://github.com/SuadeLabs/fire/blob/master/schemas/account.json) we've seen a 4x speedup over jsonschema and numbers are much closer to fastjsonschema:

| library | throughput | speedup |
| --- | --- | --- |
| jsonschema | 3965it/s | 1.0x |
| jsonscreamer | 16074it/s| 4.1x |
| fastjsonschema | 20683it/s | 5.2x |


## Usage

For good performance, create a single `Validator` instance and call its methods many times:

```python
from jsonscreamer import Validator
from jsonscreamer.format import is_date_time_iso

val = Validator({"type": "string"})
print(val.is_valid(1))  # True
print(val.is_valid("1"))  # False
val.validate(1)  # raises a ValidationError with path, message, type

# Compliant format checkers are run by default, but this one is faster
# if you're OK with python's default ISO8601 instead of RFC3339:
val = Validator(
    {"type": "string", "format": "date-time"},
    formats={"date-time": is_date_time_iso},
)
print(val.is_valid("2020-01-01 01:02:03"))  # True
```


## Test suite compliance

For the Draft 7 schema test suite, we pass **210** out of **212** tests. We consider the two failures to be very niche cases to do with relative `$ref` resolution in the "definitions" section. We are currently more compliant than fastjsonschema, and for almost all real-world schemas this should be considered complete.


## Roadmap

**Resolver:** currently we are using a subclass of fastjsonschema's resolver for ref resolution. We've added a few compatibility hacks to pass more of the json schema test site. We'd like to move to something more robust.

**2019 Draft:** the 2019 draft is on our roadmap once ref resolution is sorted.

**2020 Draft:** the 2020 draft is on our roadmap after the 2019 draft is sorted.

**Earlier Drafts:** we might consider this if there is demand.
