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
"""Separate governance documents that were minted with the same item id.

Ids used to be numbered from the item count, so removing one document and
uploading another reissued a live id. Two documents then share one, and nothing
downstream can tell them apart: retagging either retags both, and deleting either
deletes both. New uploads no longer do this (``collections.next_item_id``); this
repairs the ones already on the record.

Append-only, like the log it writes to: the shared id is retired and each
document re-filed under its own, keeping its name, file, size and upload date.
No file on disk is touched. Idempotent — a second run finds nothing to do.

Run against the configured ModelRisk database:

    python -m scripts.repair_duplicate_document_ids
"""
from __future__ import annotations

from src.governance.documents import reissue_duplicate_ids

ACTOR = "repair_duplicate_document_ids"
AGGREGATE = "GovernanceDocuments"
AGGREGATE_ID = "global"


def repair(config=None) -> list:
    """Re-file every governance document that shares an item id. Returns the moves."""
    return reissue_duplicate_ids(
        aggregate_type=AGGREGATE, aggregate_id=AGGREGATE_ID, actor=ACTOR, config=config)


def main() -> int:
    from src.database import run_migrations
    run_migrations()
    moved = repair()
    if not moved:
        print("no duplicate document ids found")
        return 0
    for move in moved:
        print(f"{move['was']} -> {move['now']}  {move['name']}")
    print(f"documents re-filed under a unique id: {len(moved)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
