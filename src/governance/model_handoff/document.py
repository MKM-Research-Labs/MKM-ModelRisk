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
"""Model Interoperability Validation document for one handoff (LaTeX -> PDF).

Renders the provider->consumer handover as the interoperability-validation report:
the sections ModelRisk captures (the two models, the field lineage as
provider->consumer pairs, the compatibility note, the MRC sign-off) are filled from
the handoff; the remaining narrative sections are laid out with the template's
expected content as guidance, ready for a practitioner to complete.
"""
from __future__ import annotations

from typing import Any

from src.governance.latex import (
    _esc, _section, _table, front_matter, history_page, logo_asset, preamble,
)
from src.governance.mrc.pack import compile_tex

# The template's narrative sections and the content each expects. Kept here so the
# generated document mirrors the interoperability template's structure even where
# ModelRisk does not yet hold the narrative — those render as guidance to complete.
_GUIDANCE: list[tuple[str, list[str]]] = [
    ("History", [
        "Previous versions of the handover — is this a replacement or enhancement?",
        "Evolution of scope, assumptions and system implementations",
        "Evolution of the consumer's optionality to use the provider's output",
    ]),
    ("Handover Controls and Usage", [
        "Service agreement between provider and consumer",
        "Production change, error and issue logging",
        "Monitoring of the consumer's usage for appropriateness by the provider",
        "Disaggregation of risk data by the consumer",
    ]),
    ("Distribution Comparison", [
        "Comparison of assumptions between provider and consumer",
        "Comparison of granularity (e.g. time buckets)",
        "Comparability of numerical methods / algorithms — are they compatible?",
        "Evidence a weaker model feeds a more sophisticated one",
    ]),
    ("Stress Testing", [
        "Compatibility of scenario assumptions between provider and consumer",
        "Capability to revalue assets within defined macro-economic scenarios",
        "Risk information lost during aggregation",
        "Whether provider inaccuracies get amplified by the consumer",
    ]),
    ("Limitations and Caveats", [
        "Limitations of use by the consumer",
        "Monitoring approach where manual overrides are used",
    ]),
    ("Model Risk Assessment", [
        "Measurement and prioritisation of residual risk",
        "Evidence of challenge, pushback and agreed actions from both model owners",
        "Impact on business decision-making --- HIGH / MEDIUM / LOW",
        "Assessment of handover --- HIGH / MEDIUM / LOW",
        "Appropriateness of model use by the consumer --- HIGH / MEDIUM / LOW",
    ]),
]


def _guidance(prompts: list[str]) -> str:
    items = "".join("\\item " + _esc(p) + "\n" for p in prompts)
    return ("\\textit{\\textcolor{gray}{To be completed:}}\n"
            "\\begin{itemize}\n" + items + "\\end{itemize}\n")


def _model_line(role: str, model: dict | None, model_id: str) -> list[str]:
    data = (model or {}).get("data", {})
    return [role, model_id, data.get("name") or "—",
            data.get("owner") or "—", str(data.get("tier") or "—")]


def _lineage_rows(handoff: dict) -> list[list[str]]:
    rows = []
    for f in handoff.get("data", {}).get("field_lineage", []):
        prov = " ".join(x for x in (f.get("provider_type"), f.get("provider_units")) if x)
        cons = " ".join(x for x in (f.get("consumer_type"), f.get("consumer_units")) if x)
        rows.append([f.get("provider_field") or "—", prov or "—",
                     f.get("consumer_field") or "—", cons or "—", f.get("note") or ""])
    return rows


def build_handover_tex(handoff: dict, provider: dict | None, consumer: dict | None,
                       as_of: str, *, logo: bool = False) -> str:
    """LaTeX source for the interoperability-validation document of one handoff."""
    data = handoff.get("data", {})
    from_id, to_id = data.get("from_model", "?"), data.get("to_model", "?")
    status = data.get("status", "Draft")
    signoff = ("Approved by the MRC at " + _esc(data.get("mrc_signoff_meeting") or "")
               + (" on " + _esc(data["mrc_signoff_date"]) if data.get("mrc_signoff_date") else "")
               if status == "Approved" else _esc(status))

    specifics = _table(
        ["Role", "Model ID", "Name", "Owner", "Tier"],
        [_model_line("Provider", provider, from_id), _model_line("Consumer", consumer, to_id)],
    )
    lineage = _lineage_rows(handoff)
    lineage_tbl = (_table(["Provider field", "Type/units", "Consumer field", "Type/units", "Note"], lineage)
                   if lineage else "\\textit{\\textcolor{gray}{No field mappings declared yet.}}\n")

    body = (
        _section("Executive Summary of the Handover",
                 "This document validates the model-to-model handover from provider "
                 "\\textbf{" + _esc(from_id) + "} to consumer \\textbf{" + _esc(to_id) +
                 "} --- one link in the string of pearls. "
                 + (_esc(data.get("data_handoff")) + " " if data.get("data_handoff") else "")
                 + "MRC compatibility status: \\textbf{" + signoff + "}.\n")
        + _section("Provider--Consumer Specifics", specifics)
        + _section("Scope of Handover",
                   (_esc(data.get("compatibility")) + "\n" if data.get("compatibility")
                    else "") + _guidance([
                       "Nature, granularity and timeliness of the data provided",
                       "How the consumer uses the data and any subsequent changes",
                       "Distributional assumption differences between provider and consumer",
                       "Level of dependency and the consumer's assumptions on accuracy/availability",
                   ]))
        + _section("Handover Parameters (Field Lineage)",
                   "Each row pairs a provider field with the consumer field it feeds.\n" + lineage_tbl)
    )
    for title, prompts in _GUIDANCE:
        body += _section(title, _guidance(prompts))
    body += _section("Sign-offs",
                     "Model risk committee: \\textbf{" + signoff + "}.\n"
                     + _guidance(["Author sign-off", "Provider and consumer handover sign-off"]))

    return (
        preamble("Model Interoperability Validation") + "\\begin{document}\n"
        + front_matter("Model Interoperability Validation",
                       from_id + " to " + to_id + " handover", date=as_of, logo=logo, toc=True)
        + body
        + history_page(as_of, "Interoperability validation generated")
        + "\\end{document}\n"
    )


def render_handover_pdf(handoff: dict, provider: dict | None, consumer: dict | None,
                        as_of: str) -> bytes:
    """Build and compile the handover document to PDF bytes."""
    assets = logo_asset()
    tex = build_handover_tex(handoff, provider, consumer, as_of, logo=bool(assets))
    return compile_tex(tex, assets=assets)
