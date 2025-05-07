import re as _re
from typing import Any as _Any
from typing import Dict as _Dict
from typing import List as _List
from typing import Optional as _Optional

from ._types import _Schema, _Validator
from .compile import compile_ as _compile
from .compile import register as _register


@_register
def max_properties(defn: _Schema) -> _Validator:
    value: int = defn["maxProperties"]
    return lambda x: len(x) <= value


@_register
def min_properties(defn: _Schema) -> _Validator:
    value: int = defn["minProperties"]
    return lambda x: len(x) >= value


@_register
def required(defn: _Schema) -> _Optional[_Validator]:
    value: _List[str] = defn["required"]
    if value:
        return lambda x: all(v in x for v in value)
    return None


@_register
def dependent_required(defn: _Schema) -> _Optional[_Validator]:
    value: _Dict[str, _List[str]] = defn["required"]
    if value:

        def validate(x):
            for dependent, required in value.items():
                if dependent in x and not all(r in x for r in required):
                    return False
            return True

        return validate

    return None


@_register
def properties(defn: _Schema) -> _Validator:
    value = defn["properties"]
    validators = {k: _compile(v) for k, v in value.items()}
    # NOTE: we expect x to be smaller than the property dict hence we iterate over x
    # we could put some advanced logic in here to iterate over the smaller of the two
    return lambda x: all(k not in validators or validators[k](v) for k, v in x.items())


@_register
def pattern_properties(defn: _Schema) -> _Validator:
    value = defn["patternProperties"]
    validators = ((_re.compile(k), _compile(v)) for k, v in value.items())

    def validate(x: _Dict[str, _Any]) -> bool:
        # ugh...
        for rex, val in validators:
            for k, v in x.items():
                if rex.match(k) and not val(v):
                    return False

        return True

    return validate


@_register
def additional_properties(defn: _Schema) -> _Validator:
    value = defn["additionalProperties"]
    simple_validator = _compile(value)

    excluded_names = set(defn.get("properties", ()))
    excluded_rexes = [_re.compile(k) for k in defn.get("patternProperties", ())]

    def validate(x: _Dict[str, _Any]) -> bool:
        for k, v in x.items():
            if k in excluded_names:
                continue
            if any(r.match(k) for r in excluded_rexes):
                continue
            if not simple_validator(v):
                return False

        return True

    return validate
