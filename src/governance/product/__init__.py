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
"""Product aggregate: register/rebind/edit/retire Product Valuation Models and query them."""
from src.governance.product.commands import (
    AGGREGATE_TYPE,
    add_collection_item,
    rebind_component,
    register_product,
    remove_collection_item,
    retire_product,
    update_collection_item,
    update_product_field,
)
from src.governance.product.projection import (
    derived_identifier,
    get_product,
    list_products,
    rebuild_product_view,
)

__all__ = [
    "AGGREGATE_TYPE",
    "register_product",
    "rebind_component",
    "update_product_field",
    "retire_product",
    "add_collection_item",
    "update_collection_item",
    "remove_collection_item",
    "derived_identifier",
    "get_product",
    "list_products",
    "rebuild_product_view",
]
