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
"""Meeting Pack PDF via LaTeX (compiled with tectonic).

``build_tex`` is pure (meeting + settings -> LaTeX source); ``compile_tex`` runs
the LaTeX engine; ``render_pack_pdf`` ties them together, embedding the branding
logo from the MRC settings when one is set.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from config.governance import CLOSED_REMEDIATION_STATUS
# The LaTeX string helpers and the shared house style live in one place now; this
# module keeps re-exporting _esc/_table/_section for its existing callers.
from src.governance.latex import (
    _esc, _para_table, _section, _table, front_matter, history_page, logo_asset,
    preamble,
)


def _model_remediation_section(
    in_scope_items: list[dict], remediations_by_model: dict[str, list[dict]],
) -> str:
    """Per-model section listing each in-scope model's open remediation steps."""
    body = ""
    for item in in_scope_items:
        model_id = item.get("model_id")
        if not model_id:
            continue
        rows = remediations_by_model.get(model_id) or []
        if not rows:
            continue
        body += "\\subsection*{" + _esc(model_id) + "}\n" + _table(
            ["ID", "Description", "Owner", "Priority", "Due", "Status"],
            [[r.get("item_id"), r.get("description"), r.get("owner"),
              r.get("priority"), r.get("due_date"), r.get("status")] for r in rows],
            caption="Remediation actions for " + model_id,
        )
    return _section("Model Remediation (in-scope)", body) if body else ""


def build_tex(
    meeting: dict, settings: dict, logo: bool = False,
    remediations_by_model: dict[str, list[dict]] | None = None,
) -> str:
    """Render the LaTeX source for a meeting pack in the shared house style."""
    data = meeting.get("data", {})
    fields = settings.get("fields", {})
    title = data.get("title") or meeting.get("meeting_id", "MRC Meeting")

    info = " \\quad ".join(
        "\\textbf{" + label + ":} " + _esc(data.get(key))
        for label, key in (("Division", "division"),
                            ("Line of Business", "line_of_business"), ("Date", "date"), ("Time", "time"),
                            ("Location", "location"), ("Chair", "chair"), ("Status", "status"))
    )

    participants = _section("Participants", _table(
        ["Name", "Role", "Organisation", "Status"],
        [[p.get("name"), p.get("role"), p.get("organisation"), p.get("status")]
         for p in data.get("participants", [])], caption="Participants")) if data.get("participants") else ""
    # A wrapping table: agenda titles can be long (an event review carries the
    # event's summary), and a fixed-width table pushed the Status column — which
    # is where an item shows as reviewed — off the right edge of the page.
    agenda = _section("Agenda", _para_table(
        ["#", "Title", "Presenter", "Status"],
        [[i + 1, a.get("title"), a.get("presenter"), a.get("status")]
         for i, a in enumerate(data.get("agenda", []))],
        [0.06, 0.60, 0.17, 0.17], caption="Agenda")) if data.get("agenda") else ""
    # Sign-off agenda items (a model/product + a proposed RAG) called out on
    # their own, with the outcome.
    signoff_items = [
        a for a in data.get("agenda", [])
        if (a.get("subject_model_id") or a.get("subject_product_id")) and a.get("proposed_rag")
    ]
    signoffs = _section("Model Sign-offs", _table(
        ["Subject", "Proposed RAG", "Status"],
        [[a.get("subject_model_id") or a.get("subject_product_id"),
          a.get("proposed_rag"), a.get("status")] for a in signoff_items],
        caption="Model sign-offs")) if signoff_items else ""
    # In-scope models with who presents and whether an analysis was attached.
    in_scope = data.get("models_in_scope") or []
    models_scope = _section("Models in Scope (Analysis)", _table(
        ["Model", "Presenter", "Analysis"],
        [[m.get("model_id"), m.get("presenter"), m.get("analysis_original_name") or "--"]
         for m in in_scope], caption="Models in scope")) if in_scope else ""
    minutes = ""
    if data.get("minutes"):
        # The presenter is only named when one was recorded; minutes captured by
        # acknowledging an agenda item may have none, and "Title ():" reads as a
        # rendering fault rather than as an absent presenter.
        body = "".join(
            "\\textbf{" + _esc(m.get("title")) + "}" +
            (" (" + _esc(m.get("presenter")) + ")" if m.get("presenter") else "") + ": " +
            _esc(m.get("text")) + "\\par\\medskip\n" for m in data["minutes"])
        minutes = _section("Minutes", body)
    decisions = _section("Decisions", _table(
        ["ID", "Date", "Decision"],
        [[x.get("item_id"), x.get("date"), x.get("description")]
         for x in data.get("decisions", [])], caption="Decisions")) if data.get("decisions") else ""
    actions = _section("Actions", _table(
        ["ID", "Action", "Owner", "Target", "Status"],
        [[a.get("item_id"), a.get("description"), a.get("owner"), a.get("target_date"),
          a.get("status")] for a in data.get("actions", [])], caption="Actions")) if data.get("actions") else ""
    remediation = _model_remediation_section(
        data.get("models_in_scope") or [], remediations_by_model or {},
    )

    org = fields.get("org_name", "")
    return (
        preamble(title, org_name=org) + "\\begin{document}\n"
        + front_matter(title, "MRC Meeting Pack", org_name=org, date=data.get("date", ""),
                       author=data.get("chair", ""), logo=logo, toc=True)
        + info + "\\par\\bigskip\n"
        + history_page(data.get("date", ""), "MRC meeting pack generated", org_name=org)
        + participants + agenda + signoffs + models_scope + minutes + decisions + actions + remediation
        + "\\end{document}\n"
    )


