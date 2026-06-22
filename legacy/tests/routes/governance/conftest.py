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

"""Shared fixtures and constants for governance route tests."""

import copy
import json
import pathlib

import pytest

from tests.routes.governance._helpers import (
    _BASE_MODEL,
    _BASE_INVENTORY,
    _BASE_RACI,
    # Re-export so existing `from tests.routes.governance.conftest import X` works
    create_meeting,
)


@pytest.fixture
def governance_env(tmp_path, monkeypatch):
    """Set up isolated governance data files for testing."""
    import routes.governance._constants as gov_constants

    inv_path = str(tmp_path / "model_inventory.json")
    audit_path = str(tmp_path / "model_audit_log.json")

    with open(inv_path, "w") as f:
        json.dump(copy.deepcopy(_BASE_INVENTORY), f)
    with open(audit_path, "w") as f:
        json.dump([], f)

    monkeypatch.setattr(gov_constants, "INVENTORY_PATH", inv_path)
    monkeypatch.setattr(gov_constants, "AUDIT_LOG_PATH", audit_path)

    return {"inv_path": inv_path, "audit_path": audit_path}


@pytest.fixture
def gov_client(governance_env, monkeypatch):
    """Flask test client with isolated governance data."""
    from config import config
    monkeypatch.setattr(config, "get_input_dir",
                        lambda: pathlib.Path(governance_env["inv_path"]).parent)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def raci_env(governance_env, monkeypatch):
    """Extend governance_env with RACI matrix data."""
    import routes.governance._constants as gov_constants

    raci_path = str(pathlib.Path(governance_env["inv_path"]).parent / "raci_matrix.json")
    with open(raci_path, "w") as f:
        json.dump(copy.deepcopy(_BASE_RACI), f)

    monkeypatch.setattr(gov_constants, "RACI_PATH", raci_path)
    governance_env["raci_path"] = raci_path
    return governance_env


@pytest.fixture
def raci_client(raci_env, monkeypatch):
    """Flask test client with isolated RACI data."""
    from config import config
    monkeypatch.setattr(config, "get_input_dir",
                        lambda: pathlib.Path(raci_env["inv_path"]).parent)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def mrc_env(tmp_path, monkeypatch):
    """Set up isolated MRC meetings data."""
    import routes.governance._constants as gov_constants
    meetings_path = str(tmp_path / "mrc_meetings.json")
    uploads_dir = str(tmp_path / "mrc_uploads")
    with open(meetings_path, "w") as f:
        json.dump([], f)
    monkeypatch.setattr(gov_constants, "MRC_MEETINGS_PATH", meetings_path)
    monkeypatch.setattr(gov_constants, "MRC_UPLOADS_DIR", uploads_dir)
    return {"meetings_path": meetings_path, "uploads_dir": uploads_dir}


@pytest.fixture
def mrc_client(mrc_env, monkeypatch):
    """Flask test client with isolated MRC data."""
    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ── Lineage fixtures ─────────────────────────────────────────────

@pytest.fixture
def lineage_env(tmp_path, monkeypatch):
    """Set up isolated lineage data files and input directory for testing."""
    import routes.governance._constants as gov_constants

    lineage_path = str(tmp_path / "data_lineage.json")
    field_lineage_path = str(tmp_path / "field_lineage_registry.json")

    inv_path = str(tmp_path / "model_inventory.json")
    audit_path = str(tmp_path / "model_audit_log.json")
    with open(inv_path, "w") as f:
        json.dump({"metadata": {}, "models": []}, f)
    with open(audit_path, "w") as f:
        json.dump([], f)

    monkeypatch.setattr(gov_constants, "INVENTORY_PATH", inv_path)
    monkeypatch.setattr(gov_constants, "AUDIT_LOG_PATH", audit_path)
    monkeypatch.setattr(gov_constants, "LINEAGE_PATH", lineage_path)
    monkeypatch.setattr(gov_constants, "FIELD_LINEAGE_PATH", field_lineage_path)

    return {
        "tmp_path": tmp_path,
        "lineage_path": lineage_path,
        "field_lineage_path": field_lineage_path,
    }


@pytest.fixture
def lineage_client(lineage_env, monkeypatch):
    """Flask test client with isolated lineage data."""
    from config import config

    monkeypatch.setattr(
        config, "get_input_dir",
        lambda: pathlib.Path(lineage_env["tmp_path"]),
    )

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ── Full trace env (shared by test_lineage_coverage_part*.py) ────


