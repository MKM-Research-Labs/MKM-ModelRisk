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
Data lineage tests: PRS trade commit → blotter → active gauges.

Uses monkeypatch + tmp_path to isolate from production data.
Follows the same pattern as tests/routes/test_prs_basic.py.
"""

import json
import shutil

import pytest


@pytest.fixture
def isolated_client(tmp_path, monkeypatch):
    """Flask test client with all write paths redirected to tmp_path."""
    from config import config
    from server import create_app

    prs_dir = tmp_path / "reports" / "prs"
    prs_dir.mkdir(parents=True)
    trading_dir = tmp_path / "trading"
    trading_dir.mkdir(parents=True)

    # Copy market state so blotter/delta engine can load
    prod_trading = config.get_trading_dir()
    if (prod_trading / "market_state.json").exists():
        shutil.copy(prod_trading / "market_state.json", trading_dir / "market_state.json")
    if (prod_trading / "trade_marks.json").exists():
        shutil.copy(prod_trading / "trade_marks.json", trading_dir / "trade_marks.json")

    monkeypatch.setattr(config, "get_reports_dir",
                        lambda name: tmp_path / "reports" / name)
    monkeypatch.setattr(config, "get_trading_dir", lambda: trading_dir)

    from fixtures_admin import AuthenticatedTestClient
    app = create_app()
    app.config['TESTING'] = True
    app.test_client_class = AuthenticatedTestClient
    with app.test_client() as c:
        yield c


@pytest.fixture
def sample_trade_payload():
    """Minimal valid PRS trade commit payload."""
    return {
        'gauge_id': 'GAUGE-ef7f75ec',
        'gauge_name': 'Thames Caversham Bridge',
        'trigger': 'severe',
        'direction': 'pay',
        'notional': 5000000,
        'spread_bps': 300.0,
        'tenor': 3,
        'counterparty_id': 'CTPY-001',
        'counterparty_name': 'Test Counterparty',
    }


class TestTradeCommitCreatesFile:
    """POST /prs/commit must create a trade file in the temp directory."""

    def test_commit_returns_swap_id(self, isolated_client, sample_trade_payload):
        resp = isolated_client.post('/api/v1/prs/commit',
                                    json=sample_trade_payload,
                                    content_type='application/json')
        data = resp.get_json()
        assert data['status'] == 'success', f"Commit failed: {data}"
        assert data['swap_id'].startswith('PRS-')

    def test_commit_writes_to_temp_dir(self, isolated_client, sample_trade_payload,
                                        tmp_path):
        resp = isolated_client.post('/api/v1/prs/commit',
                                    json=sample_trade_payload,
                                    content_type='application/json')
        swap_id = resp.get_json()['swap_id']

        trade_file = tmp_path / "reports" / "prs" / f"{swap_id}.json"
        assert trade_file.exists(), f"Trade file not in temp dir: {trade_file}"


class TestBlotterShowsNewTrade:
    """GET /trading/blotter must include a newly committed trade."""

    def test_new_trade_in_blotter(self, isolated_client, sample_trade_payload):
        commit_data = isolated_client.post(
            '/api/v1/prs/commit',
            json=sample_trade_payload,
            content_type='application/json'
        ).get_json()
        swap_id = commit_data['swap_id']

        blotter = isolated_client.get('/api/v1/trading/blotter').get_json()
        assert blotter['status'] == 'success'
        trade_ids = [t.get('swap_id') for t in blotter.get('trades', [])]
        assert swap_id in trade_ids, (
            f"Trade {swap_id} not in blotter ({len(trade_ids)} trades)"
        )


class TestActiveGaugesIncludesNewTrade:
    """GET /trading/blotter/active-gauges must include the new trade's gauge."""

    def test_gauge_in_active_list(self, isolated_client, sample_trade_payload):
        gauge_id = sample_trade_payload['gauge_id']

        isolated_client.post('/api/v1/prs/commit',
                             json=sample_trade_payload,
                             content_type='application/json')

        active = isolated_client.get(
            '/api/v1/trading/blotter/active-gauges'
        ).get_json()
        assert active['status'] == 'success'
        assert gauge_id in active.get('gauge_ids', []), (
            f"{gauge_id} not in active gauges after commit"
        )
