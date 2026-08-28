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
"""Counting the estate against an enterprise framework's clauses.

The clause list, its citations and its wording are configuration
(``config.governance._frameworks``); this module is only the counting. The split
is the point: an adopter re-points the audit at their own framework by editing
data, and the arithmetic that says "17 of 20 models carry this" does not move.

A clause is never reported as evidenced because the platform *can* hold the
record. It is evidenced because the estate *does*: the probe counts records, and
a capability nobody has populated reads as Not evidenced. An assessor is owed the
second number, not the first.

Where a clause has no applicable record at all -- no models on the register, or a
clause that only bites on records the estate does not currently have -- the
result is Not evidenced with the population said out loud. That is a deliberate
choice against the flattering reading: an audit can only evidence a clause from
records, and "nothing needed it" is a claim the reader should see and challenge
rather than one this report should make silently on the estate's behalf.
"""
from __future__ import annotations

from datetime import date

from config.governance import (
    COVERAGE_ABSENT,
    COVERAGE_EVIDENCED,
    COVERAGE_EVIDENCED_AT,
    COVERAGE_OUTSIDE,
    COVERAGE_PARTIAL,
    FRAMEWORK_COVERAGE,
    TREATABLE_RATINGS,
)
from config.governance._finos import EVIDENCE_PROBE
from src.governance.completeness._gaps import _recorded
from src.governance.completeness._probe_helpers import (_any_entries, _data,
                                                        _filled, _share)
from src.governance.completeness._probes_ai import AI_PROBES
from src.governance.completeness.review_programme import model_state
from src.identity import same_person

# Clause outcomes declared in the clause table rather than counted. Each is a
# statement about the platform, not about the estate, so no number can move it:
# a clause nothing could evidence is not made truer by a well-kept register.
DECLARED = {
    "institution": COVERAGE_OUTSIDE,
    "absent": COVERAGE_ABSENT,
    "partial": COVERAGE_PARTIAL,
}


def _independent(data: dict) -> bool:
    """A reviewer who is recorded and is not the owner.

    The check an assessor makes first and the register cannot currently fail: a
    model reviewed by the person who owns it has been through a process, but not
    an independent one, and the record does not distinguish the two by itself.
    """
    reviewer = data.get("peer_reviewer")
    return _recorded(reviewer) and not same_person(reviewer, data.get("owner"))


def _in_date(data: dict, as_of: str) -> bool:
    """A review scheduled and not yet overdue at the report date."""
    due = data.get("next_review_date")
    if not _recorded(due):
        return False
    try:
        return date.fromisoformat(str(due)) >= date.fromisoformat(str(as_of))
    except ValueError:
        return False


def _reviewed(model: dict) -> bool:
    """A review under way or signed off, read through the programme's own rules so
    the coverage table and the review section cannot disagree about what counts."""
    state = model_state(model)
    return bool(state["started"] or state["signed_off"])


def _share(estate: dict, predicate, applies=None) -> tuple[int, int]:
    """How many of the applicable models carry the evidence."""
    population = [_data(m) for m in estate["models"]]
    if applies is not None:
        population = [d for d in population if applies(d)]
    return sum(1 for d in population if predicate(d)), len(population)


# Each probe takes the estate and returns (records carrying the evidence, records
# the clause applies to). A population of zero is reported, not hidden.
PROBES = {
    "inventory": lambda e: (len(e["models"]), len(e["models"])),
    "identification": lambda e: _share(
        e, lambda d: _any_entries(d, "assumptions", "limitations", "model_weaknesses")),
    "analysis": lambda e: _share(
        e, lambda d: _filled(d, "tier", "materiality", "complexity")),
    "evaluation": lambda e: _share(e, lambda d: _filled(d, "rag_rating")),
    "criteria": lambda e: _share(
        e, lambda d: _recorded(d.get("division")) and d.get("division") in e["ratified"]),
    "accountability": lambda e: _share(e, lambda d: _filled(d, "owner")),
    "independence": lambda e: _share(e, _independent),
    "committee": lambda e: _share(
        e, lambda d: _filled(d, "mrc_signoff_date") or _any_entries(d, "signoff_history")),
    "challenge": lambda e: _share(
        e, lambda d: _any_entries(d, "review_notes", "signoff_history")),
    # A model records substantial change as a version; an ML Application has no
    # versions and records it as a train. Both evidence COSO 15, and naming both here
    # keeps this one lambda over one population rather than a per-type branch.
    "change": lambda e: _share(e, lambda d: _any_entries(d, "version_history", "training_runs")),
    "monitoring": lambda e: _share(e, lambda d: _in_date(d, e["as_of"])),
    "treatment": lambda e: _share(
        e, lambda d: _any_entries(d, "remediation_steps"),
        applies=lambda d: d.get("rag_rating") in TREATABLE_RATINGS),
    "review": lambda e: (sum(1 for m in e["models"] if _reviewed(m)), len(e["models"])),
    # Both are properties of this report over the records it audited: every
    # audited record is scored, banded, given a target date and printed here.
    "prioritisation": lambda e: (len(e["rows"]), len(e["rows"])),
    "reporting": lambda e: (len(e["rows"]), len(e["rows"])),
    # Acceptance testing recorded against the record. The one FINOS mitigation the
    # platform evidences from the register rather than from a filed description --
    # reporting it unevidenced because nobody had also written a paper about it
    # would be the register disowning evidence it holds.
    # AIR-OP-016. Counted over the WHOLE estate, not just AI Systems: bias is a
    # question about anything that scores people, and a model that ranks retail
    # applicants raises it exactly as a generative system does. It was AI-only while
    # the record had nowhere else to live, and that limit was a gap the row could not
    # report about itself.
    #
    # A recorded assessment, not a recorded intention: an entry names the attribute
    # assessed and what the measurement showed.
    "fairness": lambda e: _share(e, lambda d: _any_entries(d, "fairness_assessments")),
    # AIR-DET-015. The SECOND mitigation the platform evidences from the register
    # rather than from a filed description, on the same reasoning as acceptance
    # testing: a judge evaluation recorded against the record IS the evidence this row
    # asks for, and reporting it unevidenced because nobody had also written a paper
    # about it would be the register disowning what it holds.
    #
    # Counted over the records that carry evaluations at all, so an estate that has
    # never used a judge reads Not evidenced rather than dragging every record down.
    "judged": lambda e: _share(
        e, lambda d: any(r.get("kind") == "LLM-as-a-judge"
                         for r in (d.get("evaluations") or []))),
    "acceptance": lambda e: _share(
        e, lambda d: _filled(d, "unit_tests", "integration_tests", "benchmark_tests")),
    # The FINOS risk rows that only an AI System can answer. Kept in their own
    # module because they carry their own population rules -- see _probes_ai.
    **AI_PROBES,
}

