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
"""What happens TO a Product: hibernation, and coming back from it.

Split from ``test_product`` (what a Product IS: registering it, binding its
components, editing its fields) when the reactivate half arrived. The two change
for different reasons, which is the seam -- not the line count that made it urgent.

The wrinkle particular to this aggregate is its ``status`` field: retiring a Product
overwrites it with "Retired", where the model, ML Application and AI System all leave
the institution's own vocabulary alone. So bringing one back has to put the displaced
word back, and has to cope with a Product retired before that was recorded.
"""
from __future__ import annotations

import pytest

from config.governance import SIGNOFF_REQUESTS_COLLECTION
from src.governance.errors import DomainError
from src.governance.model_inventory import rebuild_inventory_view, register_model
from src.governance.product import (
    add_collection_item,
    get_product,
    reactivate_product,
    rebuild_product_view,
    register_product,
    retire_product,
    update_product_field,
)

_BINDINGS = {"calculating_agent": "Murex"}


def _live_model(model_id="MKM-AN-001"):
    register_model(model_id=model_id, name="Analytics engine", actor="admin")
    rebuild_inventory_view()
    return model_id


def _register(product_id="Product-0001", product="Government Bond", **overrides):
    register_product(product_id=product_id, product=product, actor="admin",
                     fields={**_BINDINGS, **overrides})
    rebuild_product_view()


def test_retire_makes_read_only():
    _live_model()
    _register()
    retire_product(product_id="Product-0001", actor="admin")
    rebuild_product_view()
    product = get_product("Product-0001")
    assert product["retired"] and product["data"]["status"] == "Retired"
    with pytest.raises(DomainError):
        update_product_field(product_id="Product-0001", field="notes", value="x", actor="admin")
    with pytest.raises(DomainError):
        retire_product(product_id="Product-0001", actor="admin")


def test_retire_unknown_product_rejected():
    with pytest.raises(DomainError):
        retire_product(product_id="Product-NONE", actor="admin")


def test_hibernation_reverses_and_puts_the_displaced_status_back():
    """Retiring is hibernation, not a terminal state. A Product is the one aggregate
    whose retire moves its ``status`` field, so bringing it back has to restore the
    word that retirement displaced -- otherwise a live Product reads as retired."""
    _live_model()
    _register()
    update_product_field(product_id="Product-0001", field="status", value="Active",
                         actor="admin")
    retire_product(product_id="Product-0001", actor="admin")
    rebuild_product_view()
    assert get_product("Product-0001")["data"]["status"] == "Retired"

    reactivate_product(product_id="Product-0001", actor="admin")
    rebuild_product_view()
    product = get_product("Product-0001")
    assert not product["retired"]
    assert product["data"]["status"] == "Active"
    # Editable again, which is the point of it not being terminal.
    update_product_field(product_id="Product-0001", field="notes", value="back",
                         actor="admin")


def test_a_live_product_cannot_be_reactivated():
    _live_model()
    _register()
    with pytest.raises(DomainError, match="not retired"):
        reactivate_product(product_id="Product-0001", actor="admin")


def test_reactivate_unknown_product_rejected():
    with pytest.raises(DomainError, match="does not exist"):
        reactivate_product(product_id="Product-NONE", actor="admin")


def test_a_product_retired_before_the_status_was_recorded_comes_back_editable():
    """The honest fallback, decided and then folded.

    A Product hibernated by an older ``ProductRetired`` event carries no record of
    what its status was, and the log is append-only -- so there is nothing to
    restore. It comes back with the status still reading "Retired": wrong, but
    visible, and editable again the moment it is live. Inventing a status the
    committee never saw would be worse than leaving one for a person to correct.
    """
    from src.governance.product._rules import decide_reactivate
    from src.governance.product._state import ProductState, apply

    was = ProductState(exists=True, retired=True, fields={"status": "Retired"})
    event_type, payload = decide_reactivate(was)
    assert event_type == "ProductReactivated"
    assert payload == {}, "nothing to restore, so nothing is claimed"

    # The fold has to survive the empty payload rather than assuming a status.
    now = apply(was, event_type, payload)
    assert now.retired is False
    assert now.fields["status"] == "Retired", "left for a person to correct"


def test_the_committee_exemption_still_needs_a_product_to_exist():
    """A hibernated Product stays writable to the committee's own collections, so a
    reactivate can be requested on it. That exemption skips the ordinary editable
    check, which is the check that would otherwise have caught a Product that was
    never registered -- so it has to refuse on its own account."""
    with pytest.raises(DomainError, match="does not exist"):
        add_collection_item(product_id="Product-NONE",
                            collection=SIGNOFF_REQUESTS_COLLECTION,
                            fields={"kind": "retire", "status": "Pending"},
                            actor="admin")
