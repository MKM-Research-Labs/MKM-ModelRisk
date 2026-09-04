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
from src.files import upload_path
from src.governance.completeness.scan import finos_evidence
from src.governance.documents import (GOVERNANCE_ARTEFACTS_AGGREGATE,
                                      find_document)
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


# --- Retrieval and removal ----------------------------------------------------

def _company_shelf(client):
    return client.get("/api/artefacts").get_json()["shelves"][0]


def test_an_artefact_can_be_retrieved_and_taken_off_the_shelf(client):
    shelf = _company_shelf(client)
    item_id = _upload(client, shelf).get_json()[0]["item_id"]

    download = client.get(f"/api/artefacts/{shelf}/{item_id}/download")
    assert download.status_code == 200 and download.data == b"PDFDATA"
    assert "attachment" in download.headers["Content-Disposition"]
    inline = client.get(f"/api/artefacts/{shelf}/{item_id}/download?inline=1")
    assert "inline" in inline.headers["Content-Disposition"]

    removed = client.post(f"/api/artefacts/{shelf}/{item_id}/delete", headers=HEADERS)
    assert removed.status_code == 200 and removed.get_json() == []


def test_an_artefact_nobody_filed_can_be_neither_downloaded_nor_removed(client):
    shelf = _company_shelf(client)
    assert client.get(f"/api/artefacts/{shelf}/DOC-999/download").status_code == 404
    assert client.post(f"/api/artefacts/{shelf}/DOC-999/delete",
                       headers=HEADERS).status_code == 404


def test_an_artefact_whose_file_has_gone_missing_is_404_not_a_500(client):
    shelf = _company_shelf(client)
    item_id = _upload(client, shelf).get_json()[0]["item_id"]
    upload_path(f"artefact/{shelf}", find_document(
        GOVERNANCE_ARTEFACTS_AGGREGATE, shelf, item_id)["filename"]).unlink()
    assert client.get(f"/api/artefacts/{shelf}/{item_id}/download").status_code == 404


# --- What the shelf will not accept -------------------------------------------

def test_an_upload_with_no_file_is_400(client):
    response = client.post("/api/artefacts/" + _company_shelf(client),
                           data={"kind": "Policy"},
                           content_type="multipart/form-data", headers=HEADERS)
    assert response.status_code == 400


def test_a_kind_outside_the_vocabulary_is_refused_and_the_options_listed(client):
    """The kind is what the tiles are read by, so an invented one would file the
    document somewhere nobody looks."""
    response = client.post(
        "/api/artefacts/" + _company_shelf(client),
        data={"file": (io.BytesIO(b"PDFDATA"), "x.pdf"), "kind": "Nonsense"},
        content_type="multipart/form-data", headers=HEADERS)
    assert response.status_code == 400
    assert "kind must be one of" in response.get_json()["error"]


def test_an_extension_the_platform_will_not_store_is_400(client):
    assert _upload(client, _company_shelf(client), filename="evil.exe").status_code == 400
