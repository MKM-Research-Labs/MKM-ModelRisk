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
"""An unregistered identity cannot author a change over HTTP (permissions P1).

The unit tests cover the rule; these cover the wiring — that it is applied at the seam
every mutating request passes through, and that a refusal reaches the caller as a 403
rather than a 500.
"""
from __future__ import annotations

import pytest

from src.identity import _recognition

REGISTERED = {"X-Auth-Request-User": "Johnny Mattimore"}
STRANGER = {"X-Auth-Request-User": "alice@corp"}


@pytest.fixture
def hardened(client, monkeypatch):
    """Enforcement as a hardened deployment runs it, with one registered person."""
    monkeypatch.setattr(_recognition, "ENFORCE_KNOWN_ACTORS", "always")
    monkeypatch.setattr(_recognition, "registered_identities",
                        lambda: {"johnny mattimore"})
    return client


def _register(client, headers, model_id="KA1"):
    return client.post("/api/models", json={"model_id": model_id, "name": "A",
                                            "confirmed": True}, headers=headers)


def test_an_unregistered_identity_cannot_register_a_model(hardened):
    """Exactly the call that created ZZ1/ZZ2 on the live estate on 2026-08-06."""
    response = _register(hardened, STRANGER)
    assert response.status_code == 403
    body = response.get_json()
    assert body["unrecognised_actor"] is True
    assert "alice@corp" in body["error"]


def test_the_refusal_leaves_nothing_behind(hardened):
    """A refused change must not be half-applied: the gate runs before the handler."""
    _register(hardened, STRANGER, model_id="KA2")
    assert hardened.get("/api/models/KA2").status_code == 404


def test_a_registered_person_is_unaffected(hardened):
    assert _register(hardened, REGISTERED, model_id="KA3").status_code == 201


def test_uploads_are_gated_too(hardened):
    """Document uploads call their command directly rather than through dispatch, so
    they need the same gate — this is the path that would otherwise stay open."""
    _register(hardened, REGISTERED, model_id="KA4")
    response = hardened.post(
        "/api/models/KA4/documents",
        data={"file": (__import__("io").BytesIO(b"%PDF-1.4 stub"), "note.pdf"),
              "category": "Core Documentation"},
        content_type="multipart/form-data", headers=STRANGER)
    assert response.status_code == 403


def test_reads_are_not_gated(hardened):
    """The rule is about authorship. A read with an odd header still renders — blocking
    it would add risk without protecting the record."""
    _register(hardened, REGISTERED, model_id="KA5")
    assert hardened.get("/api/models/KA5", headers=STRANGER).status_code == 200