class TectonicNotFound(RuntimeError):
    """The tectonic LaTeX engine is not installed, so no PDF can be produced."""


def compile_tex(tex: str, assets: dict[str, bytes] | None = None) -> bytes:
    """Compile LaTeX source to PDF bytes using tectonic.

    Raises ``TectonicNotFound`` when the engine is not on PATH, so callers can
    turn a missing optional dependency into a clean error instead of a raw
    ``FileNotFoundError`` from the subprocess layer.
    """
    if shutil.which("tectonic") is None:
        raise TectonicNotFound(
            "tectonic is not installed, so PDF reports cannot be generated. "
            "Install it (e.g. `brew install tectonic`) and try again."
        )
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        (base / "doc.tex").write_text(tex)
        for name, content in (assets or {}).items():
            (base / name).write_bytes(content)
        subprocess.run(
            ["tectonic", "--outdir", str(base), str(base / "doc.tex")],
            check=True, capture_output=True,
        )
        return (base / "doc.pdf").read_bytes()


def _collect_remediations(meeting: dict) -> dict[str, list[dict]]:
    """For each in-scope model, gather its open remediation steps.

    The lookup goes through the model inventory's public projection — the same
    surface the rest of the platform reads from, so the pack stays in sync with
    what's on screen.
    """
    from src.governance.model_inventory import get_model
    out: dict[str, list[dict]] = {}
    for item in meeting.get("data", {}).get("models_in_scope") or []:
        model_id = item.get("model_id")
        if not model_id or model_id in out:
            continue
        model = get_model(model_id)
        steps = (model or {}).get("data", {}).get("remediation_steps") or []
        open_steps = [s for s in steps
                      if (s.get("status") or "Open") != CLOSED_REMEDIATION_STATUS]
        if open_steps:
            out[model_id] = open_steps
    return out


def render_pack_pdf(meeting: dict, settings: dict) -> bytes:
    """Build and compile a meeting pack, using the org's uploaded logo if one is set."""
    assets = logo_asset(settings)
    return compile_tex(
        build_tex(meeting, settings, logo=bool(assets), remediations_by_model=_collect_remediations(meeting)),
        assets,
    )
