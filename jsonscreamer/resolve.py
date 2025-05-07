"""Resolve $ref fields in schemas to actual values.

We do this when we parse the schema and cache the results.
"""

from fastjsonschema.ref_resolver import normalize, urlparse, unquote, contextlib, get_id, resolve_path, resolve_remote, re


class RefTracker:
    """Tracks which identifiers have validations defined.

    This is required solely to allow existence of defered references.
    For example `{"properties": {"foo": "$ref": "#"}}` is infinitely
    recursive.
    """

    def __init__(self, schema, resolver=None):
        # Trackers for various states of compilation
        self.queued = []
        self._picked = set()
        self._compiled = {}

        self._resolver = resolver or RefResolver.from_schema(schema, store={}, handlers=HANDLERS)

        # Kick off the compilation with top-level function
        self.queued.append((self._resolver.get_uri(), self._resolver.get_scope_name()))
        self._entrypoint_uri = self._resolver.get_uri()

    @property
    def entrypoint(self):
        return self._compiled[self._entrypoint_uri]


def request_handler(uri):
    import requests

    resp = requests.get(uri)
    resp.raise_for_status()
    return resp.json()


HANDLERS = {"http": request_handler, "https": request_handler}



# The following is lifted from fastjsonschema, with some compatibility hacks:
class RefResolver:
    """
    Resolve JSON References.
    """

    # pylint: disable=dangerous-default-value,too-many-arguments
    def __init__(self, base_uri, schema, store={}, cache=True, handlers={}):
        """
        `base_uri` is URI of the referring document from the `schema`.
        `store` is an dictionary that will be used to cache the fetched schemas
        (if `cache=True`).

        Please notice that you can have caching problems when compiling schemas
        with colliding `$ref`. To force overwriting use `cache=False` or
        explicitly pass the `store` argument (with a brand new dictionary)
        """
        self.base_uri = base_uri
        self.resolution_scope = base_uri
        self.schema = schema
        self.store = store
        self.cache = cache
        self.handlers = handlers
        self.walk(schema)

    @classmethod
    def from_schema(cls, schema, handlers={}, **kwargs):
        """
        Construct a resolver from a JSON schema object.
        """
        return cls(
            get_id(schema) if isinstance(schema, dict) else '',
            schema,
            handlers=handlers,
            **kwargs
        )

    @contextlib.contextmanager
    def in_scope(self, scope: str):
        """
        Context manager to handle current scope.
        """
        old_scope = self.resolution_scope
        self.resolution_scope = urlparse.urljoin(old_scope, scope)
        try:
            yield
        finally:
            self.resolution_scope = old_scope

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

    def get_uri(self):
        return normalize(self.resolution_scope)

    def get_scope_name(self):
        """
        Get current scope and return it as a valid function name.
        """
        name = 'validate_' + unquote(self.resolution_scope).replace('~1', '_').replace('~0', '_').replace('"', '')
        name = re.sub(r'($[^a-zA-Z]|[^a-zA-Z0-9])', '_', name)
        name = name.lower().rstrip('_')
        return name

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
                    if isinstance(item, dict) and (arbitrary_keys or key in _valid_keys()):
                        self.walk(item, arbitrary_keys=key in _ARBITRARY_KEYS)
        else:
            for key, item in node.items():
                if isinstance(item, dict) and (arbitrary_keys or key in _valid_keys()):
                    self.walk(item, arbitrary_keys=key in _ARBITRARY_KEYS)


def _valid_keys():
    from .compile import active_properties
    return active_properties().union(("definitions",)).difference(("const", "enum"))


_ARBITRARY_KEYS = frozenset(("definitions", "properties"))
