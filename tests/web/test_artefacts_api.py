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
"""Tests for the Artefacts panel of the Documents tab, and the FINOS shelf.

The FINOS shelf is the one artefact shelf the completeness audit reads. A document
filed there names the mitigations it describes, and those tags are what turn a row
of the coverage table from Not evidenced into a citation — so the round trip that
matters is not "the file came back", it is "the tag survived and the audit can see
it".
"""
from __future__ import annotations

import io

from config.governance import FINOS_SHELF
from src.governance.completeness.scan import finos_evidence
from tests.web.conftest import HEADERS


def _upload(client, shelf, filename="controls.pdf", description="", refs=()):
    data = {"file": (io.BytesIO(b"PDFDATA"), filename), "description": description,
            "kind": "Policy"}
    if refs:
        data["finos_refs"] = list(refs)
    return client.post("/api/artefacts/" + shelf, data=data,
                       content_type="multipart/form-data", headers=HEADERS)


def test_the_finos_shelf_is_offered_with_its_mitigation_catalogue(client):
    body = client.get("/api/artefacts").get_json()
    assert FINOS_SHELF in body["shelves"]
    assert body["finos_shelf"] == FINOS_SHELF
    refs = body["finos_refs"]
    # The whole mitigation catalogue, served so the picker has one source of truth.
    assert len(refs) == 23
    assert all(r["ref"].startswith("AIR-") and r["title"] for r in refs)
    assert "AIR-PREV-005" in {r["ref"] for r in refs}


def test_a_tagged_document_is_readable_by_the_audit(client):
    """The round trip that matters: what the audit reads is what was filed."""
    assert finos_evidence() == []
    assert _upload(client, FINOS_SHELF, description="Our AI control standard",
                   refs=["AIR-PREV-017", "AIR-DET-001"]).status_code == 201

    filed = finos_evidence()
    assert len(filed) == 1
    assert filed[0]["finos_refs"] == ["AIR-PREV-017", "AIR-DET-001"]
    assert filed[0]["description"] == "Our AI control standard"


def test_references_are_ignored_on_a_shelf_that_is_not_finos(client):
    """A stray tag elsewhere is inert rather than an error: refusing the upload
    over one would lose the document to save the tag."""
    body = client.get("/api/artefacts").get_json()
    company_wide = body["shelves"][0]
    assert company_wide != FINOS_SHELF
    assert _upload(client, company_wide, refs=["AIR-PREV-017"]).status_code == 201

    artefacts = client.get("/api/artefacts").get_json()["artefacts"][company_wide]
    assert artefacts[0]["finos_refs"] == []
    assert finos_evidence() == []


def test_an_untagged_finos_document_is_filed_but_evidences_nothing(client):
    """Filing is not evidencing. A paper nobody tagged is on the shelf and counts
    for nothing, which the panel says on the tile and the audit says in the row."""
    assert _upload(client, FINOS_SHELF, description="Draft, untagged").status_code == 201
    filed = finos_evidence()
    assert len(filed) == 1 and filed[0]["finos_refs"] == []


def test_an_unknown_shelf_is_refused(client):
    assert _upload(client, "Nonexistent").status_code == 404
