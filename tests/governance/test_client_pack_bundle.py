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

from src.governance.client._pack_sources import handover_edge
from src.governance.client.pack import build_client_pack, pack_manifest
from src.governance.client._pack_events import event_rows

SETTINGS = {"fields": {"org_name": "MKM"}}

# The MRC Terms of Reference is held on the committee (reference collection ``mrc``),
# not in settings. One committee whose ToR file is the fixture's seeded tor.docx.
_MRC_WITH_TOR = [{"item_id": "MRC-001", "name": "Division MRC",
                  "tor_filename": "tor.docx", "tor_original_name": "MRC ToR.docx"}]


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
    # The ToR is held per MRC committee (reference collection ``mrc``); default to one
    # committee whose ToR file is the seeded tor.docx. Tests override via _stub_tor.
    _stub_tor(monkeypatch, _MRC_WITH_TOR)
    return tmp_path


def _stub_tor(monkeypatch, committees):
    """Stub the MRC committee list the pack reads its Terms of Reference from."""
    monkeypatch.setattr("src.governance.client._pack_sources.get_reference_lists",
                        lambda config=None: {"mrc": list(committees)})


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
    monkeypatch.setattr("src.governance.client._pack_sources.list_meetings", lambda config=None: [])


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
    monkeypatch.setattr("src.governance.client._pack_sources.get_product",
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
    monkeypatch.setattr("src.governance.client._pack_sources.get_product",
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
    monkeypatch.setattr("src.governance.client._pack_sources.list_meetings",
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
    _stub_tor(monkeypatch, [])  # no committee has a ToR
    monkeypatch.setattr("src.governance.client.pack.list_products", lambda config=None: [])
    monkeypatch.setattr("src.governance.client._pack_sources.list_meetings",
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
    _stub_tor(monkeypatch, [{"item_id": "MRC-1", "name": "Division MRC",
                             "tor_filename": "absent.docx", "tor_original_name": "ToR.docx"}])
    contents = _open(build_client_pack(
        _client([]), SETTINGS, "2026-07-27", "2026-07-27T09:30:00")).read(
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
    monkeypatch.setattr("src.governance.client._pack_sources.list_meetings",
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
    _stub_tor(monkeypatch, [])  # no committee has a ToR
    m = pack_manifest(_client([{"link_type": "Model", "subject_id": "MKM-NONE"}]),
                      {"fields": {}})
    assert m["models"][0]["present"] is False
    assert any("not in the inventory" in w for w in m["warnings"])
    assert any("No MRC Terms of Reference" in w for w in m["warnings"])


def test_manifest_flags_every_missing_file(stub, monkeypatch):
    # Model present but one attachment absent; a supplementary doc absent; a
    # meeting whose minutes file is absent; a ToR recorded but absent.
    _model(monkeypatch)  # default docs: tests.pdf (present) + gone.pdf (absent)
    _stub_tor(monkeypatch, [{"item_id": "MRC-1", "name": "Division MRC",
                             "tor_filename": "no.docx", "tor_original_name": "ToR.docx"}])
    monkeypatch.setattr("src.governance.client.pack.list_products", lambda config=None: [])
    monkeypatch.setattr("src.governance.client._pack_sources.list_meetings",
                        lambda config=None: [{"meeting_id": "MRC-9", "data": {
                            "status": "Completed", "date": "2026-06-01",
                            "minutes_filename": "nomin.pdf"}}])
    client = _client_with_supplementary(
        [{"link_type": "Model", "subject_id": "MKM-EF-001"}],
        [{"item_id": "DOC-001", "filename": "absent.pdf", "original_name": "absent.pdf"}])
    m = pack_manifest(client, {"fields": {}})
    assert m["models"][0]["present"] is True and "gone.pdf" in m["models"][0]["attachments"]
    assert m["supplementary"][0]["present"] is False
    assert m["minutes"][0]["present"] is False
    assert m["tor"]["present"] is False
    joined = " ".join(m["warnings"])
    assert "gone.pdf" in joined and "absent.pdf" in joined
    assert "MRC-9" in joined and "Terms of Reference for Division MRC is recorded" in joined


def test_event_rows_sorted_newest_first_across_products():
    products = [
        {"product_id": "P1", "data": {"operational_failure_events": [
            {"date": "2026-01-01", "description": "old"}]}},
        {"product_id": "P2", "data": {"operational_failure_events": [
            {"date": "2026-09-09", "description": "new"}]}},
    ]
    rows = event_rows(products)
    assert rows[0][0] == "P2" and rows[1][0] == "P1"


# --- Handovers are re-rendered, never packed as they were filed ----------------

_HANDOVER = "handover_MKM-EF-001_to_MKM-GH-001.pdf"


def _handover_doc():
    return [{"category": "Core Documentation", "filename": "handover.pdf",
             "original_name": _HANDOVER}]


def _stub_handoff(monkeypatch, exists=True):
    monkeypatch.setattr("src.governance.client._pack_sources.get_handoff_for_edge",
                        lambda a, b, config=None: {"handoff_id": f"{a}->{b}"}
                        if exists else None)
    monkeypatch.setattr("src.governance.client.pack.get_handoff_for_edge",
                        lambda a, b, config=None: {"handoff_id": f"{a}->{b}"}
                        if exists else None)
    monkeypatch.setattr("src.governance.client._pack_sources.render_handover_pdf",
                        lambda handoff, provider, consumer, as_of: b"%PDF-fresh-handover")


@pytest.mark.parametrize("name,edge", [
    ("handover_MKM-EF-001_to_MKM-GH-001.pdf", ("MKM-EF-001", "MKM-GH-001")),
    ("handover__to_MKM-GH-001.pdf", None),      # no provider
    ("handover_MKM-EF-001_to_.pdf", None),      # no consumer
    ("handover_MKM-EF-001.pdf", None),          # no separator at all
    ("sensitivity.pdf", None),                  # not a handover
])
def test_a_handover_filename_names_the_edge_it_documents(name, edge):
    """``_to_`` is the separator because model ids carry no underscores — so the
    two ends are recoverable from the name a previous pack wrote."""
    assert handover_edge(name) == edge


def test_a_handover_is_recompiled_from_its_handoff_record(stub, monkeypatch):
    """The pack carries the current template and lineage, not whatever was
    uploaded as evidence months ago — a stale handover misdescribes the interface
    it is the evidence for."""
    _model(monkeypatch, docs=_handover_doc())
    _no_meetings_or_products(monkeypatch)
    _stub_handoff(monkeypatch)
    archive = _open(build_client_pack(
        _client([{"link_type": "Model", "subject_id": "MKM-EF-001"}]),
        SETTINGS, "2026-07-27", "2026-07-27T09:30:00"))
    packed = f"models/MKM-EF-001/Core Documentation/{_HANDOVER}"
    assert archive.read(packed) == b"%PDF-fresh-handover"


def test_a_handover_whose_edge_no_longer_exists_falls_back_to_the_filed_copy(
        stub, monkeypatch):
    """Nothing to regenerate from, so the recorded file is the only evidence there
    is — and it is reported missing rather than quietly dropped."""
    _model(monkeypatch, docs=_handover_doc())
    _no_meetings_or_products(monkeypatch)
    _stub_handoff(monkeypatch, exists=False)
    contents = _open(build_client_pack(
        _client([{"link_type": "Model", "subject_id": "MKM-EF-001"}]),
        SETTINGS, "2026-07-27", "2026-07-27T09:30:00")).read("CONTENTS.txt").decode()
    assert _HANDOVER in contents
    assert "not available at the time of packing" in contents


def test_the_manifest_does_not_warn_about_a_handover_it_can_regenerate(
        stub, monkeypatch):
    """The preview has to agree with the pack. Warning about a missing evidence
    file the pack will simply recompile sends somebody hunting for a file that
    does not need to exist."""
    _model(monkeypatch, docs=_handover_doc())
    _no_meetings_or_products(monkeypatch)
    _stub_handoff(monkeypatch)
    manifest = pack_manifest(
        _client([{"link_type": "Model", "subject_id": "MKM-EF-001"}]), SETTINGS)
    assert not [w for w in manifest["warnings"] if _HANDOVER in w]


# --- Several committees, several Terms of Reference ---------------------------

def test_each_committees_terms_of_reference_are_labelled_when_there_are_several(
        stub, monkeypatch):
    """Two committees whose ToR files are both called "ToR.docx" would collide in
    one folder, and the reader could not tell whose was whose."""
    (stub / "mrc" / "tor2.docx").write_bytes(b"TOR-TWO")
    _model(monkeypatch)
    _no_meetings_or_products(monkeypatch)
    _stub_tor(monkeypatch, [
        {"item_id": "MRC-001", "name": "Division MRC", "tor_filename": "tor.docx",
         "tor_original_name": "ToR.docx"},
        {"item_id": "MRC-002", "name": "Group MRC", "tor_filename": "tor2.docx",
         "tor_original_name": "ToR.docx"}])
    names = _open(build_client_pack(
        _client([]), SETTINGS, "2026-07-27", "2026-07-27T09:30:00")).namelist()
    assert "governance/Division MRC --- ToR.docx" in names
    assert "governance/Group MRC --- ToR.docx" in names
