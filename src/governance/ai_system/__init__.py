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
"""The AI System aggregate: a deployed use of a generative or agentic model.

Third in the family after the model inventory and ML Applications, and built the
same way -- see ``config/governance/_ai_system.py`` for why its governance half
carries a model's field names exactly.
"""
from src.governance.ai_system.commands import (
    AGGREGATE_TYPE,
    add_collection_item,
    register_ai_system,
    remove_collection_item,
    retire_ai_system,
    update_ai_system_field,
    update_collection_item,
)
from src.governance.ai_system.projection import (
    get_ai_system,
    list_ai_systems,
    rebuild_ai_system_view,
)

__all__ = [
    "AGGREGATE_TYPE", "add_collection_item", "get_ai_system", "list_ai_systems",
    "rebuild_ai_system_view", "register_ai_system", "remove_collection_item",
    "retire_ai_system", "update_ai_system_field", "update_collection_item",
]
