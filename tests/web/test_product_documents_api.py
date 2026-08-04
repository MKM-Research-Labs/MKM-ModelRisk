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
"""Tests for the product document / pack endpoints (generated outputs on product_bp)."""
from __future__ import annotations

import io
import zipfile

import pytest

from src.governance.mrc.pack import TectonicNotFound
from tests.web.conftest import HEADERS


def _stub_compile(monkeypatch):
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex",
                        lambda tex, assets=None: b"%PDF-stub")


def _register(client):
    """A product binding one registered model as a component."""
    client.post("/api/models", json={"model_id": "MKM-AN-001", "name": "Analytics",
                                      "confirmed": True}, headers=HEADERS)
    client.post("/api/products", json={"product_id": "PRD-1", "product": "Bond",
                                       "fields": {"calculating_agent": "Murex"},
                                       "confirmed": True}, headers=HEADERS)
    client.post("/api/products/PRD-1/collections/components",
                json={"fields": {"component_type": "Analytical Model",
                                 "model_id": "MKM-AN-001"}, "confirmed": True}, headers=HEADERS)


def test_product_document_is_generated_and_filed_under_history(client, monkeypatch):
    _stub_compile(monkeypatch)
    _register(client)
    assert client.get("/api/products/PRD-1/document.pdf").status_code == 200
    client.get("/api/products/PRD-1/document.pdf")            # a second issue
    docs = client.get("/api/products/PRD-1").get_json()["data"]["documents"]
    history = [d for d in docs if d.get("category") == "History"]
    assert len(history) == 2, "each issue is filed under History, not overwritten"
    assert all(d["original_name"].startswith("PRD-1_product_document_") for d in history)
    assert len({d["original_name"] for d in history}) == 2, "timestamps distinguish them"


def test_product_pack_zips_the_document_and_component_model_pack(client, monkeypatch):
    _stub_compile(monkeypatch)
    _register(client)
    resp = client.get("/api/products/PRD-1/pack.zip")
    assert resp.status_code == 200
    assert resp.headers["Content-Disposition"] == 'attachment; filename="PRD-1_product_pack.zip"'
    names = zipfile.ZipFile(io.BytesIO(resp.data)).namelist()
    assert "PRD-1_product_document.pdf" in names
    assert "models/MKM-AN-001/MKM-AN-001_model_risk_document.pdf" in names


def test_pack_manifest_previews_without_compiling(client):
    _register(client)
    m = client.get("/api/products/PRD-1/pack-manifest").get_json()
    assert m["models"][0]["model_id"] == "MKM-AN-001"
    assert m["includes_product_document"] is True


@pytest.mark.parametrize("path", ["/document.pdf", "/pack.zip", "/pack-manifest"])
def test_unknown_product_is_404(client, path):
    assert client.get("/api/products/NONE" + path).status_code == 404


@pytest.mark.parametrize("path", ["/document.pdf", "/pack.zip"])
def test_missing_tectonic_is_a_clean_503(client, monkeypatch, path):
    _register(client)

    def _boom(tex, assets=None):
        raise TectonicNotFound("tectonic is not installed")
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex", _boom)
    resp = client.get("/api/products/PRD-1" + path)
    assert resp.status_code == 503
    assert "tectonic" in resp.get_json()["error"]
