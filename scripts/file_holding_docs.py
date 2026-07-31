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

"""File interim *holding* documents for the Monitoring and Remediation-Evidence gaps.

Every model is missing a Monitoring document and many are missing a Remediation
Evidence document. Neither can honestly be filled with results yet — no monitoring
cycle has run and no remediation evidence has been collected. What *can* be put on
record is the **approach**: how the model will be monitored, and what *type* of
evidence would close each open finding.

This files two clearly-labelled interim holding documents, tailored per model from
its live record (name, description and its actually-open validation questions):

* **Monitoring** — the ongoing-monitoring approach. States explicitly that it
  contains no results and will be replaced once the first cycle runs.
* **Remediation Evidence** — the evidence framework: for each open finding, the
  type of evidence and the acceptance standard that would close it. States
  explicitly that it contains no evidence, only the standard.

Both are rendered through the platform's own house-style LaTeX toolchain
(``pandoc`` fragment -> shared preamble/front-matter -> ``tectonic``), so they
match every other document, and are filed into the matching per-model category.

Nothing here fabricates a result or a piece of evidence: these are plan/framework
documents, and they say so on their title page and in their status banner.

Idempotent: a document already attached (by stored name) is skipped.

Run as:  python -m scripts.file_holding_docs
"""
from __future__ import annotations

import shutil
import subprocess
from datetime import date

from src.governance.completeness import findings, scan
from src.governance.documents import add_document
from src.governance.latex import front_matter, history_page, logo_asset, preamble
from src.governance.model_inventory import get_model, rebuild_inventory_view
from src.governance.model_inventory.commands import AGGREGATE_TYPE as MODEL_AGGREGATE
from src.governance.mrc.pack import TectonicNotFound, compile_tex
from src.governance.mrc_settings import get_settings

ACTOR = "file_holding_docs"

# Which open findings map to which kind of remediation evidence. Keyed by the
# validation-question item_id; only the questions genuinely open on a given model
# produce a section, so each document lists that model's real outstanding items.
_EVIDENCE = {
    "VQ-002": ("Accuracy and stability",
        "Back-testing of the model's outputs against observed outcomes over a "
        "representative period, with error statistics and a stability check across "
        "re-runs and parameter perturbations."),
    "VQ-004": ("Override controls",
        "A documented, governed override procedure: the permitted overrides, who "
        "may authorise them, and a log showing each override with its "
        "justification and sign-off."),
    "VQ-005": ("Data quality",
        "Real observation records replacing the synthetic inputs, together with a "
        "data-quality assessment (completeness, accuracy, timeliness and source "
        "lineage) demonstrating the inputs are fit for purpose."),
    "VQ-008": ("Benchmarking",
        "A documented comparison against a named, credible independent "
        "alternative, with error metrics and a reconciliation explaining material "
        "differences."),
    "VQ-009": ("Independent validation",
        "A report from a reviewer independent of the model build who has "
        "replicated the results and issued a validation opinion, with any "
        "conditions or findings recorded."),
}

_OPEN = {"Not Addressed", "Partially Addressed"}


def _open_questions(data: dict) -> list[dict]:
    """The model's validation questions that are not fully Addressed."""
    return [q for q in (data.get("validation_questions") or [])
            if q.get("status") in _OPEN]


def build_monitoring_md(data: dict) -> str:
    """Markdown for the interim monitoring-approach holding document."""
    name = data.get("name", "")
    desc = data.get("description", "").strip()
    return f"""**Status: interim holding document.** This document sets out the
ongoing-monitoring approach for {name}. It has been produced ahead of the first
monitoring cycle, so it contains **no monitoring results** — only the design. It
is replaced by a monitoring result once the first cycle runs and produces dated
metrics.

# Scope

{desc}

# What is monitored

Monitoring tracks the model's material inputs and outputs and the limitation
triggers already recorded in its Limitations register. Where a sensitivity
analysis exists for the model, the quantities it identifies as most material are
the primary monitoring targets, because those are where drift moves the priced
result fastest.

# Metrics and thresholds

The following are tracked each cycle (thresholds are fixed at the first
calibration review and are not yet set):

- **Output stability** — drift in the model's headline output against the prior
  cycle and against the value at validation.
- **Input drift** — movement in the distribution of the model's key inputs
  relative to the calibration sample.
- **Exception rate** — the frequency of inputs falling outside the model's
  documented applicability range.

# Cadence

Periodic review (proposed: quarterly) plus an event-driven review triggered by a
material hazard event or a change in an upstream model this one depends on.

# Escalation and ownership

A threshold breach re-rates the model's RAG status and is escalated to the Model
Risk Committee, which decides whether recalibration, restriction or
re-validation is required. The model owner runs each cycle and records the
result.

# Exit from interim status

This holding document is superseded when the first monitoring cycle completes and
a dated monitoring result is filed in its place.
"""


