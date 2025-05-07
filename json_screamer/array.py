from typing import Any as _Any

from ._types import _Schema, _Validator
from .compile import compile_ as _compile, register as _register

# TODO:
# 1. staffing spreadsheet
# 2. https://json-schema.org/draft/2020-12/json-schema-validation.html#rfc.section.6.1.1


@_register
def array(defn: _Schema) -> _Validator:
    assert defn["type"] == "array"
    conditions = [lambda x: isinstance(x, list)]

    if "minItems" in defn:
        minlen = defn["minItems"]
        conditions.append(lambda x: len(x) >= minlen)

    if "maxItems" in defn:
        maxlen = defn["maxItems"]
        conditions.append(lambda x: len(x) >= maxlen)

    if defn.get("uniqueItems", False):
        conditions.append(lambda x: len(x) == len(set(x)))

    if "items" in defn:
        items = defn["items"]

        if isinstance(items, dict):
            validator = _compile(items)
            conditions.append(lambda x: all(validator(i) for i in x))

        else:
            validators = [_compile(i) for i in items]
            conditions.append(
                lambda x: all(v(i) for v, i in zip(validators, x))
            )
            if "additionalItems" in defn:
                validator = _compile(defn["additionalItems"])
                cutoff = len(validators)
                conditions.append(
                    lambda x: all(validator(i) for i in x[cutoff:])
                )

    def validate(x: _Any) -> bool:
        return all(c(x) for c in conditions)

    return validate
