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
"""The Model Review Report: what the reviewer signed, and what the MRC receives.

The committee does not adjudicate the review — it signs off the risk rating, and
this is the evidence in front of it when it does. So the report carries the
argument, not just the conclusion: both sides of every one of the nine questions,
the registers as agreed, and the record of challenge verbatim under the stage it
happened on. A reader has to be able to see that the model was challenged, by whom,
and what came of it, without taking anybody's word for it.
"""
from __future__ import annotations

from config.governance import (CHALLENGE_OPEN, NOTE_KIND_CHALLENGE, REVIEW_STAGES,
                               REVIEW_STAGE_KEYS)
from src.governance.latex import (_esc, _para_table, _section, _subsection,
                                  front_matter, history_page, logo_asset, preamble)
from src.governance.mrc.pack import compile_tex

DOC_TITLE = "Model Review Report"


def _prose(text: str) -> str:
    """A paragraph of the reviewer's own words, or a plain statement of absence.

    An empty section reads as a missing page; "None recorded" reads as a finding.
    """
    text = (text or "").strip()
    return _esc(text) + "\n\n" if text else "\\textit{None recorded.}\n\n"


def _register(rows: list, columns: list[tuple[str, str]], weights: list[float]) -> str:
    """One of the agreed registers as a wrapping table, or a stated absence."""
    if not rows:
        return "\\textit{None recorded.}\n\n"
    return _para_table([label for label, _ in columns],
                       [[row.get(key) or "" for _, key in columns] for row in rows],
                       weights)


def _questions(data: dict, collection: str) -> str:
    """The nine questions with both sides shown — the owner's answer and the
    reviewer's verdict on it. Shown together because a question the owner called
    Addressed and the reviewer Challenged is the single most interesting row in
    the document, and splitting them into two tables would bury it."""
    rows = []
    for i, q in enumerate(data.get(collection) or [], start=1):
        rows.append([
            str(i) + ". " + (q.get("short_label") or ""),
            q.get("status") or "",
            q.get("rationale") or "",
            (q.get("reviewer_verdict") or "Not reviewed") +
            (" — " + q["reviewer_comment"] if q.get("reviewer_comment") else ""),
        ])
    if not rows:
        return "\\textit{No questions recorded.}\n\n"
    return _para_table(["Question", "Owner", "Rationale", "Reviewer"], rows,
                       [0.18, 0.14, 0.38, 0.30])


def _challenge_record(data: dict, stage_key: str) -> str:
    """The thread for one stage, verbatim and in order.

    Printed rather than summarised: a count of challenges tells a reader nothing
    about whether the challenge was any good. Each note carries who wrote it, which
    side of the review they were on, and when — and a challenge says whether it was
    answered, and by which note.
    """
    notes = [n for n in (data.get("review_notes") or []) if n.get("stage") == stage_key]
    if not notes:
        return "\\textit{Nothing recorded.}\n\n"
    answered = {n.get("resolves") for n in notes if n.get("resolves")}
    out = []
    for note in notes:
        mark = ""
        if note.get("kind") == NOTE_KIND_CHALLENGE:
            state = "answered" if note.get("item_id") in answered else CHALLENGE_OPEN.lower()
            mark = "\\textbf{Challenge (" + state + ")} --- "
        if note.get("resolves"):
            mark = "\\textit{Answering " + _esc(note["resolves"]) + "} --- "
        out.append(
            "\\textbf{" + _esc(note.get("author_role") or "") + "} "
            + _esc(note.get("author") or "") + ", "
            + _esc((note.get("posted_at") or "").replace("T", " ")[:16])
            + " (" + _esc(note.get("item_id") or "") + ")\\par\n"
            + mark + _esc(note.get("text") or "") + "\\par\\medskip\n"
        )
    return "".join(out)


