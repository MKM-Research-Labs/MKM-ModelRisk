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
"""End-to-end onboarding journey on a pristine, non-MKM database.

One ordered narrative — reference data, a committee, the company, a model owned
by ``coyote@acme.com``, a product built on that model, then an MRC meeting that
ratifies the model's rating — asserting after each step. The state is built up
across the whole test, so it is a single function: the root ``_clean_event_log``
fixture truncates between tests, which would otherwise unwind the chain.

Everything here is synthetic (Acme / Wile E. Coyote) and never touches MKM data.
"""
from __future__ import annotations

import pytest

from tests.journey import _flows as flow
from tests.journey.conftest import ACTOR

pytestmark = pytest.mark.journey

OWNER = ACTOR  # coyote@acme.com owns the model


def test_onboarding_journey_from_empty_to_ratified_model(client):
    # 1. Reference data the later steps depend on: the pricing platform, a model
    #    type (the inventory's Type is a closed vocabulary), and a person to own
    #    the model. A fresh journey database starts with none of these.
    assert flow.add_calculating_agent(client, "QuantLib").status_code == 201
    assert flow.add_model_type(client, "Analytical Model", "Analytics").status_code == 201
    assert flow.add_person(client, OWNER, email=OWNER).status_code == 201

    refs = flow.reference_lists(client)
    assert any(p["name"] == OWNER for p in refs["people"])
    assert any(c["value"] == "QuantLib" for c in refs["calculating_agent"])

    # 2. The Company-level MRC — the responsible committee for every model, and a
    #    precondition for any sign-off (matching_mrc must resolve a committee).
    assert flow.add_mrc(client).status_code == 201

    # 3. The company (the Client aggregate).
    resp = flow.register_client(client, "Acme Corporation", sector="Cartoon Logistics")
    assert resp.status_code == 201
    client_id = resp.get_json()["client_id"]
    assert client_id.startswith("CL-")

    # 4. A model, owned by coyote@acme.com and rated Amber pending review.
    assert flow.register_model(
        client, "ACME-PRICER-1", "Acme Rocket Pricer",
        type="Analytical Model", owner=OWNER, rag_rating="Amber").status_code == 201
    model = flow.get_model(client, "ACME-PRICER-1")
    assert model["data"]["owner"] == OWNER
    assert model["data"]["rag_rating"] == "Amber"

    # 5. A product priced on QuantLib, built from that model as a component.
    assert flow.register_product(
        client, "ACME-PRS-1", "Acme Pricing & Risk Service",
        calculating_agent="QuantLib").status_code == 201
    assert flow.add_component(
        client, "ACME-PRS-1", "Analytical Model", "ACME-PRICER-1",
        role="Pricing engine").status_code == 201
    product = flow.get_product(client, "ACME-PRS-1")
    assert any(c["model_id"] == "ACME-PRICER-1" for c in product["data"]["components"])

    # 6. Schedule the committee meeting the sign-off will be heard at.
    assert flow.schedule_meeting(
        client, "ACME-MTG-1", "Q3 Model Risk Committee",
        "2026-09-15", "MRC-CO").status_code == 201

    # 7. The owner requests sign-off of a Green rating; it lands on the meeting's
    #    agenda as a decision item.
    assert flow.request_signoff(client, "ACME-PRICER-1", "Green").status_code in (200, 201)

    # 8. The committee ratifies it (the meeting is quorate → approved). The
    #    rating is snapped to Green and stamped with the granting meeting.
    item = flow.signoff_agenda_item(client, "ACME-MTG-1", "ACME-PRICER-1")
    assert flow.approve_signoff(client, "ACME-MTG-1", item["item_id"]).status_code == 200

    ratified = flow.get_model(client, "ACME-PRICER-1")["data"]
    assert ratified["rag_rating"] == "Green"
    assert ratified["mrc_signoff_meeting"] == "ACME-MTG-1"
