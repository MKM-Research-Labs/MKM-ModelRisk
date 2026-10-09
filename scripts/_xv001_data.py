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
entry comes from the design and its agreed decisions, not demo filler; see
``PhysicalRisk/docs/xva/project_plan.md`` (sections 3, 4.4, 7 and 9).
"""
from __future__ import annotations

MODEL_ID = "MKM-XV-001"

# Version 0.1.0: designed and agreed, nothing built. The model must be
# validated in full before any figure reaches a price, a blotter or P&L.
FIELDS = {
    "name": "PRS XVA Model",
    "short_name": "PRS XVA",
    "category": "Pricing",
    "type": "Analytical Model",
    "tier": 1,
    "tier_rationale": (
        "Its output changes the client price of every PRS (all-in spread = fair "
        "spread less XVA over the risky annuity) and, once booked, fair value and "
        "daily P&L. It sits on top of the tier-1 PRS pricer (MKM-PR-001)."
    ),
    "materiality": "High",
    "complexity": "High",
    "methodology": (
        "Green (2015) semi-replication: all-in value = risk-free PRS value plus "
        "U = CVA + FVA + KVA (DVA disclosed, not booked), each a spread times a "
        "discounted expected exposure with survival discounting at r + lambda_B "
        "+ lambda_C. Two engines: a closed form for a single trade under "
        "deterministic flood hazard, and a 10,000-path Monte Carlo on the "
        "MKM-EF-001 event draws adding stochastic hazard, netting, CSA collateral "
        "with a margin period of risk, and wrong-way risk. KVA on SA-CCR and "
        "BA-CVA capital computed per path."
    ),
    "methodology_rationale": (
        "A PRS is a CDS with a flood trigger, so its exposure is a jump to the "
        "full notional rather than a diffusion. Under deterministic hazard the "
        "pre-trigger value is deterministic and every term has a closed form, "
        "which is the exact benchmark the Monte Carlo must reproduce. The model "
        "is an overlay that consumes MKM-PR-001 rather than changing it, so the "
        "pricer's validation stands."
    ),
    "source_module": "src/models/xva/",
    "repo_location": "PhysicalRisk",
    "codebase": "PhysicalRisk",
    "owner": "David K Kelly",
    "status": "Proposed",
    "lifecycle_stage": "Development",
    "version": "0.1.0",
    "validation_status": "Pending",
    "rag_rating": "Amber",
    "rating_rationale": (
        "Amber: design agreed and WP0 under way, nothing built. Counterparty, "
        "funding and CSA data are synthetic, and the regulatory treatment that "
        "drives KVA is not yet decided (see limitations)."
    ),
    "review_frequency": "Annual",
    "unit_tests": "No",
    "integration_tests": "No",
    "benchmark_tests": "No",
}

ASSUMPTIONS = [
    {
        "description": (
            "One-bond funding strategy: unilateral CVA plus a symmetric FVA at the "
            "bank's funding spread; DVA is computed and disclosed but not booked, "
            "so own credit is not counted twice (Morini-Prampolini)."
        ),
        "impact": "High",
        "monitoring": "DVA shown beside FVA on every result for comparison.",
        "mitigation": "Funding strategy is a config switch; alternatives are documented.",
    },
    {
        "description": (
            "Risk-free close-out (close-out amount = risk-free value), so the "
            "adjustment PDE is linear and the XVA terms separate."
        ),
        "impact": "Medium",
        "monitoring": "Risky close-out run as a sensitivity in the validation pack.",
        "mitigation": "Documented against Green's risky and survivor-funding alternatives.",
    },
    {
        "description": (
            "The PRS terminates at the first trigger and pays the full notional "
            "after a settlement lag (provisionally 5 business days), matching the "
            "trade pricer so that the risk-free value agrees at t = 0."
        ),
        "impact": "High",
        "monitoring": "Front-office value vs XVA-engine value as a daily KPI.",
        "mitigation": "Settlement lag carried on the trade (Payouts.SettlementDays).",
    },
    {
        "description": (
            "Counterparty default is independent of flood in the price (beta = 0); "
            "wrong-way risk is run as a governed stress, not priced."
        ),
        "impact": "High",
        "monitoring": "WWR stress by counterparty type (insurer, lender, utility).",
        "mitigation": "Path-weighted hazard on the shared event draws; priced only after sign-off.",
    },
    {
        "description": (
            "Regulatory capital is SA-CCR plus BA-CVA (reduced), no capital used "
            "for funding (phi = 0), cost of capital shared with MKM-CR-001."
        ),
        "impact": "High",
        "monitoring": "KVA under each regulatory-treatment alternative.",
        "mitigation": "One shared regulatory module for MKM-XV-001 and MKM-CR-001.",
    },
]

LIMITATIONS = [
    {
        "description": (
            "The regulatory characterisation of a PRS (derivative or insurance; "
            "SA-CCR asset class; whether the FRTB residual-risk add-on applies) is "
            "undecided, and KVA depends on all three answers."
        ),
        "impact": "High",
        "monitoring_trigger": "Before any KVA figure is used in a price.",
        "compensating_control": "Question paper raised for an owner outside the model team.",
    },
    {
        "description": (
            "Counterparty credit, own funding spread and CSA terms are synthetic "
            "on the platform today; no real input or lineage exists."
        ),
        "impact": "High",
        "monitoring_trigger": "Before production sign-off.",
        "compensating_control": "Outputs carry an ILLUSTRATIVE status until real inputs land.",
    },
    {
        "description": (
            "Triggers are rare, so exposure cannot be meaningfully backtested; "
            "outcomes analysis rests on MKM-EF-001 hazard backtests and ΔXVA P&L explain."
        ),
        "impact": "Medium",
        "monitoring_trigger": "Annual review.",
        "compensating_control": "Closed-form benchmark and limiting-case tests.",
    },
    {
        "description": (
            "Property PRS has no term pricer (its spread is an undiscounted "
            "exceedance probability), so XVA is limited to gauge PRS until one exists."
        ),
        "impact": "Medium",
        "monitoring_trigger": "Any request for XVA on Property PRS.",
        "compensating_control": "Scope restricted to TradeType 'PRS'.",
    },
]

WEAKNESSES = [
    "Variation margin does not remove the jump to notional at the trigger; only "
    "initial margin or prefunding does, so a CSA'd trade keeps material CVA.",
    "Monte Carlo error on the jump term is the largest of any component at "
    "10,000 paths, because only paths with a trigger contribute to it.",
    "Inherited from MKM-PR-001: the trade records a 6M premium frequency but the "
    "pricer prices quarterly, and remaining tenor is rounded to whole years.",
]

# Chain edges, producer -> consumer. MKM-XV-001 consumes the PRS value
# (MKM-PR-001) and the event draws (MKM-EF-001), and feeds the Trading Desk
# (MKM-TD-001), which shows XVA on the blotter and in EOD P&L.
CHAIN_EDGES = [
    ("MKM-PR-001", MODEL_ID),
    ("MKM-EF-001", MODEL_ID),
    (MODEL_ID, "MKM-TD-001"),
]
