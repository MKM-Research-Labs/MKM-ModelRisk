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
"""A Product binds models and ML Applications from one component list.

One list rather than two: a product's risk story reads off "what is this built
from", and with two collections every consumer has to remember to read both. The
ones that forget do not error — they silently under-report, which on a completeness
audit is the worst failure available. So the row carries a ``kind`` and the
consumers branch on it.
"""
from __future__ import annotations

import pytest

from config.governance import (COMPONENT_KIND_ML, COMPONENT_KIND_MODEL,
                               PRODUCT_COMPONENTS, component_kind)
from src.governance.errors import DomainError
from src.governance.ml_application import (rebuild_ml_application_view,
                                           register_ml_application)
from src.governance.model_inventory import rebuild_inventory_view, register_model
from src.governance.product import (add_collection_item, get_product,
                                    rebuild_product_view, register_product)

_ML_FIELDS = {"name": "Retail PD scorecard", "division": "Risk", "owner": "Dana",
              "estimator": "GradientBoostingClassifier", "use_case": "Ranks applicants."}


def _product(product_id="Product-0001"):
    register_product(product_id=product_id, product="Government Bond", actor="admin",
                     fields={"calculating_agent": "Murex"})
    rebuild_product_view()
    return product_id


def _model(model_id="MKM-AN-001"):
    register_model(model_id=model_id, name="Analytics engine", actor="admin")
    rebuild_inventory_view()
    return model_id


def _ml(ml_application_id="MLA-0001"):
    register_ml_application(ml_application_id=ml_application_id, fields=_ML_FIELDS,
                            actor="admin")
    rebuild_ml_application_view()
    return ml_application_id


def _bind(product_id, **fields):
    add_collection_item(product_id=product_id, collection=PRODUCT_COMPONENTS,
                        fields=fields, actor="admin")
    rebuild_product_view()


def _components(product_id="Product-0001"):
    return (get_product(product_id)["data"] or {}).get(PRODUCT_COMPONENTS) or []


def test_a_product_binds_a_model_and_an_ml_application_in_one_list():
    p, m, mla = _product(), _model(), _ml()
    _bind(p, kind=COMPONENT_KIND_MODEL, component_type="Analytical Model", model_id=m)
    _bind(p, kind=COMPONENT_KIND_ML, model_id=mla, role="Scores the retail book")

    comps = _components()
    assert len(comps) == 2
    assert [component_kind(c) for c in comps] == [COMPONENT_KIND_MODEL, COMPONENT_KIND_ML]
    assert comps[1]["model_id"] == mla


def test_a_component_recorded_before_ml_existed_still_reads_as_a_model():
    """The log is append-only: every component bound before ML Applications existed
    carries no kind, so a blank has to keep meaning Model or those rows change meaning
    retrospectively."""
    assert component_kind({"model_id": "MKM-AN-001"}) == COMPONENT_KIND_MODEL
    assert component_kind({}) == COMPONENT_KIND_MODEL


def test_a_model_component_must_state_its_type():
    p, m = _product(), _model()
    with pytest.raises(DomainError, match="component_type is required"):
        _bind(p, kind=COMPONENT_KIND_MODEL, model_id=m)


def test_an_ml_component_needs_no_type():
    """Its provenance is its Estimator; there is no model_type that describes it, so
    requiring one would force whoever binds it to pick a lie from a dropdown."""
    p, mla = _product(), _ml()
    _bind(p, kind=COMPONENT_KIND_ML, model_id=mla)
    assert _components()[0]["model_id"] == mla


def test_an_unknown_kind_is_refused():
    p, m = _product(), _model()
    with pytest.raises(DomainError, match="kind must be one of"):
        _bind(p, kind="Spreadsheet", component_type="Analytical Model", model_id=m)


def test_the_product_pack_skips_ml_components():
    """Their ids resolve against a different register; asking the model pack builder
    for one would either fail or quietly bundle nothing."""
    from src.governance.product.pack import _component_model_ids

    p, m, mla = _product(), _model(), _ml()
    _bind(p, kind=COMPONENT_KIND_MODEL, component_type="Analytical Model", model_id=m)
    _bind(p, kind=COMPONENT_KIND_ML, model_id=mla)
    assert _component_model_ids(get_product(p)) == [m]


def test_the_document_names_an_ml_component_rather_than_calling_it_missing():
    """Looked up in the inventory, a bound ML Application reads as a missing model —
    which is a finding, not a component of another kind."""
    from src.governance.product._report_product import _component_models

    p, mla = _product(), _ml()
    _bind(p, kind=COMPONENT_KIND_ML, model_id=mla, role="Scores the retail book")
    tex = _component_models(get_product(p)["data"], None)
    assert "Retail PD scorecard" in tex
    assert "not in the inventory" not in tex


def test_the_model_map_ignores_ml_components():
    """An ML Application has no dependency chain, so it is not a node in the map."""
    from src.governance.product import derive_product_map

    p, m, mla = _product(), _model(), _ml()
    _bind(p, kind=COMPONENT_KIND_MODEL, component_type="Analytical Model", model_id=m)
    _bind(p, kind=COMPONENT_KIND_ML, model_id=mla)
    assert derive_product_map(p)["components"] == [m]
