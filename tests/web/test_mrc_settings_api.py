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
"""Tests for the MRC settings + logo HTTP API."""
from __future__ import annotations

import base64
import io

from tests.web.conftest import HEADERS

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGPw9fUFAAHSAOhesXztAAAAAElFTkSuQmCC"
)


def test_get_settings_has_defaults_and_specs(client):
    settings = client.get("/api/mrc/settings").get_json()
    assert settings["fields"]["frequency"] == "Quarterly"
    assert settings["logo"] is None
    assert any(spec["key"] == "chair" for spec in settings["specs"])


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
