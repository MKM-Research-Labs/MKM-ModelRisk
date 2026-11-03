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
"""SR 11-7 as a second data set for one engine — not a second engine.

The test that matters here is ``test_evidence_resolver_is_shared``. A framework whose
coverage were resolved some other way is how two reports come to disagree about whether
the same model is validated, and then neither is used. Everything else is scaffolding
around that.
"""
from __future__ import annotations

from config.governance._finos import FINOS_RISKS
from config.governance._frameworks import FRAMEWORK_COVERAGE, FRAMEWORK_NOTES
from config.governance._sr117 import SR_11_7, SR_11_7_CLAUSES
from src.governance.completeness import framework as engine
from src.governance.completeness.framework import DECLARED, PROBES, coverage, tally

_ROWS = [{"record_id": "M1"}]
_MODELS = [{"model_id": "M1", "data": {"owner": "Alice", "peer_reviewer": "Bob",
                                       "tier": "1", "materiality": "High",
                                       "complexity": "Low", "rag_rating": "Green"}}]
_AS_OF = "2026-09-05"


def _coverage(**kw):
    return coverage(_ROWS, _MODELS, _AS_OF, **kw)


# --- One engine ---------------------------------------------------------------

def test_evidence_resolver_is_shared(monkeypatch):
    """Both frameworks resolve through the same function, proven by replacing it.

    Not "both produce plausible numbers" — that would pass with two implementations
    that happened to agree today. Swap the one resolver and BOTH frameworks change; if
    SR 11-7 ever grows its own, this test goes on passing for FINOS and fails here.
    """
    seen: list[str] = []
    real = engine._measured

    def recording(probe, estate, note):
        seen.append(probe)
        return real(probe, estate, note)

    monkeypatch.setattr(engine, "_measured", recording)
    clauses = _coverage()

    measured = {c["probe"] for c in clauses if c["probe"] not in DECLARED}
    assert measured <= set(seen), "a measured clause bypassed the shared resolver"

    frameworks_measured = {c["framework"] for c in clauses
                           if c["probe"] not in DECLARED}
    assert SR_11_7 in frameworks_measured
    assert FINOS_RISKS in frameworks_measured


def test_sr117_and_finos_rows_have_the_same_shape():
    """One engine, so one row shape. A reader comparing two frameworks' tables is
    comparing like with like."""
    clauses = _coverage()
    sr = next(c for c in clauses if c["framework"] == SR_11_7)
    finos = next(c for c in clauses if c["framework"] == FINOS_RISKS)
    assert set(sr) == set(finos)


# --- The filter ---------------------------------------------------------------

def test_sr117_filter_returns_only_sr_clauses():
    scoped = _coverage(framework=SR_11_7)
    assert scoped, "the filter must not empty the report"
    assert {c["framework"] for c in scoped} == {SR_11_7}
    assert len(scoped) == len(SR_11_7_CLAUSES)


def test_the_filter_narrows_and_never_changes_a_result():
    """A framework whose coverage depended on being asked for alone would be one
    nobody could reconcile against the others."""
    def signature(clauses):
        return [(c["ref"], c["state"], c["met"], c["total"]) for c in clauses]

    assert signature(_coverage(framework=SR_11_7)) == signature(
        [c for c in _coverage() if c["framework"] == SR_11_7])


def test_an_unknown_framework_filters_to_nothing_rather_than_to_everything():
    """The dangerous failure: a typo in a picker silently reporting the whole estate
    under one framework's name."""
    assert _coverage(framework="SR 11-8") == []


def test_tally_scopes_to_one_framework():
    counts = tally(_coverage(), SR_11_7)
    assert counts["clauses"] == len(SR_11_7_CLAUSES)
    assert sum(v for k, v in counts.items() if k != "clauses") == counts["clauses"]


# --- The data set itself ------------------------------------------------------

def test_sr117_is_registered_alongside_the_others():
    names = [name for name, _ in FRAMEWORK_COVERAGE]
    assert SR_11_7 in names
    assert names.count(SR_11_7) == 1


def test_every_sr117_clause_names_a_probe_the_engine_knows():
    """A clause naming a probe nothing implements reports nothing, and sits in the
    table looking like coverage."""
    for ref, title, probe, note in SR_11_7_CLAUSES:
        assert probe in PROBES or probe in DECLARED, f"{ref} names unknown probe {probe}"
        assert title.strip() and note.strip(), f"{ref} is not explained"


def test_the_clauses_that_are_about_people_are_declared_not_measured():
    """Internal audit and external resources are facts about the firm's audit function
    and its suppliers. A platform scoring itself on those is marking its own homework.
    """
    declared = {ref: probe for ref, _, probe, _ in SR_11_7_CLAUSES if probe in DECLARED}
    assert declared["VI.C"] == "institution"
    assert declared["VI.D"] == "institution"


def test_the_inventory_clause_is_the_one_the_platform_answers_outright():
    """VI.E is the guidance's central requirement and an inventory is what this is."""
    clause = next(c for c in _coverage(framework=SR_11_7) if c["ref"] == "VI.E")
    assert clause["met"] == clause["total"] == len(_MODELS)


def test_sr117_carries_the_note_that_disclaims_conformity():
    """No framework here certifies a product, and SR 11-7 least of all — it is
    addressed to banks and their examiners."""
    note = FRAMEWORK_NOTES[SR_11_7]
    assert "not a standard a product conforms to" in note
