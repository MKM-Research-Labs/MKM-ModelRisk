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
"""A word an institution adds in Admin must be usable on a record.

The vocabularies were half-built: Admin accepted a new impact level, priority,
remediation status or review-answer status, and every record then refused it,
because the pure collection validator checked the value against the words that
SHIPPED rather than against the list as it stands. An adopter could rename their
vocabulary but never extend it.

The split now is: ``collections`` is pure and skips reference-backed choices; the
command layer checks them against the live list. So a word on the list is accepted
and a word on no list is still refused.
"""
from __future__ import annotations

import pytest

from config.governance import IMPACT_LIST, VERSION_LIFECYCLE_LIST
from src.governance.errors import DomainError
from src.governance.model_inventory import (add_collection_item, get_model,
                                            rebuild_inventory_view, register_model)
from src.governance.reference import add_option, ensure_default_status_vocabularies
from tests.web.conftest import HEADERS


def _model(model_id="M1"):
    register_model(model_id=model_id, name="Alpha", actor="admin")
    rebuild_inventory_view()
    return model_id


def _items(collection, model_id="M1"):
    return (get_model(model_id)["data"] or {}).get(collection) or []


def test_an_impact_level_added_in_admin_can_be_used_on_a_record():
    ensure_default_status_vocabularies()
    add_option(list_name=IMPACT_LIST,
               fields={"label": "Catastrophic", "value": "Catastrophic"}, actor="admin")
    _model()
    add_collection_item(model_id="M1", collection="assumptions",
                        fields={"description": "Rates never invert", "impact": "Catastrophic"},
                        actor="admin")
    rebuild_inventory_view()
    assert _items("assumptions")[0]["impact"] == "Catastrophic"


def test_a_word_on_no_list_is_still_refused():
    """Relaxing the pure check must not leave the field open to anything at all."""
    ensure_default_status_vocabularies()
    _model()
    with pytest.raises(DomainError, match="must be one of"):
        add_collection_item(model_id="M1", collection="assumptions",
                            fields={"description": "x", "impact": "Massive"}, actor="admin")


def test_the_version_lifecycle_is_admin_managed():
    """It was a fixed tuple in config: an adopter could not rename or extend the arc
    its own versions move through without a release."""
    ensure_default_status_vocabularies()
    add_option(list_name=VERSION_LIFECYCLE_LIST,
               fields={"label": "Deprecated", "value": "Deprecated"}, actor="admin")
    _model()
    add_collection_item(model_id="M1", collection="version_history",
                        fields={"version": "2.0", "lifecycle": "Deprecated"}, actor="admin")
    rebuild_inventory_view()
    assert _items("version_history")[0]["lifecycle"] == "Deprecated"


def test_the_shipped_version_lifecycle_words_still_work():
    """Seeded value == label == the word records already carry, so nothing in the
    estate moves when the vocabulary becomes admin-managed."""
    ensure_default_status_vocabularies()
    _model()
    add_collection_item(model_id="M1", collection="version_history",
                        fields={"version": "1.0", "lifecycle": "Being Enhanced"},
                        actor="admin")
    rebuild_inventory_view()
    assert _items("version_history")[0]["lifecycle"] == "Being Enhanced"


def test_the_new_vocabulary_reaches_the_admin_screen(client):
    ensure_default_status_vocabularies()
    res = client.get("/api/reference").get_json()
    labels = {c["key"]: c["label"] for c in res["collections"]}
    assert labels[VERSION_LIFECYCLE_LIST] == "Version lifecycle"
    assert len(res["data"][VERSION_LIFECYCLE_LIST]) == 4
