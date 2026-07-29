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
"""Reusable HTTP flows for the onboarding journey — one thin helper per
governance step, each posting JSON through the real Flask routes.

Kept separate from the test module so the journey reads as a narrative, and so
the browser-level journey (step 2) can be checked against the same sequence.
Every register/retire command is confirm-to-amend; the helpers always send
``confirmed: True`` (a no-op for the non-gated commands).
"""
from __future__ import annotations

from tests.journey.conftest import HEADERS


# --- Reference data (admin-managed menu lists) -----------------------------

def add_reference(client, list_name, **fields):
    return client.post(
        f"/api/reference/collections/{list_name}",
        json={"fields": fields, "confirmed": True}, headers=HEADERS)


def add_person(client, name, **fields):
    return add_reference(client, "people", name=name, **fields)


def add_calculating_agent(client, value):
    return add_reference(client, "calculating_agent", value=value)


def add_model_type(client, value, binding_role):
    return add_reference(client, "model_type", value=value, binding_role=binding_role)


def add_mrc(client, value="MRC-CO", name="Model Risk Committee", level="Company"):
    """A Company-level committee — the responsible MRC for every model. Quorum is
    switched off so a meeting is quorate without a seated roster; the journey
    exercises the end-to-end path, not the quorum gate (covered elsewhere)."""
    return add_reference(
        client, "mrc", value=value, name=name, level=level,
        quorum_require_chair="No", quorum_require_secretary="No",
        quorum_min_voting="0")


# --- Aggregates ------------------------------------------------------------

def register_client(client, name, **fields):
    return client.post(
        "/api/clients",
        json={"name": name, "fields": fields, "confirmed": True}, headers=HEADERS)


def register_model(client, model_id, name, **fields):
    return client.post(
        "/api/models",
        json={"model_id": model_id, "name": name, "fields": fields, "confirmed": True},
        headers=HEADERS)


def register_product(client, product_id, product, **fields):
    return client.post(
        "/api/products",
        json={"product_id": product_id, "product": product, "fields": fields,
              "confirmed": True}, headers=HEADERS)


def add_component(client, product_id, component_type, model_id, role=""):
    """Bind an inventory model into a product as a component. Components are added
    after registration (a product is often registered before its models are known)."""
    return client.post(
        f"/api/products/{product_id}/collections/components",
        json={"fields": {"component_type": component_type, "model_id": model_id,
                         "role": role}, "confirmed": True}, headers=HEADERS)


def schedule_meeting(client, meeting_id, title, date, mrc):
    return client.post(
        "/api/meetings",
        json={"meeting_id": meeting_id, "title": title, "date": date,
              "fields": {"mrc": mrc}, "confirmed": True}, headers=HEADERS)


# --- MRC sign-off (ratification) -------------------------------------------

def request_signoff(client, model_id, proposed_rag):
    return client.post(
        f"/api/models/{model_id}/request-signoff",
        json={"proposed_rag": proposed_rag, "confirmed": True}, headers=HEADERS)


def signoff_agenda_item(client, meeting_id, model_id):
    """The sign-off agenda item for ``model_id`` — a scheduled meeting also seeds
    the standing agenda, so the sign-off is never the only item."""
    agenda = client.get(f"/api/meetings/{meeting_id}").get_json()["data"]["agenda"]
    return next(a for a in agenda if a.get("subject_model_id") == model_id)


def approve_signoff(client, meeting_id, agenda_id):
    return client.post(
        f"/api/meetings/{meeting_id}/agenda/{agenda_id}/approve-signoff",
        json={"confirmed": True}, headers=HEADERS)


# --- Read-backs (for assertions) -------------------------------------------

def reference_lists(client):
    return client.get("/api/reference").get_json()["data"]


def get_model(client, model_id):
    return client.get(f"/api/models/{model_id}").get_json()


def get_product(client, product_id):
    return client.get(f"/api/products/{product_id}").get_json()
