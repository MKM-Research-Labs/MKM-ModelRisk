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
"""Bibliography store: a global, event-sourced reference list."""
from __future__ import annotations

from src.database import read_stream
from src.governance import collections as coll

AGGREGATE_TYPE = "Bibliography"
AGGREGATE_ID = "global"
COLLECTION = "references"


def load(config=None) -> tuple[dict, int]:
    state: dict = {}
    version = 0
    for event in read_stream(
        aggregate_type=AGGREGATE_TYPE, aggregate_id=AGGREGATE_ID, config=config
    ):
        folded = coll.fold(state, event.event_type, event.payload)
        if folded is not None:
            state = folded
        version = event.stream_seq
    return state, version


def get_references(config=None) -> list:
    """All bibliography references."""
    state, _ = load(config)
    return list(state.get(COLLECTION, ()))
