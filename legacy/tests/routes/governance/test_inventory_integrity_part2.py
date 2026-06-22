# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Structural integrity tests for the real model_inventory.json — part 2.

Covers: TestRequiredListFields, TestRequiredStringFields, TestAPIEndpointAvailability.
"""

import json
import pathlib

import pytest


INVENTORY_PATH = (
    pathlib.Path(__file__).parents[3]
    / "docs" / "models" / "governance_data" / "model_inventory.json"
)

REQUIRED_LIST_FIELDS = ["upstream_models", "downstream_models", "limitations", "assumptions"]


@pytest.fixture(scope="module")
def inventory():
    assert INVENTORY_PATH.exists(), (
        f"model_inventory.json not found at {INVENTORY_PATH}. "
        "Run: python app.py port to generate it."
    )
    with open(INVENTORY_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def models(inventory):
    return inventory.get("models", [])


class TestRequiredListFields:
    """upstream_models, downstream_models, limitations, assumptions must be lists."""

    @pytest.mark.parametrize("field", REQUIRED_LIST_FIELDS)
    def test_field_is_list(self, models, field):
        for m in models:
            mid = m.get("model_id", "?")
            assert field in m, f"{mid}: missing field '{field}'"
            assert isinstance(m[field], list), (
                f"{mid}: '{field}' must be a list, got {type(m[field]).__name__!r}"
            )


class TestRequiredStringFields:
    """Core identity fields must be non-empty strings."""

    REQUIRED_STRINGS = ["name", "description", "category", "status", "version", "owner"]

    @pytest.mark.parametrize("field", REQUIRED_STRINGS)
    def test_field_is_string(self, models, field):
        for m in models:
            mid = m.get("model_id", "?")
            assert field in m, f"{mid}: missing field '{field}'"
            assert isinstance(m[field], str), (
                f"{mid}: '{field}' must be a string, got {type(m[field]).__name__!r}"
            )
            assert m[field].strip(), f"{mid}: '{field}' is blank"


class TestAPIEndpointAvailability:
    """Verify the governance models endpoint returns 200 against the real inventory."""

    def test_models_endpoint_returns_200(self, gov_client, governance_env):
        """Existing synthetic fixture -- confirms endpoint logic works."""
        response = gov_client.get("/api/v1/governance/models")
        assert response.status_code == 200

    def test_real_inventory_endpoint_succeeds(self, monkeypatch):
        """
        Mounts the real model_inventory.json and confirms the endpoint does not 500.

        This is the regression test for the MKM-SS-001 malformed fields bug.
        """
        import copy
        import pathlib

        import routes.governance._constants as gov_constants

        real_inventory = json.loads(INVENTORY_PATH.read_text())

        import tempfile, os
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(real_inventory, f)
            inv_tmp = f.name
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([], f)
            audit_tmp = f.name

        monkeypatch.setattr(gov_constants, "INVENTORY_PATH", inv_tmp)
        monkeypatch.setattr(gov_constants, "AUDIT_LOG_PATH", audit_tmp)

        from config import config
        monkeypatch.setattr(config, "get_input_dir",
                            lambda: pathlib.Path(inv_tmp).parent)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        response = client.get("/api/v1/governance/models")
        data = json.loads(response.data)

        os.unlink(inv_tmp)
        os.unlink(audit_tmp)

        assert response.status_code == 200, (
            f"GET /api/v1/governance/models returned {response.status_code}. "
            f"Response: {data}. "
            "Check that all models in governance_data/model_inventory.json have test_coverage "
            "and overall_risk_rating as dicts (not strings)."
        )
        assert data["status"] == "success"
        assert len(data["models"]) == len(real_inventory["models"])

    def test_real_inventory_model_count_matches_file(self, monkeypatch):
        """All models in the file are served by the endpoint."""
        import tempfile, os

        import routes.governance._constants as gov_constants

        real_inventory = json.loads(INVENTORY_PATH.read_text())
        expected_count = len(real_inventory["models"])

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(real_inventory, f)
            inv_tmp = f.name
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([], f)
            audit_tmp = f.name

        monkeypatch.setattr(gov_constants, "INVENTORY_PATH", inv_tmp)
        monkeypatch.setattr(gov_constants, "AUDIT_LOG_PATH", audit_tmp)

        from config import config
        monkeypatch.setattr(config, "get_input_dir",
                            lambda: pathlib.Path(inv_tmp).parent)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        response = client.get("/api/v1/governance/models")
        data = json.loads(response.data)

        os.unlink(inv_tmp)
        os.unlink(audit_tmp)

        assert response.status_code == 200
        assert len(data["models"]) == expected_count, (
            f"Expected {expected_count} models, got {len(data['models'])}"
        )

