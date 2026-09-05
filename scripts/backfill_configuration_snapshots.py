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
"""Give every existing AI System a first configuration snapshot, from its current values.

Without one, a system registered before snapshots existed has a configuration and no
record of it — and the first snapshot taken afterwards would look like the beginning of
its history rather than a late reading of a configuration that had been running for
months. The backfill makes the starting point explicit and dated.

**What it records is a reading, not a reconstruction.** It captures the values the
record holds TODAY, and says so in the reason on the event. Nobody can recover what the
configuration was last March from a record that never stored it, and a backfill that
guessed would be worse than none — a snapshot is only worth anything because it is
evidence, and evidence cannot be inferred backwards.

Idempotent: a system that already has a snapshot is skipped, so re-running adds nothing.

Run against the configured ModelRisk database:

    python -m scripts.backfill_configuration_snapshots
"""
from __future__ import annotations

from src.governance.ai_system import (list_ai_systems, list_snapshots,
                                      rebuild_ai_system_view,
                                      rebuild_configuration_snapshot_view,
                                      take_configuration_snapshot)

ACTOR = "backfill_configuration_snapshots"
_REASON = ("First configuration snapshot, read from the record's current values when "
           "snapshots were introduced. Not a reconstruction of any earlier state.")


def backfill_configuration_snapshots(config=None) -> str:
    """Snapshot every AI System that has none. Returns what it did."""
    # Retired systems included on purpose: a hibernated system's configuration is part
    # of the record of what the estate was, and it can be reactivated.
    systems = list_ai_systems(config=config, include_retired=True)
    if not systems:
        return "no AI Systems on this estate"

    taken, skipped = [], []
    for row in systems:
        ai_system_id = row["ai_system_id"]
        if list_snapshots(ai_system_id, config=config):
            skipped.append(ai_system_id)
            continue
        if row.get("retired"):
            # The domain refuses a snapshot of a retired system, which is right — but a
            # backfill that fell over on one would leave the estate half done.
            skipped.append(ai_system_id)
            continue
        take_configuration_snapshot(ai_system_id=ai_system_id, actor=ACTOR,
                                    reason=_REASON, config=config)
        taken.append(ai_system_id)

    # A backfill driven from a script leaves the read models stale, and the UI then
    # shows a correct database through a wrong view.
    rebuild_configuration_snapshot_view(config=config)
    rebuild_ai_system_view(config=config)

    if not taken:
        return f"nothing to do — all {len(skipped)} already snapshotted or retired"
    return (f"snapshotted {len(taken)}: {', '.join(taken)}"
            + (f"; skipped {len(skipped)}" if skipped else ""))


def main() -> None:
    print(backfill_configuration_snapshots())


if __name__ == "__main__":
    main()
