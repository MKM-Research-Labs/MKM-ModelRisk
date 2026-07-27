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
"""Tests for the client pack bundle (the ZIP compiled from a client's links)."""
from __future__ import annotations

import io
import zipfile

import pytest

from src.governance.client.pack import build_client_pack, pack_manifest
from src.governance.client._pack_events import event_rows

SETTINGS = {"fields": {"org_name": "MKM"}, "tor": {"filename": "tor.docx",
                                                   "original_name": "MRC ToR.docx"}}


@pytest.fixture
def stub(tmp_path, monkeypatch):
    """Stub the LaTeX compiler and point the upload dir at a temp tree seeded with
    a model attachment, a saved minutes PDF, and the MRC ToR file."""
    monkeypatch.setattr("src.files.store.UPLOAD_DIR", tmp_path)
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex",
                        lambda tex, assets=None: b"%PDF-stub")
    (tmp_path / "model" / "MKM-EF-001").mkdir(parents=True)
    (tmp_path / "model" / "MKM-EF-001" / "tests.pdf").write_bytes(b"%PDF-tests")
    (tmp_path / "meeting_minutes").mkdir(parents=True)
    (tmp_path / "meeting_minutes" / "minutes_MRC-1.pdf").write_bytes(b"%PDF-minutes")
    (tmp_path / "mrc").mkdir(parents=True)
    (tmp_path / "mrc" / "tor.docx").write_bytes(b"TOR-BYTES")
    return tmp_path


def _client(links):
    return {"client_id": "CL-001", "data": {"name": "Acme Bank", "links": links}}


def _model(monkeypatch, docs=None):
    monkeypatch.setattr("src.governance.client.pack.get_model",
                        lambda mid, config=None: {"model_id": mid, "data": {
                            "name": "Event Frequency",
                            "documents": docs if docs is not None else [
                                {"category": "Test Results", "filename": "tests.pdf",
                                 "original_name": "tests.pdf"},
                                {"category": "Analysis", "filename": "gone.pdf",
                                 "original_name": "gone.pdf"},
                            ]}} if mid == "MKM-EF-001" else None)


def _no_meetings_or_products(monkeypatch):
    monkeypatch.setattr("src.governance.client.pack.list_products", lambda config=None: [])
    monkeypatch.setattr("src.governance.client.pack.list_meetings", lambda config=None: [])


def _open(data):
    return zipfile.ZipFile(io.BytesIO(data))


def test_pack_carries_linked_model_doc_and_evidence(stub, monkeypatch):
    _model(monkeypatch)
    _no_meetings_or_products(monkeypatch)
    archive = _open(build_client_pack(
        _client([{"link_type": "Model", "subject_id": "MKM-EF-001"}]),
        SETTINGS, "2026-07-27", "2026-07-27T09:30:00"))
    names = archive.namelist()
    assert "models/MKM-EF-001/MKM-EF-001_model_risk_document.pdf" in names
    assert "models/MKM-EF-001/Test Results/tests.pdf" in names
    # A recorded-but-absent attachment is named in CONTENTS, not silently dropped.
    contents = archive.read("CONTENTS.txt").decode()
    assert "models/MKM-EF-001/Analysis/gone.pdf" in contents


def test_pack_resolves_models_via_a_linked_product(stub, monkeypatch):
    _model(monkeypatch)
    monkeypatch.setattr("src.governance.client.pack.get_product",
                        lambda pid, config=None: {"product_id": pid, "data": {
                            "components": [{"model_id": "MKM-EF-001"}]}})
    _no_meetings_or_products(monkeypatch)
    archive = _open(build_client_pack(
        _client([{"link_type": "Product", "subject_id": "Product-1"}]),
        SETTINGS, "2026-07-27", "2026-07-27T09:30:00"))
    assert "models/MKM-EF-001/MKM-EF-001_model_risk_document.pdf" in archive.namelist()


def test_blank_and_unknown_link_types_are_skipped(stub, monkeypatch):
    _model(monkeypatch)
    _no_meetings_or_products(monkeypatch)
    archive = _open(build_client_pack(
        _client([{"link_type": "Model", "subject_id": ""},
                 {"link_type": "Other", "subject_id": "X"}]),
        SETTINGS, "2026-07-27", "2026-07-27T09:30:00"))
    assert not any(n.startswith("models/") for n in archive.namelist())


