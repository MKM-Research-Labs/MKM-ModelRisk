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

"""Tests for lineage.field_usage — CDM field downstream-usage tiering."""

import pytest

from lineage.field_usage import (
    AMBER,
    AMBER_PREFIXES,
    EXACT_FIELDS,
    GREEN,
    RED,
    TIER_META,
    classify,
    lineage,
    tier_meta,
)

VALID_TIERS = {RED, AMBER, GREEN}

BRI_WIND = "ProtectionMeasures.RiskAssessment.GoverningBodyRatings.BRIWindScore"


class TestClassify:

    def test_bri_wind_score_feeds_prs_red(self):
        assert classify(BRI_WIND) == RED

    def test_wind_threshold_red(self):
        assert classify("ProtectionMeasures.HazardProfile.WindThresholdMinorMps") == RED

    def test_floor_level_red_both_assets(self):
        assert classify("PropertyHeader.Construction.FloorLevelMeters") == RED
        assert classify("CommercialAsset.Construction.FloorLevelMeters") == RED

    def test_valuation_red(self):
        assert classify("PropertyHeader.Valuation.PropertyValue") == RED

    def test_transaction_history_amber_by_prefix(self):
        assert classify("TransactionHistory.Insurance.InsurancePremium") == AMBER

    def test_loan_terms_amber(self):
        assert classify("RLoan.FinancialTerms.OriginalLoan") == AMBER
        assert classify("Mortgage.CurrentStatus.OutstandingBalance") == AMBER

    def test_counterparty_accounts_amber(self):
        assert classify("CounterpartySet.Party.Accounts.0.IBAN") == AMBER

    def test_descriptive_field_defaults_green(self):
        assert classify("PropertyHeader.PropertyAttributes.NumberBedrooms") == GREEN
        assert classify("EnergyPerformance.Ratings.EPCRating") == GREEN

    def test_unknown_path_is_green(self):
        assert classify("Totally.Unknown.Path") == GREEN


class TestLineage:

    def test_returns_chain_and_consumers(self):
        e = lineage(BRI_WIND)
        assert e["tier"] == RED
        assert isinstance(e["chain"], list) and len(e["chain"]) >= 2
        assert isinstance(e["consumers"], list) and e["consumers"]
        assert e["summary"]

    def test_chain_starts_at_field_ends_at_output(self):
        chain = lineage(BRI_WIND)["chain"]
        assert chain[0]["kind"] == "field"
        assert "PRS" in chain[-1]["node"]

    def test_green_default_is_report(self):
        e = lineage("PropertyHeader.PropertyAttributes.NumberBedrooms")
        assert e["tier"] == GREEN
        assert "report" in e["summary"].lower()

    def test_never_returns_none(self):
        assert lineage("a.b.c") is not None


class TestRegistryIntegrity:

    def test_every_exact_entry_well_formed(self):
        for path, e in EXACT_FIELDS.items():
            assert e["tier"] in VALID_TIERS, path
            assert isinstance(e["chain"], list) and e["chain"], path
            assert isinstance(e["consumers"], list) and e["consumers"], path
            assert e.get("summary"), path
            for node in e["chain"]:
                assert "node" in node and "kind" in node, path

    def test_exact_entries_are_red(self):
        # The curated exact registry is the RED (feeds-PRS) set.
        for path, e in EXACT_FIELDS.items():
            assert e["tier"] == RED, path

    def test_amber_prefixes_well_formed(self):
        for prefix, e in AMBER_PREFIXES:
            assert isinstance(prefix, str) and prefix
            assert e["tier"] == AMBER, prefix
            assert isinstance(e["chain"], list) and e["chain"]

    def test_tier_meta_complete(self):
        assert set(tier_meta()) == VALID_TIERS
        for tier, meta in TIER_META.items():
            assert meta["label"] and meta["colour"] and meta["description"]
