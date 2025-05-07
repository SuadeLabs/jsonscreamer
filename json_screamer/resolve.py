"""Resolve $ref fields in schemas to actual values.

We do this when we parse the schema and cache the results.
"""
import copy as _copy
import json as _json
from typing import Any as _Any
from urllib.parse import urlsplit as _urlsplit
from urllib.request import urlopen as _urlopen

from jsonpointer import resolve_pointer as _resolve_pointer


def resolve_refs(root: _Any, defn: _Any, copied: bool = False) -> _Any:
    if not copied:
        defn = _copy.deepcopy(defn)

    if isinstance(defn, dict):
        if "$ref" in defn:
            defn.update(resolve_ref(root, defn.pop("$ref")))

        for k, v in defn.items():
            if isinstance(v, (dict, list)):
                defn[k] = resolve_refs(root, v, copied=True)

    if isinstance(defn, list):
        for k, v in enumerate(defn):
            if isinstance(v, (dict, list)):
                defn[k] = resolve_refs(root, v, copied=True)

    return defn


def resolve_ref(root: _Any, ref: str):
    parsed = _urlsplit(ref)

    if parsed.netloc:
        with _urlopen(ref) as socket:
            document = _json.loads(socket.read())
    else:
        document = root

    path = parsed.fragment
    result = _resolve_pointer(document, path)
    return resolve_refs(document, result)
