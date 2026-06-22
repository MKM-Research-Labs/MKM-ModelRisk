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
Data lineage tests: PPRS trade file → client blotter endpoint.

Verifies that property PRS JSON files written to the prs/ directory
appear correctly in the GET /trading/client response with all
PropertySet fields intact.

Uses monkeypatch + tmp_path to isolate from production data.
"""

import json
import shutil

import pytest


SAMPLE_PPRS_TRADE = {
    'PhysicalSwap': {
        'Header': {
            'SwapID': 'PRS-PLINEAGE1',
            'CatchmentID': 'thames',
            'TradeType': 'PropertyPRS',
            'CounterParty': 'CTPY-lineage-test',
            'CounterPartyName': 'Lineage Test Bank (A)',
            'PartyId': 'MKM-RESEARCH-001',
            'ValuationDate': '2026-04-07',
            'ProtectionStart': '2026-04-09',
            'TradeStatus': 'Committed',
        },
        'LegData': {
            'LegType': 'Fixed',
            'Payer': False,
            'Currency': 'GBP',
            'Notional': 80_000_000,
            'DayCounter': 'ACT/360',
            'FixedLegRate': 0.032,
        },
        'ScheduleData': {
            'StartDate': '2026-04-09',
            'EndDate': '2029-04-09',
            'Tenor': '6M',
            'Calendar': 'London',
        },
        'PropertySet': {
            'PropertyID': 'PROP-lineage-01',
            'PropertyAddress': '99 Lineage Lane',
            'Postcode': 'SW1 9LN',
            'LocalAuthority': 'Westminster',
            'PropertyValue': 1_500_000.0,
            'EAFloodZone': 'Zone 3a',
            'ReferenceGauge': 'SYNTH-lineage-01',
            'Latitude': 51.488,
            'Longitude': -0.135,
        },
        'GaugeSet': {
            'GaugeSetID': 'GSET-PROP-lineage-01',
            'CatchmentID': 'thames',
            'GaugeCount': 1,
            'GaugeBasket': [{
                'GaugeID': 'SYNTH-lineage-01',
                'GaugeName': 'Lineage Synthetic',
                'Weight': 1.0,
                'TriggerLevel': 'severe',
            }],
        },
        'Triggers': {'TriggerType': 'Any', 'TriggerThreshold': 1},
        'Payouts': {'Currency': 'GBP', 'MaxPayout': 80_000_000},
        'Pricing': {
            'SpreadBps': 320,
            'FairSpreadBps': 314.5,
            'NPV': 72_000.0,
            'PremiumLegPV': 6_700_000.0,
            'ProtectionLegPV': 6_628_000.0,
            'RiskyAnnuity': 2.61,
            'YieldCurve': {'1': 0.035, '2': 0.04, '3': 0.043},
            'Recovery': 0.0,
            'TriggerLevel': 'severe',
        },
    }
}


@pytest.fixture
def lineage_client(tmp_path, monkeypatch):
    """Flask test client with a single PPRS trade file in an isolated prs/ dir."""
    from config import config
    from server import create_app

    prs_dir = tmp_path / "reports" / "prs"
    prs_dir.mkdir(parents=True)
    trading_dir = tmp_path / "trading"
    trading_dir.mkdir(parents=True)

    # Copy market state so dependent engines can load
    prod_trading = config.get_trading_dir()
    for fname in ("market_state.json", "trade_marks.json"):
        src = prod_trading / fname
        if src.exists():
            shutil.copy(src, trading_dir / fname)

    # Write the PPRS trade file
    swap_id = SAMPLE_PPRS_TRADE['PhysicalSwap']['Header']['SwapID']
    with open(prs_dir / f"{swap_id}.json", "w") as f:
        json.dump(SAMPLE_PPRS_TRADE, f)

    monkeypatch.setattr(config, "get_reports_dir",
                        lambda name: tmp_path / "reports" / name)
    monkeypatch.setattr(config, "get_trading_dir", lambda: trading_dir)

    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


class TestPPRSFileToClientBlotter:
    """PPRS-*.json on disk must appear in GET /trading/client."""

    def test_pprs_trade_in_client_blotter(self, lineage_client):
        resp = lineage_client.get('/api/v1/trading/client')
        data = resp.get_json()
        assert data['status'] == 'success'
        swap_ids = [t['swap_id'] for t in data['trades']]
        assert 'PRS-PLINEAGE1' in swap_ids, \
            f"PRS-PLINEAGE1 not in client blotter ({swap_ids})"

    def test_property_fields_survive_lineage(self, lineage_client):
        """PropertySet fields must propagate from JSON file to API response."""
        resp = lineage_client.get('/api/v1/trading/client')
        data = resp.get_json()
        trade = [t for t in data['trades']
                 if t['swap_id'] == 'PRS-PLINEAGE1'][0]

        assert trade['property_id'] == 'PROP-lineage-01'
        assert trade['property_address'] == '99 Lineage Lane'
        assert trade['postcode'] == 'SW1 9LN'
        assert trade['local_authority'] == 'Westminster'
        assert trade['ea_flood_zone'] == 'Zone 3a'

    def test_pricing_fields_survive_lineage(self, lineage_client):
        """Pricing fields must propagate from JSON file to API response."""
        resp = lineage_client.get('/api/v1/trading/client')
        data = resp.get_json()
        trade = [t for t in data['trades']
                 if t['swap_id'] == 'PRS-PLINEAGE1'][0]

        assert trade['spread_bps'] == 320
        assert trade['fair_spread_bps'] == 314.5
        assert trade['npv'] == 72_000.0
        assert trade['notional'] == 80_000_000

    def test_pprs_not_in_gauge_blotter(self, lineage_client):
        """PPRS trades must NOT appear in the regular gauge blotter."""
        resp = lineage_client.get('/api/v1/trading/blotter')
        data = resp.get_json()
        swap_ids = [t.get('swap_id') for t in data.get('trades', [])]
        assert 'PRS-PLINEAGE1' not in swap_ids, \
            "Property PRS trade should not appear in gauge blotter"

    def test_summary_reflects_pprs_count(self, lineage_client):
        """Summary num_trades should count PPRS trades."""
        resp = lineage_client.get('/api/v1/trading/client')
        data = resp.get_json()
        assert data['summary']['num_trades'] == 1
        assert data['summary']['total_notional'] == 80_000_000