def build_remediation_md(data: dict) -> str:
    """Markdown for the interim remediation-evidence framework holding document."""
    name = data.get("name", "")
    open_qs = _open_questions(data)
    if open_qs:
        lines = "\n".join(
            f"- **{q.get('short_label') or q.get('item_id')}** "
            f"({q.get('item_id')}) — currently {q.get('status')}."
            for q in open_qs)
    else:
        lines = "- No open validation questions are recorded for this model."

    sections = ""
    for q in open_qs:
        entry = _EVIDENCE.get(q.get("item_id"))
        if entry is None:
            continue
        heading, text = entry
        sections += f"\n## {heading} ({q.get('item_id')})\n\n{text}\n"
    if not sections:
        sections = ("\n## General\n\nEvidence appropriate to each open finding "
                    "as it is identified.\n")

    return f"""**Status: interim holding document.** This document describes the
*type* of evidence that would close each open finding on {name}. No remediation
evidence has yet been collected — it contains **no evidence**, only the standard
each item must meet. It is replaced, finding by finding, as real evidence is
produced.

# Open findings for this model

{lines}

# Appropriate evidence by finding
{sections}
# Acceptance criteria

To close a finding, the evidence must be dated, attributable to a named author,
reproducible from the inputs stated, and reviewed by someone independent of the
model build. Evidence that only restates the model's own construction does not
close a finding.
"""


def _render(title: str, subtitle: str, body_md: str, settings: dict) -> bytes:
    """Render markdown to PDF bytes in the shared house style (pandoc -> tectonic)."""
    if shutil.which("pandoc") is None:
        raise RuntimeError("pandoc is not installed; cannot render holding documents.")
    body = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "latex"],
        input=body_md, check=True, capture_output=True, text=True).stdout
    org = settings.get("fields", {}).get("org_name", "")
    assets = logo_asset(settings)
    as_of = date.today().isoformat()
    tex = (
        preamble(title, org_name=org)
        + "\\providecommand{\\tightlist}{\\setlength{\\itemsep}{0pt}\\setlength{\\parskip}{0pt}}\n"
        + "\\begin{document}\n"
        + front_matter(title, subtitle, org_name=org, date=as_of,
                       logo=bool(assets), toc=True)
        + body
        + "\\clearpage\n"
        + history_page(as_of, "Interim holding document generated ahead of "
                              "results / evidence", org_name=org)
        + "\\end{document}\n"
    )
    return compile_tex(tex, assets)


# (category, stored name, subtitle, builder) per holding-document kind.
_KINDS = {
    "monitoring": ("Monitoring", "monitoring.pdf",
                   "Ongoing Monitoring Approach (interim)", build_monitoring_md),
    "remediation": ("Remediation Evidence", "remediation_evidence.pdf",
                    "Remediation Evidence Framework (interim)", build_remediation_md),
}


def _targets(as_of: str, config=None):
    """Model ids that the live audit flags as missing each holding document."""
    gaps = findings(scan(as_of, config=config))
    mon, rem = [], []
    for g in gaps:
        if g.get("kind") != "document" or g.get("entity_kind") != "Model":
            continue
        if g.get("label") == "Monitoring":
            mon.append(g["entity_id"])
        elif g.get("label") == "Remediation Evidence":
            rem.append(g["entity_id"])
    return mon, rem


def file_one(model_id: str, kind: str, settings: dict, render=_render, config=None) -> bool:
    """File one holding document for one model; return True if newly filed."""
    category, stored_name, subtitle, builder = _KINDS[kind]
    model = get_model(model_id, config=config)
    if model is None:
        raise RuntimeError(f"{model_id} is not registered.")
    data = model["data"]
    have = {(d.get("original_name") or d.get("filename"))
            for d in (data.get("documents") or [])}
    if stored_name in have:
        return False
    title = f"{data.get('name', model_id)} — {subtitle.split(' (')[0]}"
    pdf = render(title, subtitle, builder(data), settings)
    add_document(
        aggregate_type=MODEL_AGGREGATE, aggregate_id=model_id,
        scope=f"model/{model_id}", category=category, filename=stored_name,
        data=pdf, description=f"{subtitle} - {data.get('name', model_id)}",
        actor=ACTOR, config=config)
    return True


def apply(config=None, as_of=None, render=_render,
          monitoring_ids=None, remediation_ids=None) -> dict:
    """File the interim holding documents; return a summary.

    Targets default to whatever the live audit flags; pass explicit id lists to
    scope a run (used by the tests).
    """
    as_of = as_of or date.today().isoformat()
    settings = get_settings()
    if monitoring_ids is None or remediation_ids is None:
        mon, rem = _targets(as_of, config=config)
        monitoring_ids = mon if monitoring_ids is None else monitoring_ids
        remediation_ids = rem if remediation_ids is None else remediation_ids

    summary = {"monitoring": [], "remediation": []}
    for mid in monitoring_ids:
        if file_one(mid, "monitoring", settings, render=render, config=config):
            summary["monitoring"].append(mid)
    for mid in remediation_ids:
        if file_one(mid, "remediation", settings, render=render, config=config):
            summary["remediation"].append(mid)
    rebuild_inventory_view(config=config)
    return summary


def main() -> int:
    from src.database import run_migrations

    run_migrations()
    try:
        s = apply()
    except TectonicNotFound as exc:
        print(f"Cannot render holding documents: {exc}")
        return 1
    print(f"Filed {len(s['monitoring'])} Monitoring and {len(s['remediation'])} "
          "Remediation Evidence holding documents.")
    if s["monitoring"]:
        print("  Monitoring:", ", ".join(s["monitoring"]))
    if s["remediation"]:
        print("  Remediation Evidence:", ", ".join(s["remediation"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
