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
"""The completeness scan over the register, and the PDF it produces."""
from __future__ import annotations

import importlib

import pytest

from src.governance.completeness.report import (
    build_completeness_tex, render_completeness_pdf)
from src.governance.completeness.scan import scoped_models
from src.governance.completeness.scan import (
    MODEL_KIND, PRODUCT_KIND, _retrievable, product_scope, scan)
from src.governance.model_inventory import rebuild_inventory_view, register_model
from src.governance.product import rebuild_product_view, register_product

AS_OF = "2026-06-22"
# The evidence a product's component models produce, which the product is therefore
# not scored on holding a copy of.
ANALYTICS_CATEGORIES = ("Sensitivity", "Analysis", "Test Results", "Unit Test",
                        "Integration Test", "Benchmark Test", "Calibration",
                        "Convergence", "Segment analysis")
SETTINGS = {"fields": {"org_name": "MKM"}}


@pytest.fixture
def register():
    """One model and one product on the register, so the scan has both kinds to
    audit and the report has rows to lay out."""
    register_model(model_id="M1", name="Alpha", actor="a", fields={"tier": 2})
    register_product(product_id="PRD-1", product="Swap", actor="a",
                     fields={"calculating_agent": "Murex"})
    rebuild_inventory_view()
    rebuild_product_view()


def test_scan_covers_models_then_products(register):
    """Products follow the models so a reader meets the model gaps before the
    product gaps that inherit from them."""
    rows = scan(AS_OF)
    kinds = [r["entity_kind"] for r in rows]
    assert kinds, "the scan found nothing to audit"
    assert kinds == sorted(kinds, key=lambda k: 0 if k == MODEL_KIND else 1)


def test_scan_orders_worst_completeness_first(register):
    scores = [r["completeness"] for r in scan(AS_OF)]
    assert scores == sorted(scores), "least complete record should be read first"


def test_scan_scoped_to_ids_audits_only_those(register):
    """A per-MRC audit passes the committee's in-scope ids; only those records are
    audited (here, the model but not the product)."""
    rows = scan(AS_OF, model_ids=["M1"], product_ids=[])
    ids = {(r["entity_kind"], r["entity_id"]) for r in rows}
    assert ids == {(MODEL_KIND, "M1")}, "only the in-scope model should be audited"


def test_scan_empty_scope_audits_nothing(register):
    """A committee that oversees nothing gets an empty audit, not the whole estate
    (the None default is what audits everything)."""
    assert scan(AS_OF, model_ids=[], product_ids=[]) == []


def test_a_recorded_document_with_no_file_is_not_counted_as_present(tmp_path, monkeypatch):
    """A document recorded against a model whose file is missing from disk is a
    gap, not evidence: an audit that trusted the metadata would report a pack that
    cannot actually be produced."""
    monkeypatch.setattr("src.files.store.UPLOAD_DIR", tmp_path)
    check = _retrievable("model/M1")
    assert check({"filename": "absent.pdf"}) is False
    assert check({}) is False, "a record with no filename cannot be retrievable"
    (tmp_path / "model" / "M1").mkdir(parents=True)
    (tmp_path / "model" / "M1" / "there.pdf").write_bytes(b"%PDF-")
    assert check({"filename": "there.pdf"}) is True


def test_product_is_not_scored_on_its_components_analytics_evidence(register):
    """A Product's analytics are its component models, so the paper about them --
    testing, sensitivities, the wider analysis, the training artefacts -- is demanded
    of those models and not restated here. Scoring it on both would raise a finding
    the product could only close by filing a second copy of the model's evidence.
    """
    rows = {r["entity_kind"]: r for r in scan(AS_OF)}
    demanded = {g["key"] for g in rows[PRODUCT_KIND]["gaps"] if g["kind"].startswith("document")}
    assert not demanded & set(ANALYTICS_CATEGORIES), (
        "a product should not be scored on its component models' evidence")
    assert "Core Documentation" in demanded, (
        "what the product itself IS is still the product's own obligation")
    # The same categories are still demanded of a model, or the evidence would have
    # been dropped from the estate rather than moved to where it is produced.
    model_gaps = {g["key"] for g in rows[MODEL_KIND]["gaps"]}
    assert set(ANALYTICS_CATEGORIES) <= model_gaps, (
        "the model that produces the analytics is still asked to evidence them")


def test_product_scope_mirrors_the_model_one():
    assert product_scope("PRD-X") == "product/PRD-X"


