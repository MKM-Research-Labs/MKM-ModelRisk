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
"""Model-handoff aggregate: field lineage + compatibility on each chain edge."""
from src.governance.model_handoff.commands import (
    AGGREGATE_TYPE,
    add_collection_item,
    declare_handoff,
    handoff_id,
    remove_collection_item,
    split_handoff_id,
    update_collection_item,
    update_handoff_field,
)
from src.governance.model_handoff.projection import (
    get_handoff,
    get_handoff_for_edge,
    list_handoffs,
    rebuild_handoff_view,
)

__all__ = [
    "AGGREGATE_TYPE",
    "declare_handoff",
    "update_handoff_field",
    "add_collection_item",
    "update_collection_item",
    "remove_collection_item",
    "handoff_id",
    "split_handoff_id",
    "get_handoff",
    "get_handoff_for_edge",
    "list_handoffs",
    "rebuild_handoff_view",
]
