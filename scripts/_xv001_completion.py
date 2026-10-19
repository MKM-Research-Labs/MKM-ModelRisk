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

"""Record content that closes MKM-XV-001's completeness-audit gaps.

Split from ``complete_xv001_governance`` as ``_xv001_data`` is from
``register_xv001``. Every entry is backed by evidence in PhysicalRisk:
``docs/xva/project_plan.md`` (sections 15-16), ``docs/xva/validation_evidence.json``
and the model document. Nothing here claims work that has not been done: the
model has not been independently validated, so the validation and sign-off
dates, the sign-off history and the peer reviewer are deliberately absent.
"""
from __future__ import annotations

# --- Scalar fields: written only while blank --------------------------------
DESCRIPTION = (
    "The PRS XVA Model computes the valuation adjustments on gauge Parametric Risk "
    "Swaps: CVA and FVA (booked), DVA (disclosed) and KVA (memo). It overlays the PRS "
    "pricer (MKM-PR-001), reproducing its risk-free value at t = 0, and runs a "
    "10,000-path Monte Carlo per netting set with a CIR++ catchment hazard factor "
    "fitted to the desk's hazard term structure, close-out netting, collateral and "
    "a wrong-way-risk stress. It runs on the whole book in port, on each PRS trade "
    "commit and at EOD, and feeds the Trading Desk blotter and XVA P&L (MKM-TD-001)."
)

SCALARS = {
    "description": DESCRIPTION,
    "materiality_rationale": (
        "High: once booked, the adjustment changes the client price, fair value and "
        "daily P&L of every gauge PRS. On the 50-trade Thames book XVA is -43k and "
        "KVA -2.0m; KVA alone is about 43bp of running spread on a 204bp trade."
    ),
    "complexity_rationale": (
        "High: a stochastic-hazard Monte Carlo over netting sets with jump-to-notional "
        "exposure, collateral with a margin period of risk, wrong-way risk, and SA-CCR "
        "and BA-CVA capital recomputed in every simulated state."
    ),
    "vendor": "In-house",
    # Annual review, a year after the model was built and submitted.
    "next_review_date": "2027-10-09",
}

# The registered version predates WP6; the filed model document is v0.10.
VERSION_FROM, VERSION_TO = "0.9.0", "0.10.0"

VERSIONS = [
    {"version": "0.9.0", "date": "2026-10-09", "author": "David K Kelly",
     "lifecycle": "New", "ref_document": "MKM-XV-001_model_document.pdf",
     "description": "WP0-WP5: analytic engine, Monte Carlo, capital and KVA, Trading "
                    "Desk integration, model document; submitted for validation."},
    {"version": "0.10.0", "date": "2026-10-12", "author": "David K Kelly",
     "lifecycle": "Being Enhanced", "ref_document": "MKM-XV-001_model_document.pdf",
     "description": "WP6: CIR++ fitted to the desk's hazard term structure; valuation "
                    "KPI breaches on the test book fall from 18/20 to 4/20."},
]

CHANGES = [
    {"version": "0.10.0", "date": "2026-10-14", "author": "David K Kelly",
     "description": "Counterparty CDS curves carried on the counterparty record and "
                    "used for the default curve; XVA now runs in port and on each "
                    "PRS trade commit as well as at EOD."},
]

DATA_SOURCES = [
    {"data_source": "MKM-PR-001 PRS pricer: trade terms, discount curve and risk-free value",
     "note": "Reproduced at t = 0 to 1e-12 (pricer reconciliation check)."},
    {"data_source": "Trading Desk market state: gauge hazard term structure",
     "note": "Tenor-bucket hazards bootstrapped into the CIR++ shift; six gauges with "
             "no term structure fall back to a flat curve and are listed in the run."},
    {"data_source": "Counterparty records: CDS curve, recovery and rating",
     "note": "Synthetic. Generated counterparties carry a rating-proxy curve, flagged "
             "RatingProxy on every output."},
    {"data_source": "Counterparty CDM: netting agreements and CSA terms",
     "note": "Synthetic; counterparties without CreditSupport run uncollateralised."},
    {"data_source": "config/xva.py: funding spread, hazard volatility, capital parameters",
     "note": "Placeholders: hazard volatility 0.30 and mean reversion 0.5 are not "
             "calibrated; funding spread has no treasury source."},
    {"data_source": "MKM-EF-001 event catalogue (trigger correlation)",
     "note": "Supported by the engine but not yet passed in by the desk, so triggers "
             "are independent given the hazard factor."},
]

