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

"""What each Wolfram benchmark established, and the documents it re-issued.

The data half of ``record_wolfram_benchmarks``, split from it as ``_xv001_data``
is from ``register_xv001``: one VQ-008 rationale per benchmarked model, and the
model documentation re-issued where a benchmark found it wrong.
"""
from __future__ import annotations

VQ_RATIONALE = {
    "MKM-GH-001": (
        "Partially addressed. The implementation was benchmarked on 2026-10-19 against "
        "Wolfram Engine 15.0 and a 50-digit mpmath reference (MKM-GH-001_wolfram_benchmark"
        ".pdf, Docs > Benchmark): return levels and exceedance probabilities agree with "
        "Wolfram to 4.2e-10 for return periods up to 10,000 years, and Wolfram and the "
        "reference agree to 5e-30. The maximum-likelihood fit reaches the likelihood "
        "maximum (gain at most 2.1e-6), confirmed by Wolfram's EstimatedDistribution. "
        "Outstanding: the fit was benchmarked on synthetic samples, not the real gauge "
        "record, and the model has not been benchmarked against an alternative method "
        "(e.g. L-moments estimation or a peaks-over-threshold GPD)."),
    "MKM-PR-001": (
        "Partially addressed. The analytical pricing path was benchmarked on 2026-10-19 "
        "against Wolfram Engine 15.0 and a 50-digit mpmath implementation of the "
        "documented formula (MKM-PR-001_wolfram_benchmark.pdf, Docs > Benchmark): over "
        "160 cases the model matches the formula to 2.4e-15 and Wolfram agrees with the "
        "reference to 4e-30; the floor, zero rule, cap and curve interpolation behave as "
        "documented. It found the documentation understated quarterly discretisation "
        "(s8.3) and the effect of the book's yield curve (s8.4); both are corrected in "
        "model documentation v3.1. Outstanding: no benchmark against an alternative "
        "pricing method (e.g. ISDA-standard pricing with accrued premium on trigger)."),
    "MKM-SI-001": (
        "Partially addressed. The implementation was benchmarked on 2026-10-20 against "
        "Wolfram Engine 15.0 and a 50-digit mpmath implementation of the model document "
        "(MKM-SI-001_wolfram_benchmark.pdf, Docs > Benchmark): exceedance and return-"
        "period intensities match the documented formulae to about 1e-15 and the "
        "quantile to 3.8e-9 (Acklam's inverse normal); Wolfram agrees with the reference "
        "to 5e-30. It found that the Imax clamp puts 1.0% (historical) to 29.7% "
        "(extreme) of storms exactly on the cap, so return-period intensities saturate, "
        "and that IntensityDistribution is not used by the production storm generator. "
        "Outstanding: no benchmark against an alternative method or observed storm data, "
        "and the calibration the document describes (MLE body, Hill tail) has no code."),
    "MKM-DE-001": (
        "Partially addressed. The delta engine was benchmarked on 2026-10-26 against "
        "Wolfram Engine 15.0 and a 50-digit mpmath implementation of its documented "
        "formulae (MKM-DE-001_wolfram_benchmark_v0.2.pdf, Docs > Benchmark): over 120 "
        "cases the risky annuity matches to 6e-16 and FS01, the spread change, the "
        "annuity, MTM and the hazard sensitivity to within their rounding; Wolfram agrees "
        "with the reference to 5e-25 and the 1 bp bump is within 3e-4 bp of the exact "
        "gradient. Benchmark v0.1 found MTM off by up to GBP 3.40 on GBP 10m and FS01 "
        "silent on the 2 bp spread floor; both are fixed, and the three documentation "
        "errors it found are corrected in model documentation v1.1, whose claims all "
        "hold. Outstanding: no benchmark against an alternative risk measure (e.g. "
        "full-revaluation sensitivities across the book)."),
    "MKM-EF-001": (
        "Partially addressed. The frequency model was benchmarked on 2026-10-27 against "
        "Wolfram Engine 15.0 and a 50-digit mpmath implementation of model document v2.4 "
        "(MKM-EF-001_wolfram_benchmark_v0.2.pdf, Docs > Benchmark): over 161 cases the "
        "annual probability, tenor probability and term structure, compound-Poisson AAL "
        "and its standard error, the dispersion test and both families' log-likelihoods "
        "match to better than 1e-12, Wolfram agrees with the reference to 5e-30, and the "
        "Negative Binomial fit reaches the likelihood maximum. Benchmark v0.1 found the "
        "term structure compounding annual probabilities as intensities (understating "
        "the tenor probability by 0.1-17.3%) and 1 - exp(-x) losing precision at small "
        "lambda*p; both are fixed, and model documentation v2.4 specifies them. "
        "Outstanding: the calibration of lambda from gauge records, which the document "
        "leaves open, and the Monte Carlo year simulation's draws, which only its "
        "reconciliation gate checks."),
    "MKM-MP-001": (
        "Partially addressed. The pricer was benchmarked on 2026-10-27 against Wolfram "
        "Engine 15.0 and a 50-digit mpmath implementation of its documented formulae "
        "(MKM-MP-001_wolfram_benchmark_v0.2.pdf, Docs > Benchmark): over 360 loans the "
        "payment, spread, expected cashflows, expected losses and fair value match Eqs. "
        "1-24 to 6e-14, and the fair value equals Wolfram's independent pathwise "
        "valuation (agreement 3e-30). Benchmark v0.1 found the fair value counting "
        "expected loss twice (understated by up to 34.6% of par) and the recovery taken "
        "a month late; both are fixed, and the documentation errors it found are "
        "corrected in model documentation v1.3, whose claims all hold. Outstanding: no "
        "benchmark against an alternative credit model or observed default and "
        "recovery data."),
    "MKM-FIRE-001": (
        "Partially addressed. The credit was benchmarked on 2026-10-27 against Wolfram "
        "Engine 15.0 and a 50-digit mpmath implementation of model document v0.40 "
        "(MKM-FIRE-001_wolfram_benchmark.pdf, Docs > Benchmark), which computes the "
        "containment rate, loss frequency and fire spread exactly rather than by Monte "
        "Carlo. Model C matches its documented formulae to 2e-16 over 90 assets; the code "
        "reproduces all 212 figures in the document's Tables 1-12 at the generator's seed, "
        "each within 2.54 standard errors of the exact credit; Wolfram agrees with the "
        "reference to 4e-31. Findings: the production spread (1,000 draws) has a 44 bp "
        "standard error at the reach cliff but is quoted to 0.1 bp; the cliff is 197.5 bp, "
        "not 203; the tall non-combustible residual is 0.003 bp, not single-digit bps; and "
        "three documentation corrections. Outstanding: calibration of every seed parameter "
        "(FIRE-R1) and benchmarking against historical fire-loss data (FIRE-R2)."),
    "MKM-SEIS-001": (
        "Partially addressed. The credit was benchmarked on 2026-10-28 against Wolfram "
        "Engine 15.0 and a 50-digit mpmath implementation of model document v0.10 "
        "(MKM-SEIS-001_wolfram_benchmark.pdf, Docs > Benchmark), which computes the "
        "no-collapse rate, loss frequency and seismic spread exactly by integrating over "
        "the magnitude law. Model C, the GMPE median and the occurrence rate match the "
        "reference to 6e-16; the code reproduces all 131 figures in the document's "
        "Tables 3-10 at the generator's seed, each within 1.94 standard errors of the "
        "exact credit; all six Table 2 gates hold exactly; Wolfram agrees to 5e-31. "
        "Findings: at 20,000 draws a 1 bp spread carries a 70% standard error, so the "
        "stability claim of s9.6 fails; the production spread at 10,000 draws carries up "
        "to 5.6 bp of error; Table 18's mean losses are medians; the GMPE form is "
        "undocumented. Outstanding: calibration (SEIS-R1) and GMPE benchmarking against "
        "an independent model (SEIS-R2)."),
    "MKM-GHD-001": (
        "Partially addressed. The generator was benchmarked on 2026-10-28 against Wolfram "
        "Engine 15.0 and an exact implementation of model document v1.0 "
        "(MKM-GHD-001_wolfram_benchmark.pdf, Docs > Benchmark), which computes the expected "
        "days above each flood threshold, the mean level and the January and July "
        "departures in closed form. Over six gauges and 200 generated 50-year series each, "
        "every statistic is within 2.03 standard errors of its exact expectation; Wolfram "
        "derives the tail integral symbolically and agrees to 4.9e-10. Findings: n3 is a "
        "5-year count spread over 50 years, so severe frequency is understated tenfold; the "
        "hash() seed differs per process and the series ends at the run date, so "
        "regeneration is not reproducible; the alert-day and lag-1 diagnostics of s7.1 "
        "cannot pass as stated; the spring-neap phase restarts each 1 January. "
        "Outstanding: the backtest against NRFA gauge records (s7.4)."),
    "MKM-DD-001": (
        "Partially addressed. The model was benchmarked on 2026-11-03 against Wolfram Engine "
        "15.0 and a 50-digit implementation of model documentation v2.0 "
        "(MKM-DD-001_wolfram_benchmark.pdf v0.2, Docs > Benchmark). The curve, Manning, "
        "slope, travel time, retention, haversine, IDW and correlation agree to 3e-16, the "
        "hydrograph to the millimetre, and the portfolio Monte Carlo mean is 1.82 standard "
        "errors from the exact expected loss; Wolfram agrees to 4e-31. All 15 of the "
        "document's claims hold, including 70 printed figures. v0.1 found the filed v1.1 "
        "no longer described the model (retention length 2 km against the code's 10 km; "
        "removed equations; wrong Table 9 and curve-shift figures) and is kept in History as "
        "evidence of the check; v2.0 replaces v1.1. "
        "Outstanding: review of the 10 km retention length against observed inundation "
        "(v2.0 Q9) and the empirical curve and velocity validation (s7.1-7.2)."),
    "MKM-FPO-001": (
        "Partially addressed. v1.0 was benchmarked on 2026-11-03 against Wolfram Engine "
        "15.0 (MKM-FPO-001_wolfram_benchmark_v0.1.pdf, kept in History as evidence of the "
        "check). The code computed its formula, but the document's evidence did not hold: "
        "8 of Table 1's 54 cells and none of Table 2 reproduced, P at the severe level ran "
        "0.00 to 0.29 rather than 0.42 to 0.97, and early in a storm P was not monotone in "
        "the level. v2.0 is a new model refitted to all 11 gauges' classifiers, with the "
        "storm hour held at a support envelope where no storm reached the level that "
        "early. Benchmark v0.2 (MKM-FPO-001_wolfram_benchmark.pdf, Docs > Benchmark) "
        "passes all 10 checks; Wolfram agrees to 3e-31. All 11 of the document's claims "
        "hold: 88 of 88 grid cells, the envelope within 0.05 h of every knot, the slope "
        "positive at every whole hour (least 0.0057), and all 11 held-out rows. "
        "Outstanding: near severe the model differs from the gauges' classifiers by "
        "0.041-0.066 on average, bias -0.034 to +0.025, and it has not been compared with "
        "observed floods."),
    "MKM-SG-001": (
        "Partially addressed. v1.3 was benchmarked on 2026-11-04 against Wolfram Engine 15.0 "
        "(MKM-SG-001_wolfram_benchmark_v0.1.pdf, kept in History as evidence of the check). "
        "The code computed its equations exactly, but 8 of the document's 16 claims did not "
        "hold: the rise was tied to the fall, so a storm needed peak 56 to reach the flood "
        "alert the calibration put at 40 and never reached severe; peak level trailed peak "
        "intensity by 3.5-5 h, not 2; the run stopped at the storm's end; an input was "
        "unread; and nothing in the platform imports the model, though v1.3 said it fed "
        "gaugets/ and the hazard curves. v2.0 gives the rise its own 1-hour constant, runs "
        "the recession, removes the unread input and states that nothing consumes the "
        "output. Benchmark v0.2 (MKM-SG-001_wolfram_benchmark.pdf, Docs > Benchmark) passes "
        "all 8 checks: the response agrees to 4e-14 m over 780 runs and Wolfram to 4.5e-31. "
        "All 16 claims hold, including 169 printed figures and the storm bands 40.9, 68.2 "
        "and 90.7. Outstanding: the parameters are uncalibrated and there is no backtest "
        "against observed hydrographs (v2.0 Q9)."),
    "MKM-SP-001": (
        "Partially addressed. v1.0 was benchmarked on 2026-11-06 against Wolfram Engine 15.0 "
        "(MKM-SP-001_wolfram_benchmark_v0.1.pdf, kept in History as evidence of the check). "
        "The code computed its haversine and IDW exactly, but 10 of the document's 15 claims "
        "did not hold: the spatial index measured degrees of latitude and longitude alike and "
        "named the wrong nearest gauge in 176 of 1000 queries; the correlation was Euclidean "
        "degrees at 111 km a degree, not the equation printed; the coordinate path fixed the "
        "IDW power; nothing returned the nearest gauge; and nothing in the platform calls the "
        "interpolation, the index or the correlation, while the tests, validation and kriging "
        "comparison v1.0 cited do not exist. v2.0 indexes gauges on the unit sphere with a "
        "nearest-gauge lookup, makes the power and threshold configurable, documents the "
        "correlation as computed (as MKM-DD-001 v2.0 does) and states its use and evidence as "
        "they are. Benchmark v0.2 (MKM-SP-001_wolfram_benchmark.pdf, Docs > Benchmark) passes "
        "all 10 checks; Wolfram agrees to 2e-31. All 13 claims hold, including 1000 of 1000 "
        "nearest-gauge queries and the sphere's 0.32% against WGS84. Outstanding: the "
        "interpolation and correlation are unvalidated and unused (v2.0 Q5, Q7)."),
    "MKM-SS-001": (
        "Partially addressed. v2.0 was benchmarked on 2026-11-08 against Wolfram Engine 15.0 "
        "(MKM-SS-001_wolfram_benchmark_v0.1.pdf, kept in History as evidence of the check). "
        "The code replayed exactly, but 11 of the document's 17 claims did not hold: the "
        "duration cap left no room for gaps, so 45.6% of multi-storm sequences had no gap at "
        "all; Table 9's counts, the cap and gap-scaling shares, the 0.70 chance of a stronger "
        "later storm and the per-catchment P_base were not what the code produced; the cited "
        "consumers and command line do not exist; storm_control.json reached the generator "
        "only if applied before import, and the duration table never; and the classifier "
        "summary covers 11 gauges, not 52. v3.0 reserves each gap's minimum before Eq. 6's "
        "cap and shortens gaps towards it (Eq. 8), moves the tables into config so an "
        "override takes effect in either order, takes P_base from each catchment's storm "
        "module, and restates the figures as computed. Benchmark v0.2 "
        "(MKM-SS-001_wolfram_benchmark.pdf, Docs > Benchmark) passes all 8 checks; Wolfram "
        "agrees to 5e-31. All 17 claims hold, including Table 9's 5,225 isolated sequences and "
        "the cap binding on 60.5% of draws. Outstanding: durations are inconsistent with the "
        "window, so both Q6 thresholds are breached at baseline and Tables 1 and 3 need "
        "recalibrating; the classifiers on file were trained on v2.0 sequences (v3.0 Q9)."),
}

