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
"""Fixtures for the onboarding-journey suite.

The journey runs against a dedicated database, completely separate from the
dev/demo ``mkm_modelrisk`` estate. The database name comes from the environment
at invocation — run the suite with::

    TEST_DB_BASE=mkm_modelrisk_journey pytest tests/journey -m journey

The root ``tests/conftest.py`` then creates ``mkm_modelrisk_journey_<worker>``,
migrates it, truncates it between tests and drops it at the end — the same
guard-railed machinery every suite uses (it refuses to touch ``mkm_modelrisk``).
Nothing here seeds MKM data; the journey builds its own synthetic world (Acme /
Wile E. Coyote) from an empty schema.
"""
from __future__ import annotations

import pytest

from src.web import create_app

# Wile E. Coyote runs the models at Acme. The journey signs in as him, so the
# actor stamped on every event and the model's owner are the same person.
ACTOR = "coyote@acme.com"
HEADERS = {"X-Auth-Request-User": ACTOR}


@pytest.fixture
def client():
    # Migrations are applied once by the root session fixture against the
    # dedicated journey database, so the app must not re-run them here.
    app = create_app(run_db_migrations=False)
    app.testing = True
    return app.test_client()