# Probes that depend on WHICH row they are run for, and so cannot be a lambda over
# the estate alone. Kept in their own table rather than given every probe a second
# parameter it would ignore: every other probe's signature should not change to
# accommodate one caller that needs something they do not.
#
# Each returns (met, total, evidence) -- the third element is the sentence the table
# prints, because "1 of 1" is not what a reader of a mitigation row wants to see.
REF_PROBES = {EVIDENCE_PROBE: lambda e, ref: _filed_against(e["evidence"], ref)}


def _filed_against(documents: list[dict], ref: str) -> tuple[int, int, str]:
    """Whether any document on the FINOS shelf names this mitigation reference.

    The evidence names the document and the date it was filed, not a count. That is
    the whole claim being made: the institution has DESCRIBED this control, in this
    paper, on this date. Whether the control operates is not something a governance
    register observes, and the sentence must not imply that it does.
    """
    naming = [d for d in documents if ref in (d.get("finos_refs") or ())]
    if not naming:
        # Said in words rather than as "0 of 1", which reads as a measurement of
        # something and is not one. The sentence also tells a reader what to do.
        return 0, 1, "No document on the FINOS shelf names this reference."
    return 1, 1, "; ".join(
        f"{d.get('original_name') or d.get('filename')} (filed {_filed_on(d)})"
        for d in naming)


def _filed_on(document: dict) -> str:
    """The upload date, day-precision. A time of day on an evidence citation is
    noise in a table an assessor reads across."""
    return str(document.get("uploaded_at") or "")[:10] or "date not recorded"


def _state(met: int, total: int) -> str:
    if not total or not met:
        return COVERAGE_ABSENT
    return COVERAGE_EVIDENCED if met / total >= COVERAGE_EVIDENCED_AT else COVERAGE_PARTIAL


def _measured(probe: str, estate: dict, note: str, ref: str = "") -> dict:
    """One row's outcome, counted.

    A probe returns ``(met, total)`` and the evidence reads "17 of 20"; a reference
    probe may return a third element, and where it does that sentence replaces the
    count. The two are different claims -- a share of the estate against a named
    document -- and printing a share for something that is not one would be worse
    than useless.
    """
    result = (REF_PROBES[probe](estate, ref) if probe in REF_PROBES
              else PROBES[probe](estate))
    met, total, stated = (result if len(result) == 3 else (*result, ""))
    if not total:
        return {"state": COVERAGE_ABSENT, "met": 0, "total": 0,
                "evidence": "No applicable record on the register. " + note}
    evidence = stated or f"{met} of {total}."
    return {"state": _state(met, total), "met": met, "total": total,
            "evidence": " ".join(part for part in (evidence, note) if part)}


def coverage(rows: list[dict], models: list[dict], as_of: str,
             ratified=(), evidence=()) -> list[dict]:
    """Every clause of every configured framework, with its evidence.

    ``rows`` are the audited records (models and products), ``models`` the
    inventory the probes count over, and ``ratified`` the divisions whose risk
    policy their committee has actually approved -- a division still running on
    the firm-wide seed default has criteria, but not criteria it has adopted.

    ``evidence`` is the documents filed on the FINOS shelf. It is the one input
    here that is not the estate: the FINOS mitigation catalogue is evidenced by
    what an institution has written about its controls rather than by what its
    register holds, so those rows are counted against filed papers. An empty one
    leaves every such row unevidenced, which is the correct reading of a shelf
    nobody has filed anything on.
    """
    estate = {"rows": rows, "models": models, "as_of": as_of,
              "ratified": set(ratified), "evidence": list(evidence)}
    out = []
    for framework, clauses in FRAMEWORK_COVERAGE:
        for ref, title, probe, note in clauses:
            result = ({"state": DECLARED[probe], "met": 0, "total": 0, "evidence": note}
                      if probe in DECLARED else _measured(probe, estate, note, ref))
            out.append({"framework": framework, "ref": ref, "title": title,
                        "probe": probe, **result})
    return out


def tally(clauses: list[dict], framework: str | None = None) -> dict:
    """Clause counts by outcome, for one framework or across all of them."""
    scoped = [c for c in clauses if framework is None or c["framework"] == framework]
    counts = {}
    for clause in scoped:
        counts[clause["state"]] = counts.get(clause["state"], 0) + 1
    counts["clauses"] = len(scoped)
    return counts


__all__ = ["coverage", "tally", "PROBES", "REF_PROBES", "DECLARED",
           "TREATABLE_RATINGS"]
