# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Product MRC sign-off: request → route via the product's Division/Department → approve."""
from __future__ import annotations

from tests.web.conftest import HEADERS


def _seed_mrc(client, value="MRC-CO", level="Company", scope_value=None):
    fields = {"value": value, "name": value, "level": level}
    if scope_value:
        fields["scope_value"] = scope_value
    return client.post("/api/reference/collections/mrc",
                       json={"fields": fields, "confirmed": True}, headers=HEADERS)


def _model(client, model_id="M1", **fields):
    return client.post("/api/models",
                       json={"model_id": model_id, "name": "Analytics", "fields": fields,
                             "confirmed": True}, headers=HEADERS)


def _product(client, product_id="P1", analytics_model="M1", rag="Amber", **org):
    client.post("/api/products",
                json={"product_id": product_id, "product": "Bond",
                      "fields": {"analytics_model": analytics_model,
                                 "market_data_model": "m", "calculating_agent": "c"},
                      "confirmed": True}, headers=HEADERS)
    # Org fields (division/department) are set via the detail field editor.
    for field, value in org.items():
        client.post(f"/api/products/{product_id}/field",
                    json={"field": field, "value": value, "confirmed": True}, headers=HEADERS)
    if rag:
        client.post(f"/api/products/{product_id}/field",
                    json={"field": "rag_rating", "value": rag, "confirmed": True}, headers=HEADERS)


def _schedule(client, meeting_id="MTG1", mrc="MRC-CO", date="2026-09-15"):
    return client.post("/api/meetings",
                       json={"meeting_id": meeting_id, "title": "Q3", "date": date,
                             "fields": {"mrc": mrc}, "confirmed": True}, headers=HEADERS)


def _request(client, product_id="P1"):
    return client.post(f"/api/products/{product_id}/request-signoff",
                       json={"confirmed": True}, headers=HEADERS)


def _signoff_items(client, meeting_id="MTG1"):
    """Sign-off items on a meeting's agenda (every meeting also seeds the five
    standing items, so a sign-off is never alone or necessarily first)."""
    agenda = client.get(f"/api/meetings/{meeting_id}").get_json()["data"]["agenda"]
    return [a for a in agenda if a.get("subject_product_id") or a.get("subject_model_id")]


def test_request_attaches_to_scheduled_meeting(client):
    _seed_mrc(client)
    _model(client)
    _product(client)
    _schedule(client)
    resp = _request(client)
    assert resp.status_code == 201
    items = _signoff_items(client)
    assert len(items) == 1
    assert items[0]["subject_product_id"] == "P1"
    assert items[0]["proposed_rag"] == "Amber"
    req = resp.get_json()["data"]["rag_signoff_requests"][0]
    assert req["status"] == "Attached" and req["meeting_id"] == "MTG1"


def test_request_without_meeting_queues_pending(client):
    _seed_mrc(client)
    _model(client)
    _product(client)
    resp = _request(client)
    assert resp.status_code == 201
    req = resp.get_json()["data"]["rag_signoff_requests"][0]
    assert req["status"] == "Pending" and req["target_mrc"] == "MRC-CO"


def test_pending_request_drains_onto_new_meeting(client):
    _seed_mrc(client)
    _model(client)
    _product(client)
    _request(client)
    _schedule(client)
    items = _signoff_items(client)
    assert len(items) == 1 and items[0]["subject_product_id"] == "P1"


def test_request_blocked_without_mrc(client):
    _model(client)
    _product(client, division="Nowhere")   # a product org that no committee covers
    resp = _request(client)
    assert resp.status_code == 400
    assert "MRC" in resp.get_json()["error"]


def test_routing_uses_product_org_not_model(client):
    # A Division-level committee for Markets. The product sits in Markets; its
    # analytics model has no org — routing must follow the product, not the model.
    _seed_mrc(client, value="MRC-MKTS", level="Division", scope_value="Markets")
    _model(client)
    _product(client, division="Markets")
    mrc = client.get("/api/products/P1/mrc").get_json()
    assert mrc["mrc"]["value"] == "MRC-MKTS" and mrc["level"] == "Division"
    resp = _request(client)
    assert resp.status_code == 201
    assert resp.get_json()["data"]["rag_signoff_requests"][0]["target_mrc"] == "MRC-MKTS"


def test_request_blocked_without_rag_rating(client):
    _seed_mrc(client)
    _model(client)
    _product(client, rag=None)
    resp = _request(client)
    assert resp.status_code == 400
    assert "RAG" in resp.get_json()["error"]


def test_approve_stamps_signoff_date_meeting_and_history(client):
    _seed_mrc(client)
    _model(client)
    _product(client, rag="Green")
    _schedule(client)
    _request(client)
    agenda_id = _signoff_items(client)[0]["item_id"]
    resp = client.post(f"/api/meetings/MTG1/agenda/{agenda_id}/approve-signoff",
                       json={"confirmed": True, "reason": "committee satisfied"}, headers=HEADERS)
    assert resp.status_code == 200
    product = resp.get_json()["product"]["data"]
    assert product["rag_rating"] == "Green"
    assert product["mrc_signoff_date"] == "2026-09-15"
    assert product["mrc_signoff_meeting"] == "MTG1"
    assert product["rag_signoff_history"][0]["to_rating"] == "Green"
    assert product["rag_signoff_requests"][0]["status"] == "Completed"
    signoff = next(a for a in resp.get_json()["meeting"]["data"]["agenda"]
                   if a.get("subject_product_id"))
    assert signoff["status"] == "Completed"


def test_product_mrc_endpoint_surfaces_pending(client):
    _seed_mrc(client)
    _model(client)
    _product(client)
    _schedule(client)
    _request(client)
    mrc = client.get("/api/products/P1/mrc").get_json()
    assert mrc["mrc"]["value"] == "MRC-CO"
    assert mrc["pending_signoff"]["status"] == "Attached"
    assert mrc["pending_signoff"]["meeting_id"] == "MTG1"