def test_report_renders_over_a_populated_register(register):
    tex = build_completeness_tex(scan(AS_OF), SETTINGS, AS_OF)
    assert "Summary of findings" in tex
    assert "Findings by severity" in tex
    assert "Records by tier" in tex
    assert tex.strip().endswith("\\end{document}")


def test_report_renders_over_an_empty_register():
    """An instance with nothing registered still produces a document that says so,
    rather than failing or emitting an empty page."""
    tex = build_completeness_tex([], SETTINGS, AS_OF)
    assert "Summary of findings" in tex
    assert tex.strip().endswith("\\end{document}")


def test_report_pdf_scans_the_register_itself(register, monkeypatch):
    """Called without rows the report runs the scan; a caller that already has
    them passes them in rather than paying for a second pass."""
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex",
                        lambda tex, assets=None: b"%PDF-stub")
    assert render_completeness_pdf(SETTINGS, AS_OF) == b"%PDF-stub"
    assert render_completeness_pdf(SETTINGS, AS_OF, rows=scan(AS_OF)) == b"%PDF-stub"


def test_document_with_no_filename_is_not_retrievable(tmp_path, monkeypatch):
    """A record carrying no filename cannot produce a file, so it must not be
    treated as evidence held."""
    module = importlib.import_module("src.governance.completeness.scan")
    check = module._retrievable("model/M1")
    assert check({}) is False
    assert check({"filename": ""}) is False


def test_path_layer_failure_is_absent_evidence_not_a_crash(monkeypatch):
    """One unresolvable path must not abort the whole audit: the finding is that
    the evidence cannot be produced, which is what the register should say."""
    # The package re-exports scan() as a function, which shadows the module of
    # the same name; even "import a.b.scan as m" resolves to the function via
    # attribute lookup, so the module has to be fetched by name.
    module = importlib.import_module("src.governance.completeness.scan")

    def _boom(scope, filename):
        raise OSError("name too long")

    monkeypatch.setattr(module, "upload_path", _boom)
    assert module._retrievable("model/M1")({"filename": "x.pdf"}) is False


def test_record_with_no_findings_renders_a_clean_dossier():
    from src.governance.completeness.report import _dossier
    row = {"entity_id": "M1", "entity_name": "Alpha", "entity_kind": "Model",
           "gaps": [], "completeness": 1.0, "tier": 1, "rag": "Green",
           "events_in_window": 0, "escalation": 1.0, "tier_weight": 1.0,
           "rag_multiplier": 1.0, "event_pressure": 1.0, "staleness": 1.0}
    assert "No completeness findings" in _dossier(row)


def _plain(tex: str) -> str:
    """Strip the LaTeX the table helpers add, so a test can look for the value
    the config actually holds rather than its typeset form."""
    return tex.replace("\\allowbreak{}", "").replace("\\_", "_")


def test_appendix_lists_every_exclusion_the_scoring_applies():
    """The document tells a reader what it does not report. If an exclusion is
    added to the config and not to the appendix, the report understates its own
    scope — which is the one omission a completeness audit cannot make."""
    from config.governance import (CONDITIONAL_DOC_CATEGORIES, DOC_CATEGORY_SATISFIED_BY,
                                   EXEMPT_COLLECTIONS, EXEMPT_DOC_CATEGORIES,
                                   EXEMPT_FIELDS)
    from src.governance.completeness._method import appendix
    printed = _plain(appendix())
    for name in (list(EXEMPT_COLLECTIONS) + list(EXEMPT_FIELDS)
                 + list(EXEMPT_DOC_CATEGORIES) + list(CONDITIONAL_DOC_CATEGORIES)
                 + list(DOC_CATEGORY_SATISFIED_BY)):
        assert name in printed, name


def test_appendix_lists_the_placeholder_values():
    from config.governance import PLACEHOLDER_VALUES
    from src.governance.completeness._method import appendix
    printed = _plain(appendix())
    for value in PLACEHOLDER_VALUES:
        assert value in printed, value


def test_scoped_models_follows_the_same_rule_as_the_findings_scan():
    """A committee audit that scoped its findings but not its inventory would put
    the committee's records and the firm's in one report with nothing to tell
    them apart. None is the whole estate; an empty sequence is nothing."""
    every = scoped_models()
    assert [m["model_id"] for m in scoped_models(None)] == [m["model_id"] for m in every]
    assert scoped_models([]) == []
    if every:
        wanted = every[0]["model_id"]
        assert [m["model_id"] for m in scoped_models([wanted])] == [wanted]
    # An id nobody has registered scopes to nothing rather than falling back.
    assert scoped_models(["MODEL-THAT-DOES-NOT-EXIST"]) == []
