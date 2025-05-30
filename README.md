![Build Status](https://github.com/SuadeLabs/jsonscreamer/actions/workflows/ci-pipeline.yml/badge.svg)
![MIT License](https://img.shields.io/badge/LICENSE-MIT-yellow.svg)
![PyPI](https://img.shields.io/pypi/v/jsonscreamer.svg)
![Pythons](https://img.shields.io/pypi/pyversions/jsonscreamer.svg)

![logo-jsonscreamer](https://repository-images.githubusercontent.com/979927857/0a75e558-981a-4d73-8f11-f35f0492e6fe)

Json Screamer is a fast JSON Schema validation library built with a few goals in mind:

1. fast - up to 10x faster than the de-facto standard [jsonschema](https://github.com/python-jsonschema/jsonschema) library
2. correct - full compliance with the json schema test suite, except some gnarly `$ref` edge cases
3. easy to maintain - pure python code, regular function calls etc.
4. iteration over all errors for a given schema

Currently it only handles the Draft 7 spec. If you want a more battle-tested and robust implementation, use [jsonschema](https://github.com/python-jsonschema/jsonschema). If you want an even faster implementation use [fastjsonschema](https://github.com/horejsek/python-fastjsonschema) (up to 2x quicker). The jsonscreamer library sits somewhere in between: more correct than fastjsonschema (e.g. counting `[0, False]` as having unique items) and faster than jsonschema.

Our primary motivations for not using fastjsonschema were correctness, security and ability to customise by writing regular python code. If the idea of dynamically creating source code and calling `exec` on it makes you (or your security team) uncomfortable that's probably a big reason not to use fastjsonschema.


## Benchmarks

The small benchmark from our test suite gives the following numbers (under python3.11):

| library | time | speedup |
| --- | --- | --- |
| jsonschema | 0.566s | 1.0x |
| jsonscreamer | 0.066s | 8.5x |
| fastjsonschema | 0.028s | 20.4x |

In real-world usage with [large schemas](https://github.com/SuadeLabs/fire/blob/master/schemas/account.json) we've seen an ~14x speedup over jsonschema. For these benchmarks, since fastjsonschema accepts nonsense datetimes like `2025-19-39T29:00:00Z` as valid by default, it made sense to explicitly set all 3 validators' date-time format checkers as the same (we'd need to do this extra check anyway if using fastjsonschema):

| library | throughput | speedup |
| --- | --- | --- |
| jsonschema | 4358it/s | 1.0x |
| jsonscreamer | 60264it/s| 13.8x |
| fastjsonschema | 120549it/s | 27.7x |


## Usage

For good performance, create a single `Validator` instance and call its methods many times:

```python
>>> from jsonscreamer import Validator
>>> from jsonscreamer.format import is_date_time_iso
>>> Validator.check_schema({"type": "string"})
>>> val = Validator({"type": "string"})
>>> val.is_valid(1)
False
>>> val.is_valid("1")
True
>>> list(val.iter_errors("1"))
[]
>>> val.validate(1)
Traceback (most recent call last):
  ...
jsonscreamer.types.ValidationError: ((), "1 is not of type 'string'", 'type')

>>> # Compliant format checkers are run by default, but this one is faster
>>> # if you're OK with python's default ISO8601 instead of RFC3339:
>>> schema = {"type": "string", "format": "date-time"}
>>> val = Validator(schema, formats={"date-time": is_date_time_iso})
>>> val.is_valid("2020-01-01 01:02:03")
True

```

The `Validator` class has 3 primary methods:

- `is_valid(instance)` which returns True or False
- `validate(instance)` which will raise a `ValidationError` if any error is encountered
- `iter_errors(instance)` which gives an iterator of `ValidationErrors` for the instance

and the `ValidationError` class itself has the following properties:

- `absolute_path`: the path to the error within the item (e.g. `("spam", 0, "eggs")`)
- `message`: a human-readable error message
- `type`: the type of validation error


### Custom formats

By default jsonscreamer installs with only a subset of format validators (those which require no external dependencies), you can install all format checkers via `pip install jsonscreamer[all-formats]`. The `Validator` class also takes a `formats` parameter which you can set to `False` to disable all formats, or provide a dictionary of your own formats to override or add to the existing formats.

When providing a dictionary of custom formats, the the keys are the format names (like "email") and the values are validators which recieve a string and return either True or False, depending on if it conforms to the format.

For example:

```python
def check_contains_spam(item: str) -> bool:
    return "spam" in item

spammy_validator = Validator(
    {"type": "string", "format": "spam"},
    formats={"spam": check_contians_spam},
)

print(spammy_validator.is_valid("spam spam spam spam"))  # True
print(spammy_validator.is_valid("eggs"))  # False
```

or, disabling the format checks completely:

```python
>>> from jsonscreamer import Validator
>>> val = Validator({"type": "string", "format": "date-time"}, formats=False)
>>> val.is_valid("not a date")
True

```

### Custom ref handlers

The `Validator` class takes a `handlers` parameter which can be used to specify how to handle `$ref` URIs.
By default we will attempt to download any schema with a URI starting with `http` or `https` - to everride this behaviour you must provide a dictionary where the keys are the URI scheme and the values are functions which take a URI and provide a json schema.

To forbid remote refs you can write something like the following:

```python
def raising_handler(uri: str) -> None:
    raise ValueError(f"cannot resolve remote ref: {uri}")

local_validator = Validator(
    ..., handlers={"http": raising_handler, "https": raising_handler},
)
```

or if you have already downloaded all of the remote schemas you could just add a local lookup function of your choosing.


## Test suite compliance

For the Draft 7 schema test suite, we pass **210** out of **212** tests. We consider the two failures to be very niche cases to do with relative `$ref` resolution in the "definitions" section. We are currently more compliant than fastjsonschema, and for almost all real-world schemas this should be considered complete.


## Roadmap

**Resolver:** currently we are using a subclass of fastjsonschema's resolver for ref resolution. We've added a few compatibility hacks to pass more of the json schema test site. We'd like to move to something more robust.

**2019 Draft:** the 2019 draft is on our roadmap once ref resolution is sorted.

**2020 Draft:** the 2020 draft is on our roadmap after the 2019 draft is sorted.

**Earlier Drafts:** we might consider this if there is demand.