# Re-issued model documentation: for each model, the files under
# MODEL_DOCS_DIR/<model>/ filed as Core Documentation, and the superseded document
# retired to History.
REISSUES = {
    "MKM-PR-001": {
        "files": (("prs_pricing_v3.1.pdf", "PRS Pricing Model v3.1 (19-Oct-2026)"),
                  ("prs_pricing_v3.1.tex", "PRS Pricing Model v3.1 (19-Oct-2026) - LaTeX source")),
        "superseded": "prs_pricing.pdf", "version": "v3.1"},
    "MKM-DE-001": {
        "files": (("delta_engine_v1.1.pdf", "Delta Engine Model v1.1 (26-Oct-2026)"),
                  ("delta_engine_v1.1.tex", "Delta Engine Model v1.1 (26-Oct-2026) - LaTeX source")),
        "superseded": "delta_engine.pdf", "version": "v1.1"},
    "MKM-MP-001": {
        "files": (("mortgage_pricer_v1.3.pdf", "Mortgage Pricing Model v1.3 (27-Oct-2026)"),
                  ("mortgage_pricer_v1.3.tex", "Mortgage Pricing Model v1.3 (27-Oct-2026) - LaTeX source")),
        "superseded": "mortgage_pricer.pdf", "version": "v1.3"},
    "MKM-EF-001": {
        "files": (("event_frequency_v2.4.pdf", "Event Frequency Model v2.4 (27-Oct-2026)"),
                  ("event_frequency_v2.4.tex", "Event Frequency Model v2.4 (27-Oct-2026) - LaTeX source")),
        "superseded": "event_frequency.pdf", "version": "v2.4"},
    "MKM-DD-001": {
        "files": (("flood_risk_v2.0.pdf", "Depth-Damage Curve Model v2.0 (03-Nov-2026)"),
                  ("flood_risk_v2.0.tex", "Depth-Damage Curve Model v2.0 (03-Nov-2026) - LaTeX source")),
        "superseded": "flood_risk.pdf", "version": "v2.0"},
    "MKM-FPO-001": {
        "files": (("flood_poly_v2.0.pdf", "Flood Polynomial Model v2.0 (03-Nov-2026)"),
                  ("flood_poly_v2.0.tex", "Flood Polynomial Model v2.0 (03-Nov-2026) - LaTeX source")),
        "superseded": "flood_poly.pdf", "version": "v2.0"},
    "MKM-SG-001": {
        "files": (("storm_gauge_v2.0.pdf", "Storm-Gauge Forward Model v2.0 (04-Nov-2026)"),
                  ("storm_gauge_v2.0.tex", "Storm-Gauge Forward Model v2.0 (04-Nov-2026) - LaTeX source")),
        "superseded": "storm_gauge.pdf", "version": "v2.0"},
    "MKM-SP-001": {
        "files": (("spatial_model_v2.0.pdf", "Spatial Interpolation Model v2.0 (06-Nov-2026)"),
                  ("spatial_model_v2.0.tex", "Spatial Interpolation Model v2.0 (06-Nov-2026) - LaTeX source")),
        "superseded": "spatial_model.pdf", "version": "v2.0"},
    "MKM-SS-001": {
        "files": (("storm_multi_v3.0.pdf", "Storm Sequence Generator v3.0 (08-Nov-2026)"),
                  ("storm_multi_v3.0.tex", "Storm Sequence Generator v3.0 (08-Nov-2026) - LaTeX source")),
        "superseded": "storm_multi.pdf", "version": "v3.0"},
}