def _stage_body(data: dict, stage: dict, approvals: dict,
                questions_collection: str = "validation_questions") -> str:
    """One stage: what was agreed, the argument that got there, and who agreed it."""
    key = stage["key"]
    if key == "documents":
        body = _prose(data.get("review_scope"))
    elif key == "assumptions":
        body = _register(data.get("assumptions") or [],
                         [("Assumption", "description"), ("Impact", "impact"),
                          ("Monitoring", "monitoring"), ("Mitigation", "mitigation")],
                         [0.34, 0.10, 0.28, 0.28])
    elif key == "questions":
        body = _questions(data, questions_collection)
    elif key == "weaknesses":
        body = _register(data.get("model_weaknesses") or [],
                         [("Weakness", "description"), ("Impact", "impact")], [0.85, 0.15])
    elif key == "limitations":
        body = _register(data.get("limitations") or [],
                         [("Limitation of use", "description"), ("Impact", "impact"),
                          ("Monitoring trigger", "monitoring_trigger"),
                          ("Compensating control", "compensating_control")],
                         [0.34, 0.10, 0.28, 0.28])
    elif key == "remediation":
        # Its own branch, which it did not have: every stage after "limitations" fell
        # through to the monitoring approach, so the remediation section of every
        # report issued to date restated the monitoring paragraph instead of listing
        # what the review found outstanding. The stage exists precisely so the
        # committee sees that list before it signs anything off.
        body = _register(data.get("remediation_steps") or [],
                         [("Finding", "description"), ("Action", "action"),
                          ("Owner", "owner"), ("Status", "status")],
                         [0.34, 0.34, 0.16, 0.16])
    else:
        body = _prose(data.get("monitoring_approach"))
    approval = approvals.get(key) or {}
    agreed = (
        "Agreed by " + _esc(approval.get("approved_by") or "") + " on "
        + _esc((approval.get("approved_at") or "")[:10])
        + ((". " + _esc(approval["note"])) if approval.get("note") else "") + "\\par\n"
        if approval else "\\textit{Not agreed.}\\par\n"
    )
    return (body + _subsection("Record of challenge", _challenge_record(data, key))
            + _subsection("Agreement", agreed))


def build_review_report_tex(model: dict, settings: dict, signoff: dict, as_of: str,
                            approvals: dict, *, logo: bool = False,
                            id_key: str = "model_id",
                            questions_collection: str = "validation_questions",
                            stages: tuple = REVIEW_STAGES) -> str:
    """LaTeX source for one record's Model Review Report.

    The defaults are a model's, so every existing caller is unchanged. The three
    parameters exist because an ML Application and an AI System are reviewed through
    exactly this workflow and receive exactly this report -- they differ only in which
    key holds their id, where their questionnaire lives, and what the questions stage
    is called. The report is deliberately still titled a Model Review Report: these are
    model-governed records, and the platform already gives them a model's governance
    vocabulary so one probe counts all three.
    """
    data = model.get("data") or {}
    org = settings.get("fields", {}).get("org_name", "")
    record_id = str(model.get(id_key) or "")
    title = record_id + " --- " + str(data.get("name") or "")
    return (
        preamble(DOC_TITLE, org_name=org) + "\\begin{document}\n"
        + front_matter(title, DOC_TITLE, org_name=org, date=as_of, logo=logo, toc=True)
        + history_page(as_of, DOC_TITLE + " signed off by the reviewer", org_name=org)
        + _section("Scope and basis", _prose(
            "This report records the review of " + record_id + ", stage by "
            "stage, including the exchange between the model owner and the reviewer. It is "
            "placed before the Model Risk Committee as the evidence supporting the model's "
            "risk rating; the committee's own decision is that rating, not this review."))
        + _section("The review", _para_table(
            ["Field", "Value"],
            [["Record", record_id],
             ["Owner", data.get("owner") or ""],
             ["Reviewer", data.get("peer_reviewer") or ""],
             ["Why this review", data.get("review_trigger") or ""],
             ["Signed off by", signoff.get("signed_by") or ""],
             ["Signed off at", (signoff.get("signed_at") or "").replace("T", " ")[:16]]],
            [0.3, 0.7]))
        + "".join(
            _section(str(i) + ". " + stage["label"],
                     _stage_body(data, stage, approvals, questions_collection))
            for i, stage in enumerate(stages))
        + _section("Reviewer's final commentary", _prose(signoff.get("commentary")))
        + "\\end{document}\n"
    )


def render_review_report_pdf(model: dict, settings: dict, signoff: dict, as_of: str,
                             approvals: dict, **record_type) -> bytes:
    """Build and compile the Model Review Report to PDF bytes.

    ``record_type`` carries ``id_key`` / ``questions_collection`` / ``stages`` through
    for a non-model record; omitted, it renders a model's exactly as before.
    """
    assets = logo_asset(settings)
    tex = build_review_report_tex(model, settings, signoff, as_of, approvals,
                                  logo=bool(assets), **record_type)
    return compile_tex(tex, assets=assets)


__all__ = ["DOC_TITLE", "REVIEW_STAGE_KEYS", "build_review_report_tex",
           "render_review_report_pdf"]
