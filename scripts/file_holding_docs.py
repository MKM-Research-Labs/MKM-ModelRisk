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

from scripts._holding_content import build_monitoring_md, build_remediation_md
from src.governance.completeness import findings, scan
from src.governance.documents import add_document
from src.governance.latex import front_matter, history_page, logo_asset, preamble
from src.governance.model_inventory import get_model, rebuild_inventory_view
from src.governance.model_inventory.commands import AGGREGATE_TYPE as MODEL_AGGREGATE
from src.governance.mrc.pack import TectonicNotFound, compile_tex
from src.governance.mrc_settings import get_settings

ACTOR = "file_holding_docs"


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