def test_product_component_without_a_model_id_is_ignored(stub, monkeypatch):
    _model(monkeypatch)
    monkeypatch.setattr("src.governance.client.pack.get_product",
                        lambda pid, config=None: {"product_id": pid, "data": {
                            "components": [{}, {"model_id": "MKM-EF-001"}]}})
    _no_meetings_or_products(monkeypatch)
    archive = _open(build_client_pack(
        _client([{"link_type": "Product", "subject_id": "Product-1"}]),
        SETTINGS, "2026-07-27", "2026-07-27T09:30:00"))
    assert "models/MKM-EF-001/MKM-EF-001_model_risk_document.pdf" in archive.namelist()


def test_pack_with_everything_present_lists_no_missing_section(stub, monkeypatch):
    _model(monkeypatch, docs=[{"category": "Test Results", "filename": "tests.pdf",
                               "original_name": "tests.pdf"}])
    _no_meetings_or_products(monkeypatch)
    contents = _open(build_client_pack(
        _client([{"link_type": "Model", "subject_id": "MKM-EF-001"}]),
        SETTINGS, "2026-07-27", "2026-07-27T09:30:00")).read("CONTENTS.txt").decode()
    assert "not available at the time of packing" not in contents


def test_pack_notes_a_link_to_an_unknown_model(stub, monkeypatch):
    _model(monkeypatch)
    _no_meetings_or_products(monkeypatch)
    contents = _open(build_client_pack(
        _client([{"link_type": "Model", "subject_id": "MKM-NONE"}]),
        SETTINGS, "2026-07-27", "2026-07-27T09:30:00")).read("CONTENTS.txt").decode()
    assert "models/MKM-NONE (not in the inventory)" in contents


def test_pack_includes_minutes_events_tor_and_gaps(stub, monkeypatch):
    _model(monkeypatch)
    monkeypatch.setattr("src.governance.client.pack.list_products",
                        lambda config=None: [{"product_id": "P1", "data": {
                            "operational_failure_events": [
                                {"date": "2026-05-01", "description": "Feed outage"}]}}])
    monkeypatch.setattr("src.governance.client.pack.list_meetings",
                        lambda config=None: [{"meeting_id": "MRC-1", "data": {
                            "status": "Completed", "date": "2026-06-01",
                            "minutes_filename": "minutes_MRC-1.pdf",
                            "minutes_original_name": "MRC-1 minutes.pdf"}}])
    archive = _open(build_client_pack(
        _client([{"link_type": "Model", "subject_id": "MKM-EF-001"}]),
        SETTINGS, "2026-07-27", "2026-07-27T09:30:00"))
    names = archive.namelist()
    assert "mrc/minutes/MRC-1 minutes.pdf" in names
    assert "events/event_writeups.pdf" in names
    assert "governance/MRC ToR.docx" in names
    assert archive.read("governance/MRC ToR.docx") == b"TOR-BYTES"
    assert "governance/completeness_audit.pdf" in names
    contents = archive.read("CONTENTS.txt").decode()
    assert "As of (valid time):      2026-07-27" in contents
    assert "Generated at (txn time): 2026-07-27T09:30:00" in contents


def test_pack_notes_missing_minutes_file_and_absent_tor(stub, monkeypatch):
    _model(monkeypatch)
    monkeypatch.setattr("src.governance.client.pack.list_products", lambda config=None: [])
    monkeypatch.setattr("src.governance.client.pack.list_meetings",
                        lambda config=None: [{"meeting_id": "MRC-9", "data": {
                            "status": "Completed", "date": "2026-06-01",
                            "minutes_filename": "gone.pdf"}}])
    contents = _open(build_client_pack(
        _client([]), {"fields": {}}, "2026-07-27", "2026-07-27T09:30:00")).read(
        "CONTENTS.txt").decode()
    assert "mrc/minutes/MRC-9_minutes.pdf" in contents
    assert "MRC Terms of Reference (none uploaded)" in contents


def test_pack_notes_a_recorded_tor_whose_file_is_missing(stub, monkeypatch):
    _model(monkeypatch)
    _no_meetings_or_products(monkeypatch)
    settings = {"fields": {}, "tor": {"filename": "absent.docx", "original_name": "ToR.docx"}}
    contents = _open(build_client_pack(
        _client([]), settings, "2026-07-27", "2026-07-27T09:30:00")).read(
        "CONTENTS.txt").decode()
    assert "governance/ToR.docx (recorded but file missing)" in contents


