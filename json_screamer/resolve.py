"""Resolve $ref fields in schemas to actual values.

We do this when we parse the schema and cache the results.
"""

import copy as _copy
from typing import Any as _Any
from urllib.parse import urlsplit as _urlsplit

from jsonpointer import resolve_pointer as _resolve_pointer
import requests


__ID_REGISTRY = {}


def register_ids(defn, within_properties=False):
    if isinstance(defn, dict):
        if "$id" in defn:
            __ID_REGISTRY[defn["$id"]] = defn

        # TODO: it seems permissible to put an id on any valid directive,
        # but we only support top-level and definition-level ids for now
        if "definitions" in defn:
            for value in defn["definitions"].values():
                register_ids(value)

    elif isinstance(defn, list):
        for item in defn:
            register_ids(item)


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

    base_uri = ""
    if parsed.netloc or parsed.path:
        prefix = f"{parsed.scheme}://" if parsed.scheme else ""
        base_uri = prefix + parsed.netloc + parsed.path

        # First check if the ref refers to a local id
        if base_uri in __ID_REGISTRY:
            document = __ID_REGISTRY[base_uri]

        elif parsed.netloc:
            resp = requests.get(ref)
            resp.raise_for_status()
            document = __ID_REGISTRY[base_uri] = resp.json()

        else:
            # warning or error?
            raise RuntimeError(f"could not resolve {ref}")

    else:
        document = root

    path = parsed.fragment
    result = _resolve_pointer(document, path)
    return resolve_refs(document, result)
