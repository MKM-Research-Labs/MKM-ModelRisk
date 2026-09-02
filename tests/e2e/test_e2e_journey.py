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
"""Browser-level onboarding journey — the UI twin of tests/journey.

Drives a real browser through the whole governance chain against a dedicated,
non-MKM database. Run it with::

    E2E_DB_NAME=mkm_modelrisk_journey pytest tests/e2e -m journey

The pure-prerequisite records with no browser flow of their own (a person, the
committee, the company) are seeded through the app's own API, exactly as the
other e2e tests do; the core workflow — registering the models, building the
product, scheduling the meeting, proposing a rating and the committee ratifying
it — goes through the actual UI. Everything is synthetic (Acme / Wile E. Coyote)
and never touches MKM data.

Marked ``journey`` (not ``e2e``), so ``pytest tests/e2e -m e2e`` leaves it alone
and it only ever runs against its dedicated database.
"""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from tests.e2e._flows import confirm, open_app, open_committee, open_tab

pytestmark = pytest.mark.journey

# Wile E. Coyote runs the models at Acme: the actor on every event and the owner
# of the model are one and the same.
ACTOR = "coyote@acme.com"
HEADERS = {"X-Auth-Request-User": ACTOR, "Content-Type": "application/json"}


def _api(page: Page, base_url: str, path: str, body: dict):
    resp = page.request.post(base_url + path, data=body, headers=HEADERS)
    assert resp.ok, f"POST {path} -> {resp.status}: {resp.text()}"
    return resp


def _register_model(page: Page, model_id: str, name: str, model_type: str) -> None:
    page.click("#m-register")
    page.fill("#reg-model_id", model_id)
    page.fill("#reg-name", name)
    page.select_option("#reg-type", model_type)
    page.select_option("#reg-owner", ACTOR)     # owner is mandatory at registration
    page.click("#reg-submit")
    confirm(page)                               # register_model is gated
    expect(page.locator(f"tr.clickable[data-id='{model_id}']")).to_be_visible()


def _register_product(page: Page, product_id: str, name: str, agent: str) -> None:
    # The register modal takes the product, its id and the calculating agent;
    # model components are bound afterwards (see the API call in the test).
    open_tab(page, "product")
    page.click("#product-register")
    page.fill("#preg-product_id", product_id)
    page.fill("#preg-product", name)
    page.fill("#preg-calculating_agent", agent)  # free text — the agent list is unseeded
    page.click("#product-reg-submit")
    confirm(page)                               # register_product is gated
    expect(page.locator(f"tr.clickable[data-id='{product_id}']")).to_be_visible()


def _schedule_meeting(page: Page, meeting_id: str, title: str, date: str) -> None:
    # The schedule form lives on the committee, so it is bound to whichever one
    # was opened; scheduling is ungated (no confirm modal).
    open_committee(page, "MRC-CO")
    page.fill("#sc-meeting_id", meeting_id)
    page.fill("#sc-title", title)
    page.fill("#sc-date", date)
    page.click("#mt-schedule")
    expect(page.locator(f"tr.clickable[data-id='{meeting_id}']")).to_be_visible()


def _propose_rag(page: Page, model_id: str, rag: str) -> None:
    # Choosing a RAG on the overview is not a plain edit — it raises an MRC
    # sign-off proposal (ungated) and routes to the scheduled meeting.
    open_tab(page, "inventory")
    page.click(f"tr.clickable[data-id='{model_id}']")
    expect(page.locator("#m-detail .dtabs")).to_be_visible()
    page.click("[data-edit='rag_rating']")
    page.select_option("#ed-input", rag)
    page.click("#ed-save")
    expect(page.locator("[data-dtab='risk'].active")).to_be_visible()


def _approve_signoff(page: Page, meeting_id: str) -> None:
    open_committee(page, "MRC-CO")
    page.click(f"tr.clickable[data-id='{meeting_id}']")
    page.click("[data-mtab='models_in_scope']")
    approve = page.locator("[data-agapprove]").first
    expect(approve).to_be_visible()
    approve.click()
    confirm(page)                               # ratifying is gated


def test_browser_onboarding_journey(page: Page, base_url: str):
    # 1. Prerequisites with no browser flow of their own — seeded via the API,
    #    the same way the rest of the e2e suite seeds people and committees.
    #    Model types are seeded explicitly rather than relied upon: the harness
    #    truncates the event log before each test, which clears the defaults the
    #    app seeds at startup (they are event-sourced reference data).
    _api(page, base_url, "/api/reference/collections/model_type",
         {"fields": {"value": "Analytical Model", "binding_role": "Analytics"},
          "confirmed": True})
    _api(page, base_url, "/api/reference/collections/people",
         {"fields": {"name": ACTOR, "email": ACTOR}, "confirmed": True})
    _api(page, base_url, "/api/reference/collections/mrc",
         {"fields": {"value": "MRC-CO", "name": "Model Risk Committee", "level": "Company",
                     "quorum_require_chair": "No", "quorum_require_secretary": "No",
                     "quorum_min_voting": "0"}, "confirmed": True})
    _api(page, base_url, "/api/clients",
         {"name": "Acme Corporation", "fields": {}, "confirmed": True})

    open_app(page, base_url)
    page.evaluate("typeof MrcNav !== 'undefined' && MrcNav.invalidate()")

    # 2. A model owned by coyote@acme.com.
    _register_model(page, "ACME-PRICER-1", "Acme Rocket Pricer", "Analytical Model")

    # 3. A product priced on QuantLib, then that model bound as its component.
    #    Registration is through the UI; the component (added after registration
    #    in this app) is bound via the API.
    _register_product(page, "ACME-PRS-1", "Acme Pricing and Risk Service", "QuantLib")
    resp = page.request.post(
        base_url + "/api/products/ACME-PRS-1/collections/components",
        data={"fields": {"component_type": "Analytical Model",
                         "model_id": "ACME-PRICER-1", "role": "Pricing engine"},
              "confirmed": True}, headers=HEADERS)
    assert resp.ok, f"bind component -> {resp.status}: {resp.text()}"

    # 4. Schedule the committee meeting, propose a Green rating (routes to it),
    #    and have the committee ratify it.
    _schedule_meeting(page, "ACME-MTG-1", "Q3 Model Risk Committee", "2026-09-15")
    _propose_rag(page, "ACME-PRICER-1", "Green")
    _approve_signoff(page, "ACME-MTG-1")

    # 5. Governance state, asserted against the API to avoid UI re-render races.
    model = page.request.get(base_url + "/api/models/ACME-PRICER-1").json()["data"]
    assert model["rag_rating"] == "Green"
    assert model["mrc_signoff_meeting"] == "ACME-MTG-1"

    clients = page.request.get(base_url + "/api/clients").json()
    assert any(c["data"]["name"] == "Acme Corporation" for c in clients)

    product = page.request.get(base_url + "/api/products/ACME-PRS-1").json()["data"]
    assert any(c["model_id"] == "ACME-PRICER-1" for c in product["components"])
