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

"""Governance data for MKM-XV-001 (PRS XVA Model).

The scalar record and the assumption / limitation / weakness registers, split
from ``register_xv001`` as ``_ef001_data`` is from ``register_ef001``. Every
entry comes from building and testing the model; see
``PhysicalRisk/docs/xva/project_plan.md`` (sections 9-13) and the model
document ``PhysicalRisk/docs/models/prs_xva/MKM-XV-001_model_document.pdf``.
"""
from __future__ import annotations

MODEL_ID = "MKM-XV-001"

# Version 0.9.0: built (WP0-WP4) and submitted for independent validation.
# Nothing reaches a price or P&L until it is validated, and KVA not until the
# regulatory treatment of a PRS is decided.
FIELDS = {
    "name": "PRS XVA Model",
    "short_name": "PRS XVA",
    "category": "Pricing",
    "type": "Analytical Model",
    "tier": 1,
    "tier_rationale": (
        "Its output changes the client price of every PRS and, once booked, fair "
        "value and daily P&L. KVA alone is about 43bp of running spread on a "
        "204bp trade. It sits on top of the tier-1 PRS pricer (MKM-PR-001)."
    ),
    "materiality": "High",
    "complexity": "High",
    "methodology": (
        "Green (2015) semi-replication: all-in value = risk-free PRS value plus "
        "U = CVA + FVA (one-bond strategy, discounting at r_F + lambda_C), with "
        "the semi-replication view (CVA + DVA + FCA) computed beside it and DVA "
        "disclosed. A closed-form engine for one trade under deterministic flood "
        "hazard; a 10,000-path Monte Carlo with a CIR++ flood-hazard factor fitted "
        "to the pricer's curve, correlated triggers from the MKM-EF-001 catalogue, "
        "close-out netting, VM with an MPoR lookback, IM, and a wrong-way-risk "
        "stress. KVA on SA-CCR and BA-CVA capital computed in every state."
    ),
    "methodology_rationale": (
        "A PRS is a CDS with a flood trigger, so exposure is a jump to the full "
        "notional. Under deterministic hazard every term has a closed form, the "
        "exact benchmark the Monte Carlo reproduces. The model is an overlay that "
        "reproduces MKM-PR-001 at t = 0 and does not change it."
    ),
    "source_module": "src/models/xva/",
    "repo_location": "PhysicalRisk",
    "codebase": "PhysicalRisk",
    # Placed with MKM-PR-001, the pricer it overlays, so a committee covers it
    # from its first event rather than from a later edit.
    "division": "PhysicalRisk",
    "line_of_business": "PRS Platform",
    "functional_group": "FG-004",
    "owner": "David K Kelly",
    "status": "Proposed",
    "lifecycle_stage": "Validation",
    "version": "0.9.0",
    "validation_status": "Pending",
    "rag_rating": "Amber",
    "rating_rationale": (
        "Amber: built and benchmarked (independent re-implementation to 1e-8, "
        "Basel SA-CCR worked examples, Monte Carlo against closed form within "
        "3 SE). Counterparty credit, funding spread and hazard volatility are "
        "placeholders, and the regulatory treatment that drives KVA is undecided."
    ),
    "review_frequency": "Annual",
    "unit_tests": "Yes",
    "integration_tests": "Yes",
    "benchmark_tests": "Yes",
}

ASSUMPTIONS = [
    {
        "description": (
            "One-bond funding strategy: unilateral CVA plus a symmetric FVA at the "
            "bank's funding spread, discounted at r_F + lambda_C (Green 9.64-9.67). "
            "DVA is computed under semi-replication and disclosed, not booked."
        ),
        "impact": "High",
        "monitoring": "Both views reported on every run; they coincide when R_B = 0.",
        "mitigation": "Funding strategy is a config switch.",
    },
    {
        "description": (
            "Risk-free close-out (close-out amount = risk-free value), so the "
            "adjustment PDE is linear and the XVA terms separate."
        ),
        "impact": "Medium",
        "monitoring": "Risky close-out to be run as a sensitivity in validation.",
        "mitigation": "Documented against Green's alternatives.",
    },
    {
        "description": (
            "The PRS terminates at the first trigger and pays the notional after "
            "a settlement lag (provisionally 5 business days), matching the pricer "
            "so that the risk-free value agrees at t = 0."
        ),
        "impact": "High",
        "monitoring": "Daily KPI: engine V(0) against front-office MTM, 5bp of notional.",
        "mitigation": "Lag carried on the trade (Payouts.SettlementDays).",
    },
    {
        "description": (
            "Flood hazard follows a CIR++ catchment factor (Y0 = theta = 1) fitted "
            "exactly to the pricer's flat hazard; kappa 0.5 and sigma 0.3 are "
            "placeholders. Hazard volatility multiplies the buyer's CVA about 4.6x."
        ),
        "impact": "High",
        "monitoring": "Sensitivity table in the model document.",
        "mitigation": "Calibration to the history of re-estimated hazard (no owner yet).",
    },
    {
        "description": (
            "Counterparty default is independent of flood in the price (beta = 0); "
            "wrong-way risk is a governed stress whose sign depends on direction."
        ),
        "impact": "High",
        "monitoring": "WWR stress by counterparty type and direction.",
        "mitigation": "Normalised path weighting (Green 7.17).",
    },
    {
        "description": (
            "Capital is SA-CCR plus BA-CVA (reduced), phi = 0, gamma_K 12% and a "
            "10.5% capital ratio shared with MKM-CR-001; KVA is reported, not booked."
        ),
        "impact": "High",
        "monitoring": "KVA under each regulatory treatment and with the RRAO.",
        "mitigation": "One shared regulatory module for MKM-XV-001 and MKM-CR-001.",
    },
]

