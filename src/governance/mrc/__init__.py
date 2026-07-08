# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
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
    update_collection_item,
    update_meeting_field,
)
from src.governance.mrc.projection import (
    derive_org_scope,
    get_meeting,
    get_meeting_enriched,
    list_meetings,
    list_meetings_enriched,
    matching_mrc,
    meeting_items_for_model,
    rebuild_meeting_view,
)

__all__ = [
    "AGGREGATE_TYPE",
    "DomainError",
    "schedule_meeting",
    "update_meeting_field",
    "add_collection_item",
    "update_collection_item",
    "remove_collection_item",
    "derive_org_scope",
    "get_meeting",
    "get_meeting_enriched",
    "list_meetings",
    "list_meetings_enriched",
    "matching_mrc",
    "meeting_items_for_model",
    "rebuild_meeting_view",
]
