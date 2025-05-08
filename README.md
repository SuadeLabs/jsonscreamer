# Json Screamer

Json Screamer is a fast json schema validation library built with a few goals in mind:

1. fast - up to 10x faster than the de-facto standard [jsonschema](https://github.com/python-jsonschema/jsonschema) library
2. correct - full compliance with the json schema test suite, except some gnarly `$ref` edge cases
3. easy to maintain - pure python code, regular function calls etc.

Currently it only handles the Draft 7 spec. If you want a more battle-tested and robust implementation, use [jsonschema](https://github.com/python-jsonschema/jsonschema). If you want an even faster implementation use [fastjsonschema](https://github.com/horejsek/python-fastjsonschema) (up to 2x quicker).

Given that the above libraries exist, why use jsonscreamer? Well, if the idea of dynamically creating source code and calling `exec` on it makes you (or your security team) uncomfortable that's probably the main reason not to use fastjsonschema. For that reason, jsonscreamer should also be a bit easier to reason about, improve and maintain, since it's not a python code compiler, it's just python. We also aim to be a little more correct - for instance distinguishing between 0 and False when checking unique items in arrays.

## Usage

For good performance, create a single `Validator` instance and call its methods many times:

```python
from jsonscreamer import Validator

val = Validator({"type": "string"})
print(val.is_valid(1))
print(val.is_valid("1"))

val.validate(1)  # raises a ValidationError
```

instantiating the validator is expensive, whereas calling its methods is cheap.


## Test suite compliance

For the Draft 7 schema test suite, we pass 210 out of 212 tests. We consider the two failures to be very niche cases to do with relative `$ref` resolution in the "definitions" section. We are currently more compliant than fastjsonschema, and for almost all real-world schemas this should be considered complete.

## Design

Under the hood, we follow a similar pattern to fastjsonschema in that there is a "compile" phase, where we define validators based on the schema. Naively, one might write a type validator like this:

```python
def validate_type(definition, item):
    match definition["type"]:
        case "array":
            return isinstance(item, list)
        case "object":
            return isinstance(item, dict)
        case "boolean":
            return isinstance(item, bool)
        ...
```

however, this means the majority of time validating is spent working out which validation to run on the item. Instead,
we can move the determination of exactly which validation is required to an earlier step:

```python
def create_type_validator(definition):
    match definition["type"]:
        case "array":
            return lambda item: isinstance(item, list)
        case "object":
            return lambda item: isinstance(item, dict)
        case "boolean":
            return lambda item: isinstance(item, bool)
        ...
```

so that we create the validator from the definition and later just call it on our items without reference to the original schema.


## Roadmap

**Resolver:** currently we are using a subclass of fastjsonschema's resolver for ref resolution. We've added a few compatibility hacks to pass more of the json schema test site. We'd like to move to something more robust.

**2019 Draft:** the 2019 draft is on our roadmap once ref resolution is sorted.

**2020 Draft:** the 2020 draft is on our roadmap after the 2019 draft is sorted.

**Earlier Drafts:** we might consider this if there is demand.
