from __future__ import annotations

import pathlib
from http.server import HTTPServer, SimpleHTTPRequestHandler
from multiprocessing import Process

import pytest

HERE = pathlib.Path(__file__).parent.resolve()
REMOTES = HERE / "suite" / "JSON-Schema-Test-Suite" / "remotes"


class _RemotesRequestHandler(SimpleHTTPRequestHandler):
    """Uses remote schemas directory as the default."""

    def __init__(self, request, client_address, server, *, directory=REMOTES):
        super().__init__(request, client_address, server, directory=directory)


def _remote_ref_server_impl():
    httpd = HTTPServer(("localhost", 1234), _RemotesRequestHandler)
    httpd.serve_forever()


@pytest.fixture(scope="session")
def _remote_ref_server():
    """Runs a server on localhost to serve "remote" schemas."""
    proc = Process(target=_remote_ref_server_impl, daemon=True)
    proc.start()