@pytest.fixture
def full_trace_env(tmp_path, monkeypatch):
    """Trace environment with gaugehd, sequence_gauge, mortgage,
    propertyhc, trade_marks, eod, counterparty, classifier summary,
    and market_state files."""
    from config import config

    input_dir = tmp_path / "input"
    input_dir.mkdir()
    classifiers_dir = tmp_path / "classifiers"
    classifiers_dir.mkdir()
    blotter_dir = tmp_path / "blotter"
    blotter_dir.mkdir()
    (blotter_dir / "eod").mkdir()

    monkeypatch.setattr(config, "get_input_dir", lambda: input_dir)
    monkeypatch.setattr(config, "get_classifiers_dir", lambda: classifiers_dir)
    monkeypatch.setattr(config, "get_trading_dir", lambda: blotter_dir)

    # gauge.json
    with open(input_dir / "gauge.json", "w") as f:
        json.dump({"flood_gauges": [
            {"FloodGauge": {"Header": {"GaugeID": "GAUGE-FULL01"}}}
        ]}, f)

    # gaugehc.json
    with open(input_dir / "gaugehc.json", "w") as f:
        json.dump({"hazard_curves": {"GAUGE-FULL01": {"gev": {}}}}, f)

    # gaugets/ per-gauge file
    (input_dir / "gaugets").mkdir()
    with open(input_dir / "gaugets" / "GAUGE-FULL01.json", "w") as f:
        json.dump({"gauge_id": "GAUGE-FULL01"}, f)

    # gaugehd/ historical daily observations
    (input_dir / "gaugehd").mkdir()
    with open(input_dir / "gaugehd" / "GAUGE-FULL01_daily.csv", "w") as f:
        f.write("date,level\n2026-01-01,3.5\n")

    # sequence_gauge/ per-gauge split files
    sg_dir = input_dir / "sequence_gauge"
    sg_dir.mkdir()
    with open(sg_dir / "GAUGE-FULL01.json", "w") as f:
        json.dump({"gauge_id": "GAUGE-FULL01", "peaks": [4.1]}, f)
    with open(sg_dir / "_index.json", "w") as f:
        json.dump({"gauge_ids": ["GAUGE-FULL01"]}, f)

    # classifier .joblib + training_summary.json
    (classifiers_dir / "GAUGE-FULL01.joblib").write_bytes(b"fake")
    with open(classifiers_dir / "training_summary.json", "w") as f:
        json.dump({"gauges": [{"gauge_id": "GAUGE-FULL01", "auc": 0.95}]}, f)

    # market_state.json referencing gauge
    with open(blotter_dir / "market_state.json", "w") as f:
        json.dump({"hazard_curves": {"GAUGE-FULL01": {}}}, f)

    # property.json
    with open(input_dir / "property.json", "w") as f:
        json.dump({"properties": [
            {"PropertyHeader": {"Header": {"PropertyID": "PROP-FULL01"}}}
        ]}, f)

    # propertyts/
    (input_dir / "propertyts").mkdir()
    with open(input_dir / "propertyts" / "PROP-FULL01.json", "w") as f:
        json.dump({"property_id": "PROP-FULL01"}, f)

    # loan.json
    with open(input_dir / "loan.json", "w") as f:
        json.dump({"loans": [{"property_id": "PROP-FULL01", "ltv": 0.75}]}, f)

    # propertyhc.json
    with open(input_dir / "propertyhc.json", "w") as f:
        json.dump({"property_curves": {"PROP-FULL01": {"depth": 1.2}}}, f)

    # propertyshd.json / propertyshe.json
    with open(input_dir / "propertyshd.json", "w") as f:
        json.dump({"property_hazard_curves": {"PROP-FULL01": {"shd": True}}}, f)
    with open(input_dir / "propertyshe.json", "w") as f:
        json.dump({"property_hazard_curves": {"PROP-FULL01": {"she": True}}}, f)

    # prs/ trades
    (input_dir / "prs").mkdir()
    with open(input_dir / "prs" / "PRS-FULL01.json", "w") as f:
        json.dump({"PhysicalSwap": {
            "Header": {"SwapID": "PRS-FULL01"},
            "GaugeSet": {"GaugeBasket": [{"GaugeID": "GAUGE-FULL01"}]},
            "Counterparty": "CTPY-FULL01",
        }}, f)

    # trade_marks.json
    with open(blotter_dir / "trade_marks.json", "w") as f:
        json.dump({"marks": [{"trade_id": "PRS-FULL01", "mtm": 1000}]}, f)

    # eod snapshot referencing trade
    with open(blotter_dir / "eod" / "2026-03-25_PRS-FULL01.json", "w") as f:
        json.dump({"trade_id": "PRS-FULL01", "pnl": 500}, f)

    # counterparty.json
    with open(input_dir / "counterparty.json", "w") as f:
        json.dump({"counterparties": [
            {"counterparty_id": "CTPY-FULL01", "name": "Test Bank"}
        ]}, f)

    return {"input_dir": input_dir, "classifiers_dir": classifiers_dir,
            "blotter_dir": blotter_dir}
