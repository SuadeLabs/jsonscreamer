"""Resolve $ref fields in schemas to actual values.

We do this when we parse the schema and cache the results.
This code is

"""
import contextlib
import urllib.parse as urlparse
from fastjsonschema.ref_resolver import RefResolver as _FastRefResolver, normalize, get_id, resolve_path, resolve_remote


class RefTracker:
    """Tracks which identifiers have validations defined.

    This is required solely to allow existence of defered references.
    For example `{"properties": {"foo": "$ref": "#"}}` is infinitely
    recursive.
    """

    def __init__(self, schema, resolver=None):
        # Trackers for various states of compilation
        self._queued = []
        self._picked = set()
        self.compiled = {}

        self._resolver = resolver or RefResolver.from_schema(schema, store={}, handlers=HANDLERS)

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
    def entrypoint(self):
        return self.compiled[self._entrypoint_uri]


def request_handler(uri):
    import requests

    resp = requests.get(uri)
    resp.raise_for_status()
    return resp.json()


HANDLERS = {"http": request_handler, "https": request_handler}


class RefResolver(_FastRefResolver):
    """
    Resolve JSON References.

    This is a partial rewrite of fastjsonschema's implementation,
    with some compatibility hacks. See:
        https://github.com/horejsek/python-fastjsonschema
    """
    _TRAVERSE_ARBITRARY_KEYS = frozenset(("definitions", "properties"))

    def __init__(self, base_uri, schema, store=..., cache=True, handlers=...):
        # XXX: import here must be deferred to prevent cyclic imports
        from .compile import _COMPILATION_FUNCTIONS
        self._TRAVERSABLE_KEYS = frozenset(_COMPILATION_FUNCTIONS).union(("definitions",)).difference(("const", "enum"))

        super().__init__(base_uri, schema, store, cache, handlers)

    @contextlib.contextmanager
    def resolving(self, ref: str):
        """
        Context manager which resolves a JSON ``ref`` and enters the
        resolution scope of this ref.
        """
        absolute = bool(urlparse.urlsplit(ref).netloc)

        new_uri = ref if absolute else urlparse.urljoin(self.resolution_scope, ref)
        uri, fragment = urlparse.urldefrag(new_uri)

        # TODO: edge case - fragments in ids - remove for later schemas
        if new_uri and new_uri in self.store:
            schema = self.store[new_uri]
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

    def walk(self, node: dict, arbitrary_keys=False):
        """
        Walk thru schema and dereferencing ``id`` and ``$ref`` instances
        """
        if isinstance(node, bool):
            pass
        elif '$ref' in node and isinstance(node['$ref'], str):
            ref = node['$ref']
            node['$ref'] = urlparse.urljoin(self.resolution_scope, ref)
        elif ('$id' in node or 'id' in node) and isinstance(get_id(node), str):
            with self.in_scope(get_id(node)):
                self.store[normalize(self.resolution_scope)] = node
                # TODO: edge case - fragments in ids - remove for later schemas
                self.store[self.resolution_scope] = node
                for key, item in node.items():
                    if isinstance(item, dict) and (arbitrary_keys or key in self._TRAVERSABLE_KEYS):
                        self.walk(item, arbitrary_keys=key in self._TRAVERSE_ARBITRARY_KEYS)
        else:
            for key, item in node.items():
                if isinstance(item, dict) and (arbitrary_keys or key in self._TRAVERSABLE_KEYS):
                    self.walk(item, arbitrary_keys=key in self._TRAVERSE_ARBITRARY_KEYS)
