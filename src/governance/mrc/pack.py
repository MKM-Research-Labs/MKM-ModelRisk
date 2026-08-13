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


def _subject_of(item: dict) -> str:
    """The model, product or handoff a routed sign-off is about — empty for an
    ordinary agenda item, which is what separates the running order from the
    requests the committee is answering."""
    return (item.get("subject_model_id") or item.get("subject_product_id")
            or item.get("subject_handoff_id") or "")


def _signoff_ask(item: dict) -> str:
    """What the committee was asked to ratify, in one cell.

    Mirrors the console's Approvals row so the pack and the screen describe the same
    decision: a rating names the RAG proposed, a change of owner names who it moves
    between, and a lifecycle decision names itself. Plain ASCII for the arrow — the
    preamble loads ``inputenc`` with utf8, and a literal arrow is a compile risk this
    document should not take on.
    """
    kind = item.get("signoff_kind") or "rag"
    if kind == "owner":
        return (f"{item.get('from_owner') or 'unassigned'} -> "
                f"{item.get('to_owner') or 'unassigned'}")
    if kind in ("retire", "reactivate"):
        return kind.capitalize()
    return item.get("proposed_rag") or ""


def _owners(action: dict) -> str:
    """An action's owners as one cell.

    An action agreed before it could have several owners holds a bare string, so
    both shapes have to read the same way in a pack reprinted from the event log.
    """
    owner = action.get("owner")
    if isinstance(owner, list):
        return ", ".join(str(o) for o in owner)
    return owner or ""


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


def _carried_forward_section(actions: list[dict], meeting_id: str) -> str:
    """Actions still owed once this meeting closes — the register the next one inherits.

    Deliberately includes actions agreed at THIS meeting alongside older ones: what
    matters to the reader is what is still owed when the meeting ends, not which
    meeting first said it. The source meeting is named so an action carried over
    several meetings shows how long it has been open.
    """
    if not actions:
        return ""
    rows = [[a.get("item_id"), a.get("model_id"), a.get("description"), _owners(a),
             a.get("status"),
             "this meeting" if a.get("meeting_id") == meeting_id else a.get("meeting_id")]
            for a in actions]
    return _section("Actions Carried Forward", _para_table(
        ["ID", "Model", "Action", "Owners", "Status", "Agreed at"], rows,
        [0.08, 0.15, 0.32, 0.17, 0.14, 0.14], caption="Actions carried forward") +
        "\\par\\medskip\n\\textit{These remain outstanding at the close of this meeting "
        "and carry forward to the next.}")


def build_tex(
    meeting: dict, settings: dict, logo: bool = False,
    remediations_by_model: dict[str, list[dict]] | None = None,
    carried_forward: list[dict] | None = None,
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
    # The running order, and only that. A routed sign-off is an owner's request that
    # happens to be carried on an agenda item; it is answered in its own section below,
    # so listing it here too printed every one twice and buried the order the meeting
    # actually ran. The console's Agenda tab draws the same distinction.
    running_order = [a for a in data.get("agenda", []) if not _subject_of(a)]
    agenda = _section("Agenda", _para_table(
        ["#", "Title", "Presenter", "Status"],
        [[i + 1, a.get("title"), a.get("presenter"), a.get("status")]
         for i, a in enumerate(running_order)],
        [0.06, 0.60, 0.17, 0.17], caption="Agenda")) if running_order else ""
    # Every sign-off routed to this meeting, with what the committee was asked to
    # ratify. Deliberately not only the rating ones: a change of model owner, a
    # retirement and a reactivation carry no proposed RAG, and filtering on one would
    # drop them from the record entirely now that the agenda no longer repeats them.
    signoff_items = [a for a in data.get("agenda", []) if _subject_of(a)]
    signoffs = _section("Sign-offs", _table(
        ["Subject", "Decision", "Status"],
        [[_subject_of(a), _signoff_ask(a), a.get("status")] for a in signoff_items],
        caption="Sign-offs")) if signoff_items else ""
    # In-scope models with who presents, whether an analysis was attached, and — the
    # part that makes this minutes rather than an attendance list — what the committee
    # concluded: the outcome it recorded and the basis it let the presenter proceed on.
    in_scope = data.get("models_in_scope") or []
    models_scope = _section("Models in Scope (Analysis)", _para_table(
        ["Model", "Presenter", "Analysis", "Outcome", "Basis to proceed"],
        [[m.get("model_id"), m.get("presenter"), m.get("analysis_original_name") or "--",
          m.get("analysis_status") or "Pending", m.get("proceed_basis") or "--"]
         for m in in_scope],
        [0.17, 0.15, 0.20, 0.16, 0.32], caption="Models in scope")) if in_scope else ""
    # The committee's discussion of each model, kept out of the table because a note
    # is prose and a table cell is not.
    notes = "".join(
        "\\textbf{" + _esc(m.get("model_id")) + "}: " + _esc(m.get("analysis_note")) +
        "\\par\\medskip\n" for m in in_scope if m.get("analysis_note"))
    if notes:
        models_scope += _section("Analysis Discussion", notes)
    # The standing completeness-audit item: its latest run and the committee's
    # notes, so the minutes carry the audit outcome the committee reviewed.
    audit_item = next((a for a in data.get("agenda", [])
                       if a.get("kind") == "completeness_audit"), None)
    completeness = ""
    if audit_item and audit_item.get("audit_version"):
        rows = [["Version", audit_item.get("audit_version")],
                ["Records audited", audit_item.get("audit_entities") or "0"],
                ["Findings", audit_item.get("audit_findings") or "0"],
                ["Generated by", audit_item.get("audit_generated_by") or "--"],
                ["Generated at", audit_item.get("audit_generated_at") or "--"],
                ["Review status", audit_item.get("status") or "Pending"]]
        body = _table(["Field", "Value"], rows, caption="Completeness audit")
        if audit_item.get("audit_notes"):
            body += "\\par\\medskip\n\\textbf{Committee notes:} " + _esc(audit_item["audit_notes"])
        completeness = _section("Completeness Audit", body)
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
        ["ID", "Model", "Action", "Owners", "Status"],
        [[a.get("item_id"), a.get("model_id"), a.get("description"), _owners(a),
          a.get("status")] for a in data.get("actions", [])], caption="Actions")) if data.get("actions") else ""
    carried = _carried_forward_section(carried_forward or [], meeting.get("meeting_id", ""))
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
        + participants + agenda + signoffs + models_scope + completeness + minutes + decisions
        + actions + carried + remediation
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
        # Deliberately platform-neutral: this reaches a Windows pilot as readily as
        # a developer's Mac, and "brew install" is no help to the former. It also
        # says PATH out loud, because the usual cause is an installed tectonic.exe
        # sitting somewhere the app cannot see.
        raise TectonicNotFound(
            "tectonic is not installed, or is not on this process's PATH, so PDF "
            "reports cannot be generated. See the README (Install tectonic) for "
            "your platform, then restart the app so it picks up the new PATH."
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
    from src.governance.mrc.projection import outstanding_actions_for_committee
    assets = logo_asset(settings)
    return compile_tex(
        build_tex(meeting, settings, logo=bool(assets),
                  remediations_by_model=_collect_remediations(meeting),
                  carried_forward=outstanding_actions_for_committee(
                      meeting.get("meeting_id", ""))),
        assets,
    )