LIMITATIONS = [
    {
        "description": (
            "The regulatory characterisation of a PRS (derivative or insurance; "
            "SA-CCR asset class; whether the FRTB residual-risk add-on applies) is "
            "undecided. It is worth about 32bp of spread on a 5y trade, and the RRAO "
            "a further 15bp."
        ),
        "impact": "High",
        "monitoring_trigger": "Before any KVA figure is used in a price.",
        "compensating_control": "Question paper raised; KVA kept out of the booked figure.",
    },
    {
        "description": (
            "Counterparty credit (rating proxy), the bank's funding spread and CSA "
            "terms are synthetic or placeholder; no real input or lineage exists."
        ),
        "impact": "High",
        "monitoring_trigger": "Before production sign-off.",
        "compensating_control": "Every output carries an ILLUSTRATIVE status line.",
    },
    {
        "description": (
            "The classical MPoR lookback freezes collateral but not trade cash "
            "flows: a protection buyer that posted VM is briefly over-collateralised "
            "when it pays premium, so VM can raise its CVA (Andersen-Pykhtin-Sokol)."
        ),
        "impact": "Medium",
        "monitoring_trigger": "Any CSA'd PRS netting set.",
        "compensating_control": "Recorded; advanced MPoR conventions are a candidate extension.",
    },
    {
        "description": (
            "The desk uses one flat hazard per gauge (the CIR++ fit is flat); the "
            "front office's hazard term structure and whole-year tenors differ, so "
            "the valuation KPI is expected to breach on the live book."
        ),
        "impact": "Medium",
        "monitoring_trigger": "Daily valuation KPI.",
        "compensating_control": "Breaches are reported, never auto-corrected.",
    },
    {
        "description": (
            "Triggers are rare, so exposure cannot be meaningfully backtested; "
            "outcomes analysis rests on MKM-EF-001 hazard backtests, the KPI and "
            "the EOD XVA P&L line."
        ),
        "impact": "Medium",
        "monitoring_trigger": "Annual review.",
        "compensating_control": "Closed-form benchmark and limiting-case tests.",
    },
    {
        "description": (
            "Property PRS has no term pricer, so XVA covers gauge PRS only; "
            "BA-CVA is standalone per counterparty, with no portfolio diversification."
        ),
        "impact": "Medium",
        "monitoring_trigger": "Any request for XVA on Property PRS or portfolio KVA.",
        "compensating_control": "Scope restricted to TradeType 'PRS'.",
    },
]

WEAKNESSES = [
    "Variation margin does not remove the jump to notional at the trigger; only "
    "initial margin or prefunding does.",
    "The wrong-way-risk driver is the netting set's triggered gauges, not the "
    "counterparty's real flood book.",
    "KVA is allocated to trades pro rata to notional; only the netting-set total "
    "is invariant (Green Ch. 15).",
    "Inherited from MKM-PR-001: a fair-spread floor in MTM, no settlement lag, a "
    "6M premium frequency on the trade against quarterly pricing.",
]

# Chain edges, producer -> consumer. MKM-XV-001 consumes the PRS value
# (MKM-PR-001) and the event catalogue (MKM-EF-001), and feeds the Trading Desk
# (MKM-TD-001), which shows XVA on the blotter and in EOD P&L.
CHAIN_EDGES = [
    ("MKM-PR-001", MODEL_ID),
    ("MKM-EF-001", MODEL_ID),
    (MODEL_ID, "MKM-TD-001"),
]
