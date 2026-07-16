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
"""Negative-path / conflict coverage for the confirm-to-amend command layer.

These document the two rejection channels the write path exposes (see
``src/web/app.py`` error handlers and ``src/database/eventstore.py``):

* **409 ``ConfirmationRequired``** — an amend that arrives without ``confirmed``
  is gated, not applied. This is what the confirm-to-amend modal satisfies; it
  is *not* a concurrency signal.
* **400 ``DomainError``** — the decision functions reject an illegal transition
  (duplicate registration, editing a retired model). The browser surfaces the
  message as an error toast and leaves the confirm overlay open.

There is deliberately no test for a stale-version ``ConcurrencyError``: the
command handlers read the stream head fresh inside the same transaction as the
append (``eventstore.append_event``) and never accept a client-supplied
``expected_version``, so no UI or API path can drive two writers to the same
head deterministically.
"""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from tests.e2e._flows import open_app, register_model

pytestmark = pytest.mark.e2e

_HEADERS = {"X-Auth-Request-User": "e2e", "Content-Type": "application/json"}


def test_duplicate_registration_is_rejected(page: Page, base_url: str):
    """A second registration of the same model ID is refused: the confirm overlay
    stays open, an error toast explains why, and no duplicate row is created."""
    open_app(page, base_url)
    register_model(page, "DUP-001", "Retail Credit Scoring")

    # Attempt to register the same ID again — drive the confirm-to-amend modal by
    # hand because, unlike the happy path, the overlay does not close on rejection.
    page.click("#m-register")
    page.fill("#reg-model_id", "DUP-001")
    page.fill("#reg-name", "Second Attempt")
    page.select_option("#reg-owner", "E2E Owner")   # owner is mandatory
    page.click("#reg-submit")
    expect(page.locator("#confirm-overlay")).to_be_visible()
    page.click("#confirm-ok")

    expect(page.locator("#toast")).to_contain_text("already registered")
    expect(page.locator("#confirm-overlay")).to_be_visible()   # rejected -> stays open
    expect(page.locator("tr.clickable[data-id='DUP-001']")).to_have_count(1)


def test_amend_without_confirmation_is_gated_409(page: Page, base_url: str):
    """An amend POST with no ``confirmed`` flag is held at the confirmation gate."""
    resp = page.request.post(
        base_url + "/api/models",
        data={"model_id": "GATE-001", "name": "Unconfirmed", "fields": {}},
        headers=_HEADERS,
    )
    assert resp.status == 409, resp.text()
    body = resp.json()
    assert body.get("needs_confirmation") is True

    # And nothing was written — a follow-up confirmed register still creates it fresh.
    ok = page.request.post(
        base_url + "/api/models",
        data={"model_id": "GATE-001", "name": "Unconfirmed", "fields": {}, "confirmed": True},
        headers=_HEADERS,
    )
    assert ok.status == 201, ok.text()


def test_editing_a_retired_model_is_rejected_400(page: Page, base_url: str):
    """The retired-model guard holds at the command layer even if the UI (which
    hides the edit pencils) is bypassed with a direct API call."""
    page.request.post(
        base_url + "/api/models",
        data={"model_id": "RET-001", "name": "Retire Me", "fields": {}, "confirmed": True},
        headers=_HEADERS,
    )
    page.request.post(
        base_url + "/api/models/RET-001/retire",
        data={"confirmed": True}, headers=_HEADERS,
    )

    resp = page.request.post(
        base_url + "/api/models/RET-001/field",
        data={"field": "owner", "value": "Nobody", "confirmed": True},
        headers=_HEADERS,
    )
    assert resp.status == 400, resp.text()
    assert "retired" in resp.json()["error"].lower()
