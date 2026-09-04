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
"""Tests for the MRC settings + logo HTTP API."""
from __future__ import annotations

import base64
import io

from config.reporting import DEFAULT_CLASSIFICATION, DEFAULT_LEGAL_NOTICE
from src.files import upload_path
from tests.web.conftest import HEADERS

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGPw9fUFAAHSAOhesXztAAAAAElFTkSuQmCC"
)


def test_get_settings_has_defaults_and_specs(client):
    settings = client.get("/api/mrc/settings").get_json()
    assert settings["fields"]["frequency"] == "Quarterly"
    assert settings["logo"] is None
    assert any(spec["key"] == "chair" for spec in settings["specs"])


def test_report_wording_is_served_to_the_misc_tab(client):
    """Admin > Misc edits the document wording that used to live in config code, so
    the API has to say which settings belong to it and what they currently say."""
    settings = client.get("/api/mrc/settings").get_json()
    misc = {spec["key"] for spec in settings["specs"] if spec["group"] == "misc"}
    assert {"report_classification", "report_author", "report_legal_notice"} <= misc
    assert settings["fields"]["report_classification"] == DEFAULT_CLASSIFICATION
    # Both ship empty for the adopter to fill in, so the tab has to serve the keys
    # even when there is nothing yet to show against them.
    assert settings["fields"]["report_legal_notice"] == "".join(DEFAULT_LEGAL_NOTICE)


def test_update_report_legal_notice(client):
    response = client.post(
        "/api/mrc/settings/field",
        json={"field": "report_legal_notice", "value": "Property of Sterling Bank plc.",
              "confirmed": True},
        headers=HEADERS,
    )
    assert response.get_json()["fields"]["report_legal_notice"] == "Property of Sterling Bank plc."


def test_update_setting_field(client):
    response = client.post(
        "/api/mrc/settings/field",
        json={"field": "chair", "value": "Johnny Mattimore", "confirmed": True}, headers=HEADERS,
    )
    assert response.get_json()["fields"]["chair"] == "Johnny Mattimore"


def test_update_unknown_setting_is_400(client):
    response = client.post(
        "/api/mrc/settings/field",
        json={"field": "bogus", "value": "x", "confirmed": True}, headers=HEADERS,
    )
    assert response.status_code == 400


def test_logo_upload_then_serve(client):
    upload = client.post(
        "/api/mrc/settings/logo",
        data={"file": (io.BytesIO(PNG), "logo.png")},
        content_type="multipart/form-data", headers=HEADERS,
    )
    assert upload.status_code == 201
    assert upload.get_json()["logo"]["filename"] == "logo.png"

    served = client.get("/api/mrc/logo")
    assert served.status_code == 200
    assert served.data[:4] == b"\x89PNG"


def test_logo_missing_file_is_400(client):
    response = client.post(
        "/api/mrc/settings/logo", data={}, content_type="multipart/form-data", headers=HEADERS,
    )
    assert response.status_code == 400


def test_logo_bad_extension_is_400(client):
    response = client.post(
        "/api/mrc/settings/logo",
        data={"file": (io.BytesIO(b"x"), "evil.exe")},
        content_type="multipart/form-data", headers=HEADERS,
    )
    assert response.status_code == 400


def test_logo_not_set_is_404(client):
    assert client.get("/api/mrc/logo").status_code == 404


def test_tor_upload_then_download(client):
    upload = client.post(
        "/api/mrc/settings/tor",
        data={"file": (io.BytesIO(b"%PDF-fake"), "mrc-tor.pdf")},
        content_type="multipart/form-data", headers=HEADERS,
    )
    assert upload.status_code == 201
    assert upload.get_json()["tor"]["original_name"] == "mrc-tor.pdf"

    served = client.get("/api/mrc/tor")
    assert served.status_code == 200
    assert served.headers["Content-Disposition"].endswith('filename=mrc-tor.pdf')
    assert served.data == b"%PDF-fake"


def test_tor_missing_file_is_400(client):
    response = client.post(
        "/api/mrc/settings/tor", data={}, content_type="multipart/form-data", headers=HEADERS,
    )
    assert response.status_code == 400


def test_tor_not_set_is_404(client):
    assert client.get("/api/mrc/tor").status_code == 404


def test_tor_bad_extension_is_400(client):
    response = client.post(
        "/api/mrc/settings/tor",
        data={"file": (io.BytesIO(b"x"), "evil.exe")},
        content_type="multipart/form-data", headers=HEADERS,
    )
    assert response.status_code == 400


def test_a_tor_whose_file_has_gone_missing_is_404_not_a_500(client):
    """The settings still record the ToR; the file underneath is gone. That is a
    404 about the file rather than a stack trace about the store."""
    client.post("/api/mrc/settings/tor",
                data={"file": (io.BytesIO(b"%PDF-fake"), "mrc-tor.pdf")},
                content_type="multipart/form-data", headers=HEADERS)
    filename = client.get("/api/mrc/settings").get_json()["tor"]["filename"]
    upload_path("mrc", filename).unlink()
    assert client.get("/api/mrc/tor").status_code == 404
