from typing import Any as _Any

from .compile import compile_ as _compile, register as _register
from ._types import _Schema, _Validator


@_register
def object_(defn: _Schema) -> _Validator:
    assert defn["type"] == "object"

    conditions = [lambda x: isinstance(x, dict)]

    if "properties" in defn:
        properties = defn["properties"]
        validators = {key: _compile(val) for key, val in properties.items()}

        if "additionalProperties" in defn:
            aps = defn["additionalProperties"]
            if isinstance(aps, dict):
                default = _compile(aps)

                conditions.append(lambda x: all(
                    validators.get(k, default)(v) for k, v in x.items()
                ))
            elif aps is False:
                conditions.append(lambda x: all(
                    k in validators and validators[k](v) for k, v in x.items()
                ))

            else:
                conditions.append(lambda x: all(
                    validators[k](v) for k, v in x.items() if k in validators
                ))

    else:
        if "additionalProperties" in defn:
            aps = defn["additionalProperties"]
            if aps is False:
                conditions.append(lambda x: len(x) == 0)

            elif isinstance(aps, dict):
                validator = _compile(aps)
                conditions.append(
                    lambda x: all(validator(v) for v in x.values())
                )

    if "required" in defn:
        required = defn["required"]
        conditions.append(lambda x: all(r in x for r in required))

    if "minProperties" in defn:
        minlen = defn["minProperties"]
        conditions.append(lambda x: len(x) >= minlen)

    if "maxProperties" in defn:
        maxlen = defn["maxProperties"]
        conditions.append(lambda x: len(x) <= maxlen)

    if "dependencies" in defn:
        dependencies = defn["dependencies"]

        for key, deps in dependencies.items():
            if isinstance(deps, list):
                conditions.append(
                    lambda x, key=key, deps=deps:
                    key not in x or all(d in x for d in deps)
                )
            else:
                condition = _compile(deps)
                conditions.append(
                    lambda x, condition=condition: key not in x or condition(x)
                )

    # TODO: pattern properties
    def validate(x: _Any) -> bool:
        return all(c(x) for c in conditions)

    return validate