def _client_with_supplementary(links, docs):
    c = _client(links)
    c["data"]["documents"] = docs
    return c


def test_pack_carries_supplementary_documents(stub, monkeypatch):
    _model(monkeypatch)
    _no_meetings_or_products(monkeypatch)
    (stub / "client" / "CL-001").mkdir(parents=True)
    (stub / "client" / "CL-001" / "cover.pdf").write_bytes(b"%PDF-cover")
    client = _client_with_supplementary(
        [], [{"item_id": "DOC-001", "category": "Supplementary",
              "filename": "cover.pdf", "original_name": "cover.pdf"},
             {"item_id": "DOC-002", "category": "Supplementary",
              "filename": "gone.pdf", "original_name": "gone.pdf"}])
    archive = _open(build_client_pack(client, SETTINGS, "2026-07-27", "2026-07-27T09:30:00"))
    assert "supplementary/cover.pdf" in archive.namelist()
    contents = archive.read("CONTENTS.txt").decode()
    assert "supplementary/gone.pdf (recorded but file missing)" in contents


def test_manifest_previews_contents_without_compiling(stub, monkeypatch):
    _model(monkeypatch, docs=[{"category": "Test Results", "filename": "tests.pdf",
                               "original_name": "tests.pdf"}])
    monkeypatch.setattr("src.governance.client.pack.list_products", lambda config=None: [])
    monkeypatch.setattr("src.governance.client.pack.list_meetings",
                        lambda config=None: [{"meeting_id": "MRC-1", "data": {
                            "status": "Completed", "date": "2026-06-01",
                            "minutes_filename": "minutes_MRC-1.pdf"}}])  # present in the stub tree
    m = pack_manifest(_client([{"link_type": "Model", "subject_id": "MKM-EF-001"}]), SETTINGS)
    assert m["models"][0] == {"model_id": "MKM-EF-001", "name": "Event Frequency",
                              "present": True, "attachments": ["tests.pdf"]}
    assert m["minutes"][0]["present"] is True
    assert m["tor"]["present"] is True and m["includes_gaps_audit"] is True
    assert m["warnings"] == []


def test_manifest_warns_about_unknown_model_and_missing_tor(stub, monkeypatch):
    _model(monkeypatch)
    _no_meetings_or_products(monkeypatch)
    m = pack_manifest(_client([{"link_type": "Model", "subject_id": "MKM-NONE"}]),
                      {"fields": {}})
    assert m["models"][0]["present"] is False
    assert any("not in the inventory" in w for w in m["warnings"])
    assert any("No MRC Terms of Reference" in w for w in m["warnings"])


def test_manifest_flags_every_missing_file(stub, monkeypatch):
    # Model present but one attachment absent; a supplementary doc absent; a
    # meeting whose minutes file is absent; a ToR recorded but absent.
    _model(monkeypatch)  # default docs: tests.pdf (present) + gone.pdf (absent)
    monkeypatch.setattr("src.governance.client.pack.list_products", lambda config=None: [])
    monkeypatch.setattr("src.governance.client.pack.list_meetings",
                        lambda config=None: [{"meeting_id": "MRC-9", "data": {
                            "status": "Completed", "date": "2026-06-01",
                            "minutes_filename": "nomin.pdf"}}])
    client = _client_with_supplementary(
        [{"link_type": "Model", "subject_id": "MKM-EF-001"}],
        [{"item_id": "DOC-001", "filename": "absent.pdf", "original_name": "absent.pdf"}])
    m = pack_manifest(client, {"fields": {}, "tor": {"filename": "no.docx",
                                                     "original_name": "ToR.docx"}})
    assert m["models"][0]["present"] is True and "gone.pdf" in m["models"][0]["attachments"]
    assert m["supplementary"][0]["present"] is False
    assert m["minutes"][0]["present"] is False
    assert m["tor"]["present"] is False
    joined = " ".join(m["warnings"])
    assert "gone.pdf" in joined and "absent.pdf" in joined
    assert "MRC-9" in joined and "Terms of Reference is recorded" in joined


def test_event_rows_sorted_newest_first_across_products():
    products = [
        {"product_id": "P1", "data": {"operational_failure_events": [
            {"date": "2026-01-01", "description": "old"}]}},
        {"product_id": "P2", "data": {"operational_failure_events": [
            {"date": "2026-09-09", "description": "new"}]}},
    ]
    rows = event_rows(products)
    assert rows[0][0] == "P2" and rows[1][0] == "P1"
