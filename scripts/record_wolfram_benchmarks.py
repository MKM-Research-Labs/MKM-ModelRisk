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

"""Record each model's Wolfram benchmark on its record; re-issue PR-001's document.

Both benchmarks are filed (scripts.attach_wolfram_benchmark). This records what
they established:

* ``benchmark_tests = Yes`` on each benchmarked model;
* validation question VQ-008 (Benchmarking) at Partially Addressed, with a
  rationale that cites the benchmark and says what is still outstanding. On
  GH-001 it replaces a status that read Addressed over a rationale saying no
  benchmark existed;
* model documentation re-issued where a benchmark found it wrong (``REISSUES``):
  PR-001 as v3.1 and DE-001 as v1.1, each the latest source recovered from
  PhysicalRisk and corrected against its benchmark. The PDF and its .tex are
  filed as Core Documentation, and the superseded document moves to History: a
  metadata change, so it keeps its id and file.

Idempotent: a field already at its value, a question already at its status and
rationale, a document already filed, and a document already in History are left
alone.

Run as:  python -m scripts.record_wolfram_benchmarks
"""
from __future__ import annotations

from pathlib import Path

from config.governance._documents import HISTORY_DOC_CATEGORY
from config.paths import MODEL_DOCS_DIR
from src.governance.documents import add_document, update_document
from src.governance.model_inventory import (
    get_model,
    rebuild_inventory_view,
    update_collection_item,
    update_model_field,
)
from src.governance.model_inventory.commands import AGGREGATE_TYPE as MODEL_AGGREGATE

ACTOR = "record_wolfram_benchmarks"
CORE_DOC_CATEGORY = "Core Documentation"
BENCHMARK_FIELD, BENCHMARK_VALUE = "benchmark_tests", "Yes"
VQ_BENCHMARKING = "VQ-008"
VQ_STATUS = "Partially Addressed"

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
        "Partially addressed. The frequency model was benchmarked on 2026-10-26 against "
        "Wolfram Engine 15.0 and a 50-digit mpmath implementation of model document v2.3 "
        "(MKM-EF-001_wolfram_benchmark.pdf, Docs > Benchmark): over 161 cases the annual "
        "probability, tenor probability, compound-Poisson AAL and its standard error, the "
        "dispersion test and both families' log-likelihoods match to better than 1e-12, "
        "Wolfram agrees with the reference to 5e-30, and the Negative Binomial fit "
        "reaches the likelihood maximum. It found that the hazard builder's term "
        "structure compounds annual probabilities as intensities, understating the "
        "probability of a flood within the tenor by 0.1-17.3%, and that annualisation "
        "loses about 1e-10 relative precision below lambda*p = 1e-4. Outstanding: the "
        "calibration of lambda from gauge records, which the document leaves open, and "
        "the Monte Carlo year simulation's draws, which only its reconciliation gate checks."),
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
}


def _record_benchmark(model_id: str, data: dict, config) -> list[str]:
    done = []
    if data.get(BENCHMARK_FIELD) != BENCHMARK_VALUE:
        update_model_field(model_id=model_id, field=BENCHMARK_FIELD, value=BENCHMARK_VALUE,
                           actor=ACTOR, config=config,
                           reason="Wolfram oracle benchmark filed (Docs > Benchmark)")
        done.append(BENCHMARK_FIELD)
    rationale = VQ_RATIONALE[model_id]
    q = next((q for q in data.get("validation_questions") or []
              if q.get("item_id") == VQ_BENCHMARKING), None)
    if q is None:
        raise RuntimeError(f"{model_id} has no {VQ_BENCHMARKING} validation question.")
    if q.get("status") != VQ_STATUS or q.get("rationale") != rationale:
        update_collection_item(
            model_id=model_id, collection="validation_questions", item_id=VQ_BENCHMARKING,
            fields={"status": VQ_STATUS, "rationale": rationale}, actor=ACTOR,
            config=config, reason="Benchmarking assessed against the Wolfram benchmark")
        done.append(VQ_BENCHMARKING)
    return done


def _reissue(model_id: str, data: dict, docs_dir: Path, config) -> list[str]:
    spec, done = REISSUES[model_id], []
    documents = data.get("documents") or []
    have = {d.get("original_name") or d.get("filename") for d in documents}
    for name, description in spec["files"]:
        if name in have:
            continue
        add_document(
            aggregate_type=MODEL_AGGREGATE, aggregate_id=model_id,
            scope=f"model/{model_id}", category=CORE_DOC_CATEGORY, filename=name,
            data=(docs_dir / model_id / name).read_bytes(), description=description,
            actor=ACTOR, config=config)
        done.append(name)
    for d in documents:
        if (d.get("original_name") == spec["superseded"]
                and d.get("category") == CORE_DOC_CATEGORY):
            update_document(
                aggregate_type=MODEL_AGGREGATE, aggregate_id=model_id,
                item_id=d["item_id"], fields={"category": HISTORY_DOC_CATEGORY},
                actor=ACTOR, config=config,
                reason=f"Superseded by model documentation {spec['version']}")
            done.append(f"{spec['superseded']} -> {HISTORY_DOC_CATEGORY}")
    return done


def apply(docs_dir: Path = MODEL_DOCS_DIR, config=None) -> dict:
    """Record every benchmark and re-issue the documents; return what changed.

    Every model and file is checked before anything is written.
    """
    models = {m: get_model(m, config=config) for m in VQ_RATIONALE}
    absent = [m for m, rec in models.items() if rec is None]
    if absent:
        raise RuntimeError(f"Not registered: {', '.join(absent)}.")
    missing = [f"{m}/{n}" for m, spec in REISSUES.items() for n, _ in spec["files"]
               if not (docs_dir / m / n).is_file()]
    if missing:
        raise FileNotFoundError(f"Not found under {docs_dir}: {', '.join(missing)}")

    changed = {m: _record_benchmark(m, rec["data"], config) for m, rec in models.items()}
    for model_id in REISSUES:
        changed[model_id] += _reissue(model_id, models[model_id]["data"], docs_dir, config)
    rebuild_inventory_view(config=config)
    return changed


def main() -> int:
    from config.database import DatabaseConfig
    from src.database import run_migrations

    print(f"Database: {DatabaseConfig.from_env().name}")
    run_migrations()
    for model_id, done in apply().items():
        print(f"  {model_id}: {', '.join(done) if done else 'nothing to do'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
