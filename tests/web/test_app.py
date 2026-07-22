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
    # The "Acting as" picker is a menu of People; the resolved principal is carried
    # as its default so it stays selectable when it is not one of them.
    html = client.get("/", headers={"X-Auth-Request-User": "alice@bank.com"}).get_data(as_text=True)
    assert 'id="actor-input" data-default="alice@bank.com"' in html


def test_index_actor_field_falls_back_when_no_header(client):
    # With no SSO header, it falls back to the configured dev identity.
    html = client.get("/").get_data(as_text=True)
    assert 'id="actor-input" data-default="david.kelly@mkmresearchlabs.com"' in html


def test_create_app_runs_migrations_by_default():
    # Default path applies migrations (idempotent); the app builds successfully.
    app = create_app()
    assert app.test_client().get("/").status_code == 200
