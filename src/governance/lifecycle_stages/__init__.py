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
"""Per-division lifecycle stages: which of the catalogue a division's records use."""
from src.governance.lifecycle_stages._store import (
    AGGREGATE_TYPE,
    chosen_stages,
    chosen_stages_draft,
    load,
    stage_labels,
    stages_for,
)
from src.governance.lifecycle_stages._validate import (
    reject_division_move_out_of_stage,
    reject_unknown_lifecycle_stage,
)
from src.governance.lifecycle_stages.commands import (
    approve_division_stages,
    propose_division_stages,
    reject_division_stages,
    stages_in_use,
)

__all__ = [
    "AGGREGATE_TYPE",
    "approve_division_stages",
    "chosen_stages",
    "chosen_stages_draft",
    "load",
    "propose_division_stages",
    "reject_division_move_out_of_stage",
    "reject_division_stages",
    "reject_unknown_lifecycle_stage",
    "stage_labels",
    "stages_for",
    "stages_in_use",
]
