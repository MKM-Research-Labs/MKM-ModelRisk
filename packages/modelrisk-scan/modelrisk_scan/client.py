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
"""HTTP client for pushing artifacts to a ModelRisk collector.

Wraps one artifact push into the ingest envelope, POSTs it to
``/api/ingest/<artifact>`` with the shared producer token, and interprets the
response (201 stored / 200 idempotent / anything else -> ``IngestError``). The
transport is injectable so the client is testable without a live server; the
default uses the standard library only.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable

DEFAULT_TOKEN_HEADER = "X-Ingest-Token"
CONTRACT_VERSION = "v1"

# transport(url, json_body, headers) -> (status_code, parsed_response_body)
Transport = Callable[[str, dict, dict], "tuple[int, Any]"]


class IngestError(RuntimeError):
    """Raised when the collector rejects a push (non-2xx response)."""

    def __init__(self, status: int, body: Any) -> None:
        super().__init__(f"ingest failed with HTTP {status}: {body}")
        self.status = status
        self.body = body


class IngestResult:
    """The outcome of a successful push."""

    def __init__(self, *, created: bool, receipt: Any) -> None:
        self.created = created  # True on 201 (stored), False on 200 (idempotent)
        self.receipt = receipt


def _safe_json(raw: bytes) -> Any:
    try:
        return json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return {"raw": raw.decode("utf-8", "replace")}


def _http_post(url: str, body: dict, headers: dict) -> tuple[int, Any]:
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request) as response:  # noqa: S310 (trusted URL)
            return response.status, _safe_json(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, _safe_json(exc.read())


class IngestClient:
    """Pushes scan artifacts to a ModelRisk collector over HTTP."""

    def __init__(
        self, base_url: str, token: str, *,
        token_header: str = DEFAULT_TOKEN_HEADER, transport: Transport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._token_header = token_header
        self._post = transport or _http_post

    def push(self, artifact: str, payload: dict, provenance: dict) -> IngestResult:
        """Wrap ``payload`` in the ingest envelope and POST it to the collector."""
        envelope = {
            "schema_version": CONTRACT_VERSION,
            "artifact": artifact,
            "provenance": provenance,
            "payload": payload,
        }
        url = f"{self._base_url}/api/ingest/{artifact}"
        headers = {"Content-Type": "application/json", self._token_header: self._token}
        status, body = self._post(url, envelope, headers)
        if status not in (200, 201):
            raise IngestError(status, body)
        return IngestResult(created=(status == 201), receipt=body)
