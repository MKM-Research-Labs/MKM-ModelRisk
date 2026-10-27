"""The numerical-method catalogue, and the model collection that references it.

Referenced, not governed: a model names the off-the-shelf methods it is built with so
its documentation can, and nothing scores, classifies or reviews the list. These tests
hold both halves -- that the reference works, and that it stays only a reference.
"""
from __future__ import annotations

import pytest

from config.governance import COLLECTION_SPECS, EXEMPT_COLLECTIONS, REFERENCE_SPECS
from config.governance._completeness_weights import AUDIT_WEIGHT_SECTIONS
from config.governance._numerical_methods import (DEFAULT_NUMERICAL_METHODS,
                                                  NUMERICAL_METHOD_FAMILIES)
from src.governance.change._rules import classify
from src.governance.completeness.scan import scan
from src.governance.errors import DomainError
from src.governance.model_inventory import (add_collection_item, rebuild_inventory_view,
                                            register_model)
from src.governance.model_inventory.document import build_model_document_tex
from src.governance.reference import (add_option, ensure_default_reference_lists,
                                      get_reference_lists)


def test_the_seed_is_whole_unique_and_in_known_families():
    names = [m["value"] for m in DEFAULT_NUMERICAL_METHODS]
    assert len(names) == len(set(names))
    assert {m["family"] for m in DEFAULT_NUMERICAL_METHODS} <= set(NUMERICAL_METHOD_FAMILIES)
    assert names[-1] == "Other"
    # Printed into the LaTeX dossier, so kept to ASCII.
    assert all(name.isascii() for name in names)


def test_the_admin_list_seeds_a_vacuum_with_family_and_notes():
    ensure_default_reference_lists()
    rows = get_reference_lists()["numerical_method"]
    assert [r["value"] for r in rows] == [m["value"] for m in DEFAULT_NUMERICAL_METHODS]
    assert rows[0]["family"] == DEFAULT_NUMERICAL_METHODS[0]["family"]
    assert "numerical_method" in REFERENCE_SPECS


def test_a_model_may_link_several_methods_but_only_defined_ones():
    add_option(list_name="numerical_method", fields={"value": "Brent's method"}, actor="admin")
    add_option(list_name="numerical_method", fields={"value": "Cubic spline"}, actor="admin")
    register_model(model_id="M1", name="Alpha", actor="alice")
    for method in ("Brent's method", "Cubic spline"):
        add_collection_item(model_id="M1", collection="numerical_methods",
                            fields={"numerical_method": method,
                                    "implementation": "SciPy"}, actor="alice")
    with pytest.raises(DomainError):
        add_collection_item(model_id="M1", collection="numerical_methods",
                            fields={"numerical_method": "Made Up Solver"}, actor="alice")


def test_an_empty_list_is_never_a_completeness_gap():
    assert "numerical_methods" in EXEMPT_COLLECTIONS
    # Nor may a division weight it back in through its risk policy.
    assert "numerical_methods" not in AUDIT_WEIGHT_SECTIONS["collection"]["names"]
    register_model(model_id="M1", name="Alpha", actor="a", fields={"tier": 2})
    rebuild_inventory_view()
    row = repr(scan("2026-10-27", model_ids=["M1"], product_ids=[]))
    assert "numerical_methods" not in row
    assert COLLECTION_SPECS["numerical_methods"]["label"] not in row


def test_linking_a_method_is_an_administrative_change():
    before = {"numerical_methods": []}
    after = {"numerical_methods": [{"numerical_method": "Monte Carlo (pseudo-random)"}]}
    assert classify(subject_type="model", before=before, after=after) == "Administrative"


def test_the_methods_appear_in_the_model_documentation():
    model = {"model_id": "M1", "data": {"name": "Alpha", "numerical_methods": [
        {"numerical_method": "Brent's method", "implementation": "scipy.optimize.brentq",
         "note": "Implied hazard rate"}]}}
    tex = build_model_document_tex(model, {"fields": {}}, "2026-10-27")
    assert "\\section{Numerical methods}" in tex
    assert "Implied hazard rate" in tex
