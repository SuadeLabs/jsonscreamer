"""Resolve $ref fields in schemas to actual values.

We do this when we parse the schema and cache the results.
This code is

"""

from __future__ import annotations

import contextlib as _contextlib
import json as _json
import urllib.parse as _urlparse
import urllib.request as _request
from typing import TYPE_CHECKING as _TYPE_CHECKING

from fastjsonschema.ref_resolver import (
    RefResolver as _FastRefResolver,
    get_id,
    normalize,
    resolve_path,
    resolve_remote,
)

if _TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from .types import Json, Schema, Validator


class RefTracker:
    """Tracks which identifiers have validations defined.

    This is required solely to allow existence of defered references.
    For example `{"properties": {"foo": "$ref": "#"}}` is infinitely
    recursive.
    """

    def __init__(
        self, schema: Schema | bool, handlers: dict[str, Callable[[str], Json]]
    ) -> None:
        # Trackers for various states of compilation
        self._queued: list[str] = []
        self._picked: set[str] = set()
        self.compiled: dict[str, Validator] = {}

        self._resolver = RefResolver.from_schema(schema, store={}, handlers=handlers)

        # Kick off the compilation with top-level function
        self._queued.append(self._resolver.get_uri())
        self._entrypoint_uri = self._queued[0]

    def __bool__(self) -> bool:
        return bool(self._queued)

    def queue(self, uri: str) -> None:
        self._queued.append(uri)

    def pop(self) -> str:
        uri = self._queued.pop()
        self._picked.add(uri)
        return uri

    def seen(self, uri: str) -> bool:
        return uri in self._picked

    @property
    def entrypoint(self) -> Validator:
        return self.compiled[self._entrypoint_uri]


def request_handler(uri: str) -> Json:
    request = _request.Request(uri, headers={"User-Agent": "jsonscreamer"})  # noqa: S310
    with _request.urlopen(request) as resp:  # noqa: S310
        return _json.load(resp)


HANDLERS = {"http": request_handler, "https": request_handler}


class RefResolver(_FastRefResolver):
    """
    Resolve JSON References.

    This is a partial rewrite of fastjsonschema's implementation,
    with some compatibility hacks. See:
        https://github.com/horejsek/python-fastjsonschema
    """

    _TRAVERSE_ARBITRARY_KEYS = frozenset(("definitions", "properties"))

    def __init__(
        self,
        base_uri: str,
        schema: Schema | bool,
        store: object = ...,
        cache: bool = True,
        handlers: object = ...,
    ) -> None:
        # XXX: import here must be deferred to prevent cyclic imports
        from .compile import _COMPILATION_FUNCTIONS

        self._TRAVERSABLE_KEYS = (
            frozenset(_COMPILATION_FUNCTIONS)
            .union(("definitions",))
            .difference(("const", "enum"))
        )

        super().__init__(base_uri, schema, store, cache, handlers)

    @_contextlib.contextmanager
    def resolving(self, ref: str) -> Iterator[Schema | bool]:
        """
        Context manager which resolves a JSON ``ref`` and enters the
        resolution scope of this ref.
        """
        absolute = bool(_urlparse.urlsplit(ref).netloc)

        new_uri = ref if absolute else _urlparse.urljoin(self.resolution_scope, ref)
        uri, fragment = _urlparse.urldefrag(new_uri)

        # TODO: edge case - fragments in ids - remove for later schemas
        if new_uri and new_uri in self.store:
            schema: Schema = self.store[new_uri]
            fragment = ""
        elif uri and normalize(uri) in self.store:
            schema = self.store[normalize(uri)]
        elif not uri or uri == self.base_uri:
            schema = self.schema
        else:
            schema = resolve_remote(uri, self.handlers)
            if self.cache:
                self.store[normalize(uri)] = schema

        old_base_uri, old_schema = self.base_uri, self.schema
        self.base_uri, self.schema = uri, schema
        try:
            with self.in_scope(uri):
                yield resolve_path(schema, fragment)
        finally:
            self.base_uri, self.schema = old_base_uri, old_schema

    def walk(self, node: dict, arbitrary_keys: bool = False) -> None:
        """
        Walk thru schema and dereferencing ``id`` and ``$ref`` instances
        """
        if isinstance(node, bool):
            pass
        elif "$ref" in node and isinstance(node["$ref"], str):
            ref = node["$ref"]
            node["$ref"] = _urlparse.urljoin(self.resolution_scope, ref)
        elif ("$id" in node or "id" in node) and isinstance(get_id(node), str):
            with self.in_scope(get_id(node)):
                self.store[normalize(self.resolution_scope)] = node
                # TODO: edge case - fragments in ids - remove for later schemas
                self.store[self.resolution_scope] = node
                for key, item in node.items():
                    if isinstance(item, dict) and (
                        arbitrary_keys or key in self._TRAVERSABLE_KEYS
                    ):
                        self.walk(
                            item, arbitrary_keys=key in self._TRAVERSE_ARBITRARY_KEYS
                        )
        else:
            for key, item in node.items():
                if isinstance(item, dict) and (
                    arbitrary_keys or key in self._TRAVERSABLE_KEYS
                ):
                    self.walk(item, arbitrary_keys=key in self._TRAVERSE_ARBITRARY_KEYS)
