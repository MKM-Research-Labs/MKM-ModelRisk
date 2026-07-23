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
"""Fixtures for the web-layer tests."""
from __future__ import annotations

import pytest

from src.governance.reference import ensure_default_model_types
from src.web import create_app

HEADERS = {"X-Auth-Request-User": "alice@corp"}


@pytest.fixture
def client():
    # Migrations are applied once by the root session fixture.
    app = create_app(run_db_migrations=False)
    app.testing = True
    return app.test_client()


@pytest.fixture
def seeded_model_types():
    """Seed the model-type list, as a real app does when it starts.

    Opt-in rather than part of ``client``: seeding writes events, and tests that
    assert a pristine audit trail or empty reference lists are entitled to one.
    """
    ensure_default_model_types()
