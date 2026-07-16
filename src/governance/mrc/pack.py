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

from config.files import IMAGE_EXTENSIONS
from src.files import extension, upload_path

_LATEX_REPLACEMENTS = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
    "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def _esc(value: Any) -> str:
    text = "" if value is None else str(value)
    return "".join(_LATEX_REPLACEMENTS.get(ch, ch) for ch in text)


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    cols = "|" + "l|" * len(headers)
    head = " & ".join("\\textbf{" + _esc(h) + "}" for h in headers) + " \\\\ \\hline"
    body = "".join(" & ".join(_esc(c) for c in row) + " \\\\ \\hline\n" for row in rows)
    return ("\\begin{longtable}{" + cols + "}\n\\hline " + head + "\n" + body +
            "\\end{longtable}\n")


def _section(title: str, body: str) -> str:
    return "\\section*{" + _esc(title) + "}\n" + body


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
        )
    return _section("Model Remediation (in-scope)", body) if body else ""


def build_tex(
    meeting: dict, settings: dict, logo_filename: str | None = None,
    remediations_by_model: dict[str, list[dict]] | None = None,
) -> str:
    """Render the LaTeX source for a meeting pack."""
    data = meeting.get("data", {})
    fields = settings.get("fields", {})
    title = data.get("title") or meeting.get("meeting_id", "MRC Meeting")

    header = ""
    if logo_filename:
        header += "\\includegraphics[height=1.4cm]{" + logo_filename + "}\\\\[4pt]\n"
    if fields.get("org_name"):
        header += "{\\large\\textbf{" + _esc(fields["org_name"]) + "}}\\\\\n"
    if fields.get("org_address"):
        header += "{\\small " + _esc(fields["org_address"]) + "}\\\\\n"

    info = " \\quad ".join(
        "\\textbf{" + label + ":} " + _esc(data.get(key))
        for label, key in (("Division", "division"),
                            ("Department", "department"), ("Date", "date"), ("Time", "time"),
                            ("Location", "location"), ("Chair", "chair"), ("Status", "status"))
    )

    participants = _section("Participants", _table(
        ["Name", "Role", "Organisation", "Status"],
        [[p.get("name"), p.get("role"), p.get("organisation"), p.get("status")]
         for p in data.get("participants", [])])) if data.get("participants") else ""
    agenda = _section("Agenda", _table(
        ["#", "Title", "Presenter", "Status"],
        [[i + 1, a.get("title"), a.get("presenter"), a.get("status")]
         for i, a in enumerate(data.get("agenda", []))])) if data.get("agenda") else ""
    # Sign-off agenda items (a model/product + a proposed RAG) called out on
    # their own, with the outcome.
    signoff_items = [
        a for a in data.get("agenda", [])
        if (a.get("subject_model_id") or a.get("subject_product_id")) and a.get("proposed_rag")
    ]
    signoffs = _section("Model Sign-offs", _table(
        ["Subject", "Proposed RAG", "Status"],
        [[a.get("subject_model_id") or a.get("subject_product_id"),
          a.get("proposed_rag"), a.get("status")] for a in signoff_items])) if signoff_items else ""
    # In-scope models with who presents and whether an analysis was attached.
    in_scope = data.get("models_in_scope") or []
    models_scope = _section("Models in Scope (Analysis)", _table(
        ["Model", "Presenter", "Analysis"],
        [[m.get("model_id"), m.get("presenter"), m.get("analysis_original_name") or "--"]
         for m in in_scope])) if in_scope else ""
    minutes = ""
    if data.get("minutes"):
        body = "".join(
            "\\textbf{" + _esc(m.get("title")) + "} (" + _esc(m.get("presenter")) + "): " +
            _esc(m.get("text")) + "\\par\\medskip\n" for m in data["minutes"])
        minutes = _section("Minutes", body)
    decisions = _section("Decisions", _table(
        ["ID", "Date", "Decision"],
        [[x.get("item_id"), x.get("date"), x.get("description")]
         for x in data.get("decisions", [])])) if data.get("decisions") else ""
    actions = _section("Actions", _table(
        ["ID", "Action", "Owner", "Target", "Status"],
        [[a.get("item_id"), a.get("description"), a.get("owner"), a.get("target_date"),
          a.get("status")] for a in data.get("actions", [])])) if data.get("actions") else ""
    remediation = _model_remediation_section(
        data.get("models_in_scope") or [], remediations_by_model or {},
    )

    footer = _esc(fields.get("framework", "")) + " --- " + _esc(fields.get("handbook_reference", ""))
    return (
        "\\documentclass[11pt]{article}\n"
        "\\usepackage[a4paper,margin=20mm]{geometry}\n"
        "\\usepackage{graphicx}\\usepackage{longtable}\\usepackage{array}\n"
        "\\usepackage{xcolor}\\usepackage{parskip}\n"
        "\\pagestyle{plain}\n\\begin{document}\n"
        "\\begin{center}\n" + header + "\\end{center}\n"
        "{\\Large\\textbf{" + _esc(title) + "}}\\\\[4pt]\n" + info + "\\par\\bigskip\n" +
        participants + agenda + signoffs + models_scope + minutes + decisions + actions + remediation +
        "\\vfill\\begin{center}\\small\\textcolor{gray}{" + footer + "}\\end{center}\n"
        "\\end{document}\n"
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
        open_steps = [s for s in steps if (s.get("status") or "Open") != "Closed"]
        if open_steps:
            out[model_id] = open_steps
    return out


def render_pack_pdf(meeting: dict, settings: dict) -> bytes:
    """Build and compile a meeting pack, embedding the logo if one is set."""
    logo = settings.get("logo")
    assets: dict[str, bytes] = {}
    logo_filename = None
    if logo and extension(logo["filename"]) in IMAGE_EXTENSIONS:
        path = upload_path("mrc", logo["filename"])
        if path.exists():
            logo_filename = "logo." + extension(logo["filename"])
            assets[logo_filename] = path.read_bytes()
    return compile_tex(
        build_tex(meeting, settings, logo_filename, _collect_remediations(meeting)),
        assets,
    )
