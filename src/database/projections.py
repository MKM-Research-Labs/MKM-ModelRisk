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
"""Projection support: rebuild read models by replaying the event log.

In CQRS the event log is the source of truth; read models are derived and fully
rebuildable. ``replay`` streams events in global order to a handler so a
projection can be built from zero or caught up from a checkpoint.
"""
from __future__ import annotations

from typing import Callable

from src.database.eventstore import Event, read_all


def replay(
    handler: Callable[[Event], None],
    *,
    after_global_seq: int = 0,
    config=None,
) -> int:
    """Apply ``handler`` to every event after ``after_global_seq``.

    Returns the number of events replayed and the caller can read the last
    ``global_seq`` from the events it received to persist a checkpoint.
    """
    count = 0
    for event in read_all(after_global_seq=after_global_seq, config=config):
        handler(event)
        count += 1
    return count
