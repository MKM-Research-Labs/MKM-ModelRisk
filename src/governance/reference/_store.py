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
"""Reference-data store: admin-managed menu lists, event-sourced.

A single global aggregate whose collections are the menu lists (company,
division, department). State is folded from the event log via the shared
collection engine; no projection table is needed at this scale.
"""
from __future__ import annotations

from config.governance import REFERENCE_LISTS
from src.database import read_stream
from src.governance import collections as coll

AGGREGATE_TYPE = "ReferenceData"
AGGREGATE_ID = "global"


def load(config=None) -> tuple[dict[str, tuple], int]:
    """Fold the reference-data stream into its collections + current version."""
    collections: dict[str, tuple] = {}
    version = 0
    for event in read_stream(
        aggregate_type=AGGREGATE_TYPE, aggregate_id=AGGREGATE_ID, config=config
    ):
        collections = coll.fold(collections, event.event_type, event.payload)
        version = event.stream_seq
    return collections, version


def get_reference_lists(config=None) -> dict[str, list]:
    """Return every menu list as ``{list_name: [items]}`` (items carry item_id)."""
    collections, _ = load(config)
    return {name: list(collections.get(name, ())) for name in REFERENCE_LISTS}
