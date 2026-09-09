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
"""The firm-wide lifecycle stage catalogue, ratified by the Company MRC."""
from src.governance.lifecycle_stage_catalogue._store import (
    AGGREGATE_TYPE,
    catalogue_labels,
    catalogue_values,
    get_catalogue,
    get_catalogue_draft,
    load,
)
from src.governance.lifecycle_stage_catalogue.commands import (
    LIFECYCLE_STAGE_FIELD,
    approve_lifecycle_catalogue,
    propose_lifecycle_catalogue,
    reject_lifecycle_catalogue,
    stages_in_use,
)

__all__ = [
    "AGGREGATE_TYPE",
    "LIFECYCLE_STAGE_FIELD",
    "approve_lifecycle_catalogue",
    "catalogue_labels",
    "catalogue_values",
    "get_catalogue",
    "get_catalogue_draft",
    "load",
    "propose_lifecycle_catalogue",
    "reject_lifecycle_catalogue",
    "stages_in_use",
]
