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
"""An AI System's place in the rest of the estate: the committee, its evidence
pack, and a Product that binds it.

These are the three things that make a record type real rather than a register of
its own. A record the committee never sees, that carries no evidence and that
nothing can be built from is a list, not governance.
"""
from __future__ import annotations

import io

from config.governance import COMPONENT_KIND_AI, VALID_COMPONENT_KINDS
from src.governance.ai_system import get_ai_system
from tests.web.conftest import HEADERS

_MINIMUM = {"name": "Client mail summariser", "division": "Risk",
            "owner": "David K Kelly",
            "use_case": "Summarises inbound client correspondence.",
            "deployment_pattern": "Agentic (tool-using)"}


def _register(client, ai_system_id="AIS-0001", **overrides):
    return client.post("/api/ai-systems", json={
        "ai_system_id": ai_system_id, "fields": {**_MINIMUM, **overrides},
        "actor": "admin"}, headers=HEADERS)


# --- The committee ----------------------------------------------------------

def test_the_signoff_subject_is_registered():
    """The routing is a registry of adapters; a record type absent from it cannot be
    put in front of a committee at all."""
    from src.web._signoff_subject import SUBJECTS
    kinds = {s.kind for s in SUBJECTS}
    assert "ai_system" in kinds
    subject = next(s for s in SUBJECTS if s.kind == "ai_system")
    assert subject.agenda_id_field == "subject_ai_system_id"
    assert subject.id_key == "ai_system_id"


def test_the_agenda_can_carry_an_ai_system_as_its_subject():
    """An agenda item names its subject through a per-kind field. Without one the
    committee's decision has nothing to apply to."""
    from config.governance import MRC_COLLECTION_SPECS
    agenda = MRC_COLLECTION_SPECS["agenda"]
    keys = {f["key"] for f in agenda["fields"]}
    assert "subject_ai_system_id" in keys


def test_a_rating_cannot_be_proposed_without_one(client):
    _register(client)
    res = client.post("/api/ai-systems/AIS-0001/request-signoff",
                      json={"actor": "admin"}, headers=HEADERS)
    assert res.status_code == 400
    assert "proposed_rag is required" in res.get_json()["error"]


def test_signoff_is_refused_when_no_committee_covers_the_division(client):
    """Better to refuse than to raise a request nothing will ever pick up."""
    _register(client, division="Nowhere")
    res = client.post("/api/ai-systems/AIS-0001/request-signoff",
                      json={"proposed_rag": "Amber", "actor": "admin"}, headers=HEADERS)
    assert res.status_code == 400
    assert "no MRC committee covers" in res.get_json()["error"]


# --- The evidence pack ------------------------------------------------------

def test_a_document_round_trips_against_the_record(client):
    _register(client)
    res = client.post("/api/ai-systems/AIS-0001/documents", data={
        "file": (io.BytesIO(b"PDFDATA"), "red-team-report.pdf"),
        "category": "Analysis", "description": "Red-team findings, July"},
        content_type="multipart/form-data", headers=HEADERS)
    assert res.status_code == 201
    docs = res.get_json()["data"]["documents"]
    assert len(docs) == 1 and docs[0]["original_name"] == "red-team-report.pdf"

    item_id = docs[0]["item_id"]
    assert client.get(f"/api/ai-systems/AIS-0001/documents/{item_id}/download").status_code == 200
    assert client.post(f"/api/ai-systems/AIS-0001/documents/{item_id}/delete",
                       json={"actor": "admin"}, headers=HEADERS).status_code == 200
    assert get_ai_system("AIS-0001")["data"].get("documents", []) == []


def test_an_uncategorised_document_is_refused(client):
    _register(client)
    res = client.post("/api/ai-systems/AIS-0001/documents", data={
        "file": (io.BytesIO(b"X"), "x.pdf"), "category": "Not a category"},
        content_type="multipart/form-data", headers=HEADERS)
    assert res.status_code == 400


# --- A Product that binds one -----------------------------------------------

def test_a_product_can_bind_an_ai_system_as_a_component(client):
    """The point of the record type for a bank: a Product that draws on models,
    ML Applications and an AI System is one product, governed as one thing."""
    assert COMPONENT_KIND_AI in VALID_COMPONENT_KINDS
    _register(client)
    client.post("/api/products", json={
        "product_id": "PRD-0001", "product": "Client service desk",
        "fields": {"calculating_agent": "Murex"},
        "confirmed": True}, headers=HEADERS)
    res = client.post("/api/products/PRD-0001/collections/components", json={
        "fields": {"kind": COMPONENT_KIND_AI, "model_id": "AIS-0001",
                   "role": "Drafts the first reply"},
        "confirmed": True}, headers=HEADERS)
    assert res.status_code in (200, 201), res.get_json()
    comps = client.get("/api/products/PRD-0001").get_json()["data"]["components"]
    assert comps[0]["kind"] == COMPONENT_KIND_AI
    assert comps[0]["model_id"] == "AIS-0001"


def test_an_ai_component_needs_no_model_type(client):
    """A model component names its type from the admin list. An AI System has no
    entry there, so requiring one would force whoever binds it to pick a lie."""
    _register(client)
    client.post("/api/products", json={
        "product_id": "PRD-0002", "product": "Desk",
        "fields": {"calculating_agent": "Murex"},
        "confirmed": True}, headers=HEADERS)
    res = client.post("/api/products/PRD-0002/collections/components", json={
        "fields": {"kind": COMPONENT_KIND_AI, "model_id": "AIS-0001"},
        "confirmed": True}, headers=HEADERS)
    assert res.status_code in (200, 201)


def test_the_product_report_resolves_it_against_the_right_register():
    """Looking an AI System up in the model inventory would report a bound component
    as missing — a finding, rather than a component of another kind."""
    from src.governance.product._report_product import _RESOLVERS
    from config.governance import COMPONENT_KIND_ML
    assert set(_RESOLVERS) == {COMPONENT_KIND_ML, COMPONENT_KIND_AI, None}
    assert "AI System register" in _RESOLVERS[COMPONENT_KIND_AI][1]
