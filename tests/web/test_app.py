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
"""Tests for the Flask app factory and the index view."""
from __future__ import annotations

from config.web import WEB_HOST, WEB_PORT
from src.web import create_app


def test_web_config_has_sensible_defaults():
    assert isinstance(WEB_PORT, int)
    assert WEB_HOST


def test_index_serves_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"MKM" in response.data
    assert b"Model Risk Governance" in response.data


def test_index_actor_field_prefills_from_sso_header(client):
    # The "Acting as" field defaults to the resolved principal.
    html = client.get("/", headers={"X-Auth-Request-User": "alice@bank.com"}).get_data(as_text=True)
    assert 'id="actor-input" value="alice@bank.com"' in html


def test_index_actor_field_falls_back_when_no_header(client):
    # With no SSO header, it falls back to the configured dev identity.
    html = client.get("/").get_data(as_text=True)
    assert 'id="actor-input" value="dev@localhost"' in html


def test_create_app_runs_migrations_by_default():
    # Default path applies migrations (idempotent); the app builds successfully.
    app = create_app()
    assert app.test_client().get("/").status_code == 200
