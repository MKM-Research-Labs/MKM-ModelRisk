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
"""Every table layout declares one column width per field it renders.

A layout with the wrong number of widths does not fail a unit test or a type check:
it produces LaTeX whose header row has more alignment tabs than the table has
columns, and the document fails to compile at the point somebody asks for it. That
is the worst place to discover it, so it is checked here instead -- for all three
report modules, because the mistake is equally available in each.
"""
from __future__ import annotations

import pytest

from config.governance import (COLLECTION_SPECS, ML_APPLICATION_COLLECTION_SPECS,
                               PRODUCT_COLLECTION_SPECS)
from src.governance.ml_application._report import LAYOUTS as ML_LAYOUTS
from src.governance.model_inventory._report_model import LAYOUTS as MODEL_LAYOUTS
from src.governance.product._report_product import LAYOUTS as PRODUCT_LAYOUTS

_MODULES = (
    ("ml_application", ML_LAYOUTS, ML_APPLICATION_COLLECTION_SPECS),
    ("model", MODEL_LAYOUTS, COLLECTION_SPECS),
    ("product", PRODUCT_LAYOUTS, PRODUCT_COLLECTION_SPECS),
)


@pytest.mark.parametrize("name,layouts,specs", _MODULES, ids=[m[0] for m in _MODULES])
def test_table_layouts_have_one_width_per_field(name, layouts, specs):
    mismatched = {
        key: (len(layout), len(specs[key]["fields"]))
        for key, layout in layouts.items()
        if layout != "blocks" and key in specs and len(layout) != len(specs[key]["fields"])
    }
    assert not mismatched, (
        f"{name}: these layouts declare the wrong number of column widths "
        f"(widths, fields): {mismatched}")


@pytest.mark.parametrize("name,layouts,specs", _MODULES, ids=[m[0] for m in _MODULES])
def test_every_rendered_collection_has_a_layout(name, layouts, specs):
    """A collection the report renders with no layout entry raises a KeyError mid
    document, which reaches the reader as a 500 rather than as a missing table."""
    missing = [key for key in layouts if key not in specs]
    assert not missing, f"{name}: layouts name collections the record does not carry: {missing}"
