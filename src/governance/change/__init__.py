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
"""The Change aggregate: a proposed change to a record, and the tier it falls into.

Moody's four-tier taxonomy -- Administrative, Bounded, Measurement, Material -- as one
engine serving both the ML and AI workflows. The tiers and the triggers are data in
``config/governance/_change.py``; what differs between the workflows is only the depth
of revalidation a tier calls for.
"""
from src.governance.change.commands import (
    AGGREGATE_TYPE,
    classify_change,
    propose_change,
    supersede_change,
)
from src.governance.change.projection import (
    get_change,
    list_changes,
    list_changes_for,
    rebuild_change_view,
)

__all__ = [
    "AGGREGATE_TYPE", "classify_change", "get_change", "list_changes",
    "list_changes_for", "propose_change", "rebuild_change_view", "supersede_change",
]
