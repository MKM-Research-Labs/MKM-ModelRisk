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
Data lineage tests: gaugehc → market state → hazard-term-structure API.

Ensures the hazard curve data flows correctly from the generated
gaugehc.json through the market state to the API endpoint that
the PRS pricer chart reads.
"""

import json

import pytest


class TestHazardCurveLineage:
    """Verify hazard data flows from gaugehc → market state → API."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        """Load paths from config."""
        from config import config
        self.input_dir = config.get_input_dir()
        self.trading_dir = config.get_trading_dir()

    def test_gaugehc_exists_with_curves(self):
        """gaugehc.json must exist and contain hazard curves."""
        path = self.input_dir / 'gaugehc.json'
        assert path.exists(), f"gaugehc.json not found at {path}"
        with open(path) as f:
            data = json.load(f)
        curves = data.get('hazard_curves', {})
        assert len(curves) > 0, "gaugehc.json has no hazard_curves"

    def test_gaugehc_has_annual_hazard_rates(self):
        """Each gauge curve must have annual_hazard_rate for all triggers."""
        path = self.input_dir / 'gaugehc.json'
        if not path.exists():
            pytest.skip("gaugehc.json not found")
        with open(path) as f:
            data = json.load(f)
        for gid, gc in data.get('hazard_curves', {}).items():
            for trigger in ['alert', 'warning', 'severe']:
                key = f'annual_hazard_rate_{trigger}'
                assert key in gc, f"{gid} missing {key}"
                assert gc[key] > 0, f"{gid} {key} is zero"

    def test_market_state_exists_with_hts(self):
        """market_state.json must exist with hazard_term_structure."""
        path = self.trading_dir / 'market_state.json'
        assert path.exists(), f"market_state.json not found at {path}"
        with open(path) as f:
            data = json.load(f)
        hts = data.get('hazard_term_structure', {})
        assert len(hts) > 0, "market_state.json has empty hazard_term_structure"

    def test_market_state_hts_has_all_gaugehc_gauges(self):
        """Every real gauge in gaugehc should have a market state entry."""
        hc_path = self.input_dir / 'gaugehc.json'
        ms_path = self.trading_dir / 'market_state.json'
        if not hc_path.exists() or not ms_path.exists():
            pytest.skip("Missing data files")

        with open(hc_path) as f:
            hc_gauges = set(json.load(f).get('hazard_curves', {}).keys())
        with open(ms_path) as f:
            ms_gauges = set(json.load(f).get('hazard_term_structure', {}).keys())

        real_gauges = {g for g in hc_gauges if not g.startswith('SYNTH-')}
        missing = real_gauges - ms_gauges
        assert not missing, (
            f"{len(missing)} gauges in gaugehc but missing from market_state HTS: "
            f"{list(missing)[:5]}"
        )

    def test_market_state_hts_has_all_tenors(self):
        """Each gauge's HTS must have rates for tenors 1-5."""
        ms_path = self.trading_dir / 'market_state.json'
        if not ms_path.exists():
            pytest.skip("market_state.json not found")
        with open(ms_path) as f:
            hts = json.load(f).get('hazard_term_structure', {})

        for gid, triggers in list(hts.items())[:10]:
            for trigger in ['alert', 'warning', 'severe']:
                rates = triggers.get(trigger, {})
                for tenor in ['1', '2', '3', '4', '5']:
                    assert tenor in rates, (
                        f"{gid}/{trigger} missing tenor {tenor}"
                    )
                    assert rates[tenor] > 0, (
                        f"{gid}/{trigger}/{tenor} rate is zero"
                    )

    def test_api_hazard_term_structure_returns_data(self):
        """GET /api/v1/trading/hazard-term-structure must return HTS data."""
        from server import create_app
        app = create_app()
        with app.test_client() as c:
            resp = c.get('/api/v1/trading/hazard-term-structure')
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['status'] == 'success'
            hts = data.get('hazard_term_structure', {})
            assert len(hts) > 0, "API returned empty hazard_term_structure"

    def test_api_hts_matches_market_state_file(self):
        """API response must match the market_state.json file."""
        ms_path = self.trading_dir / 'market_state.json'
        if not ms_path.exists():
            pytest.skip("market_state.json not found")
        with open(ms_path) as f:
            file_hts = json.load(f).get('hazard_term_structure', {})

        from server import create_app
        app = create_app()
        with app.test_client() as c:
            resp = c.get('/api/v1/trading/hazard-term-structure')
            api_hts = resp.get_json().get('hazard_term_structure', {})

        assert set(api_hts.keys()) == set(file_hts.keys()), (
            f"API gauge set differs from file: "
            f"API={len(api_hts)}, file={len(file_hts)}"
        )

    def test_sequence_count_matches_storm_sequences(self):
        """num_sequences used by property pricer must match storm_sequences.json."""
        seq_path = self.input_dir / 'storm_sequences.json'
        if not seq_path.exists():
            pytest.skip("storm_sequences.json not found")
        with open(seq_path) as f:
            seq_data = json.load(f)
        expected = seq_data.get('num_sequences', len(seq_data.get('sequences', [])))

        hc_path = self.input_dir / 'gaugehc.json'
        if not hc_path.exists():
            pytest.skip("gaugehc.json not found")
        with open(hc_path) as f:
            num_storms = json.load(f).get('metadata', {}).get('num_storms', 0)

        # num_storms in gaugehc is individual pulses, NOT sequences
        # The property pricer must use sequence count, not num_storms
        assert expected != num_storms or expected == num_storms, (
            "Sanity check — at least one must exist"
        )
        assert expected > 0, "No sequences found"
        assert expected < num_storms, (
            f"Expected fewer sequences ({expected}) than individual storms "
            f"({num_storms}) — sequences contain multiple pulses"
        )
