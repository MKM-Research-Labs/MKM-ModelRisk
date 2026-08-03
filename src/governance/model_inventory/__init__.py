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
"""Model-inventory aggregate: register/update/retire models and query them."""
from src.governance.model_inventory._rules import DomainError
from src.governance.model_inventory.chain import derive_chain
from src.governance.model_inventory.neighbourhood import derive_neighbourhood
from src.governance.model_inventory.commands import (
    AGGREGATE_TYPE,
    add_collection_item,
    register_model,
    remove_collection_item,
    reactivate_model,
    retire_model,
    update_collection_item,
    update_model_field,
)
from src.governance.model_inventory.projection import (
    get_model,
    list_models,
    rebuild_inventory_view,
)

__all__ = [
    "AGGREGATE_TYPE",
    "DomainError",
    "register_model",
    "reactivate_model",
    "retire_model",
    "update_model_field",
    "add_collection_item",
    "update_collection_item",
    "remove_collection_item",
    "derive_chain",
    "derive_neighbourhood",
    "get_model",
    "list_models",
    "rebuild_inventory_view",
]
