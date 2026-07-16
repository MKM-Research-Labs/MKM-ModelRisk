# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Tests for the ModelRisk ingest client."""
from __future__ import annotations

import io
import urllib.error
import urllib.request

import pytest

from modelrisk_scan import IngestClient, IngestError
from modelrisk_scan.client import _http_post, _safe_json

PROV = {"source_repo": "PhysicalRisk", "commit": "abc", "producer": "modelrisk-scan",
        "producer_version": "0.1.0", "generated_at": "2026-07-15T00:00:00Z"}
MANIFEST = {"runs": {"r1": ["s1"]}, "steps": {"s1": {"type": "file"}}}


class _Recorder:
    """A transport that records the call and returns a canned response."""

    def __init__(self, status, body):
        self.status, self.body = status, body
        self.calls = []

    def __call__(self, url, json_body, headers):
        self.calls.append((url, json_body, headers))
        return self.status, self.body


def test_push_created_builds_envelope_and_url():
    transport = _Recorder(201, {"artifact": "data-lineage"})
    client = IngestClient("https://mr.internal/", "tok", transport=transport)
    result = client.push("data-lineage", MANIFEST, PROV)
    assert result.created is True
    url, body, headers = transport.calls[0]
    assert url == "https://mr.internal/api/ingest/data-lineage"  # trailing slash stripped
    assert body == {"schema_version": "v1", "artifact": "data-lineage",
                    "provenance": PROV, "payload": MANIFEST}
    assert headers["X-Ingest-Token"] == "tok"


def test_push_idempotent_is_not_created():
    client = IngestClient("https://mr.internal", "tok", transport=_Recorder(200, {}))
    assert client.push("data-lineage", MANIFEST, PROV).created is False


def test_push_error_raises_with_status_and_body():
    client = IngestClient("https://mr.internal", "tok",
                          transport=_Recorder(422, {"error": "bad", "details": ["x"]}))
    with pytest.raises(IngestError) as exc:
        client.push("data-lineage", MANIFEST, PROV)
    assert exc.value.status == 422
    assert exc.value.body["details"] == ["x"]


def test_custom_token_header():
    transport = _Recorder(201, {})
    client = IngestClient("https://mr.internal", "tok",
                          token_header="Authorization", transport=transport)
    client.push("data-lineage", MANIFEST, PROV)
    assert transport.calls[0][2]["Authorization"] == "tok"


def test_safe_json_parses_valid_and_wraps_invalid():
    assert _safe_json(b'{"a": 1}') == {"a": 1}
    assert _safe_json(b"not json") == {"raw": "not json"}


def test_http_post_success(monkeypatch):
    class _Resp:
        status = 201
        def read(self): return b'{"ok": true}'
        def __enter__(self): return self
        def __exit__(self, *a): return False
    monkeypatch.setattr(urllib.request, "urlopen", lambda req: _Resp())
    status, body = _http_post("https://mr/api/ingest/data-lineage", {"a": 1}, {"H": "v"})
    assert status == 201 and body == {"ok": True}


def test_http_post_http_error(monkeypatch):
    def _raise(req):
        raise urllib.error.HTTPError("u", 422, "unprocessable", {}, io.BytesIO(b'{"error": "x"}'))
    monkeypatch.setattr(urllib.request, "urlopen", _raise)
    status, body = _http_post("https://mr/api/ingest/data-lineage", {"a": 1}, {})
    assert status == 422 and body == {"error": "x"}