EVALUATIONS = [
    {"kind": "Benchmark against a baseline", "performed_on": "2026-10-09",
     "dataset": "Single-trade cases: flat and humped hazard, bank buying and selling",
     "metric": "Agreement with an independent re-implementation sharing no engine code",
     "result": "CVA and FVA agree to 1e-8 in every case.", "passed": "Passed"},
    {"kind": "Benchmark against a baseline", "performed_on": "2026-10-09",
     "dataset": "BCBS 279 Annex 4a worked examples 2 and 3",
     "metric": "SA-CCR EAD against the printed figures",
     "result": "EAD 381.2 against 381 and 5,405.6 against 5,406.", "passed": "Passed"},
    {"kind": "Benchmark against a baseline", "performed_on": "2026-10-09",
     "dataset": "Monte Carlo against the closed form, 10,000 paths",
     "metric": "z-score of each XVA term against its analytic value",
     "result": "Largest |z| 1.56, inside the 3-standard-error gate.", "passed": "Passed"},
    {"kind": "Reproducibility check", "performed_on": "2026-10-12",
     "dataset": "20-trade gauge book on the local test portfolio, 10,000 paths",
     "metric": "Engine value against front-office MTM (KPI: 5bp of notional)",
     "result": "With the term-structure fit 4 of 20 trades breach (median gap 0.05bp); "
               "all four are F-4, whole-year tenor rounding in MKM-TD-001.",
     "passed": "Passed with caveats"},
]

RACI_ROLES = [
    {"role": "Model owner", "raci": "Accountable", "assigned_to": "David K Kelly",
     "description": "Owns the record, the limitations register and remediation."},
    {"role": "Model developer", "raci": "Responsible", "assigned_to": "David K Kelly",
     "description": "Builds and maintains src/models/xva and its tests."},
    {"role": "Independent validator", "raci": "Responsible",
     "description": "Unassigned: independent validation (VQ-009) is outstanding."},
    {"role": "Model Risk Committee", "raci": "Consulted",
     "description": "Signs off validation and the regulatory treatment of KVA."},
    {"role": "Trading Desk", "raci": "Informed",
     "description": "Consumes XVA and KVA on the blotter and in EOD P&L."},
]

FAIRNESS = [
    {"attribute": "Not applicable: counterparties are institutions and the output "
                  "prices credit and funding risk, not decisions about individuals.",
     "how_assessed": "Scope review of the model's inputs and outputs.",
     "assessed_on": "2026-10-19"},
]

# Validation questions, first-line assessment against the evidence. Data quality
# and independent validation stay Not Addressed: the inputs are synthetic and no
# independent review has run.
VQ_UPDATES = {
    "VQ-001": ("Partially Addressed",
        "It reproduces the PRS pricer's value at t = 0 to 1e-12 and computes CVA, FVA "
        "and KVA as specified in the model document, but on synthetic counterparty, "
        "funding and CSA inputs, so it is not yet fit to price real trades."),
    "VQ-002": ("Partially Addressed",
        "Numerically accurate and stable: an independent re-implementation agrees to "
        "1e-8, the Monte Carlo is within 3 standard errors of the closed form, and runs "
        "are seeded. Real-world accuracy rests on placeholder hazard volatility and "
        "funding spread, and four test-book trades still breach the KPI (F-4)."),
    "VQ-003": ("Addressed",
        "A 10,000-path run of a 20-trade book took 11s; port and EOD run the book "
        "once, and a trade commit reruns only that counterparty's netting set."),
    "VQ-004": ("Addressed",
        "Every parameter is in config/xva.py (rule R1) with no per-run overrides; the "
        "port and trade-commit runs are config switches, and KPI breaches are reported, "
        "never auto-corrected."),
    "VQ-006": ("Addressed",
        "Six assumptions are on the record with their rationale and impact, and the "
        "decisions behind them (D-01 to D-17) are logged in the model document."),
    "VQ-007": ("Addressed",
        "Six limitations are recorded, each with a monitoring trigger and a "
        "compensating control; the daily valuation KPI and EOD XVA P&L monitor them."),
    "VQ-008": ("Partially Addressed",
        "Benchmarked against an independent re-implementation and the Basel SA-CCR "
        "worked examples. No external or vendor XVA engine has been compared."),
}

# Document categories the model document evidences, beyond those filed at
# registration. Monitoring and Segment analysis are not covered and stay open.
EXTRA_DOCS = [
    ("Analysis", "analysis.pdf", "Results and sensitivity analysis - PRS XVA Model"),
    ("Convergence", "convergence.pdf", "Monte Carlo against the closed form - PRS XVA Model"),
    ("Calibration", "calibration.pdf",
     "CIR++ fit to the hazard term structure - PRS XVA Model (hazard volatility uncalibrated)"),
]
