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
"""The top-level Documents area is external-only: categorised docs are rejected.

Guards the failure where an importer attached categorised model documents
(Core Documentation / Analysis / …) to the governance-wide aggregate instead of
their model, so they surfaced in the external Documents tab.
"""
from __future__ import annotations

import pytest

from src.governance.documents import (GOVERNANCE_DOCUMENTS_AGGREGATE,
                                       add_document)
from src.governance.errors import DomainError


def test_categorised_document_rejected_on_the_governance_aggregate():
    with pytest.raises(DomainError, match="external-only"):
        add_document(
            aggregate_type=GOVERNANCE_DOCUMENTS_AGGREGATE, aggregate_id="global",
            scope="governance", filename="model_inputs.pdf", data=b"%PDF-1.5",
            description="Sensitivity Analysis", actor="tester",
            category="Core Documentation",
        )


def test_uncategorised_external_document_still_allowed():
    doc = add_document(
        aggregate_type=GOVERNANCE_DOCUMENTS_AGGREGATE, aggregate_id="global",
        scope="governance", filename="regulation.pdf", data=b"%PDF-1.5",
        description="External reference paper", actor="tester",
    )
    assert doc["category"] == ""


def test_categorised_document_allowed_on_a_model():
    doc = add_document(
        aggregate_type="ModelInventoryEntry", aggregate_id="MKM-GUARD-TEST",
        scope="model/MKM-GUARD-TEST", filename="sensitivity.pdf", data=b"%PDF-1.5",
        description="Sensitivity analysis", actor="tester",
        category="Analysis",
    )
    assert doc["category"] == "Analysis"
