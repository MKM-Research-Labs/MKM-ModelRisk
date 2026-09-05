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
"""MRC-meeting aggregate: schedule meetings and manage their collections."""
from src.governance.mrc._rules import DomainError
from src.governance.mrc.commands import (
    AGGREGATE_TYPE,
    add_collection_item,
    remove_collection_item,
    schedule_meeting,
    seed_standing_agenda,
    update_collection_item,
    update_meeting_field,
)
from src.governance.mrc.projection import (
    derive_org_scope,
    get_meeting,
    get_meeting_enriched,
    list_meetings,
    list_meetings_enriched,
    committee_at_levels,
    matching_mrc,
    meeting_items_for_model,
    outstanding_actions_for_committee,
    rebuild_meeting_view,
)

from src.governance.mrc.routing import route

__all__ = [
    "AGGREGATE_TYPE",
    "DomainError",
    "schedule_meeting",
    "seed_standing_agenda",
    "update_meeting_field",
    "add_collection_item",
    "update_collection_item",
    "remove_collection_item",
    "derive_org_scope",
    "get_meeting",
    "get_meeting_enriched",
    "list_meetings",
    "list_meetings_enriched",
    "committee_at_levels",
    "matching_mrc",
    "route",
    "meeting_items_for_model",
    "outstanding_actions_for_committee",
    "rebuild_meeting_view",
]
