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
"""The record's own history: its versions, and the changes made to it.

Split from ``_collections`` at the seam that module already had — the registers a
review works through (assumptions, limitations, weaknesses, remediation) are one thing,
and the log of what this record HAS BEEN is another. They are read by different people
at different moments: a reviewer works down the registers, an auditor reads back up the
history.

Merged into ``COLLECTION_SPECS`` exactly as the assessment collections are.
"""
from __future__ import annotations

from config.governance._change import CHANGE_CLASSES
# Imported from ``_collections``, which imports this module at its foot — after both
# names are bound. The cycle is one-way in practice and the alternative, moving the
# version vocabulary here too, would drag the version-history field spec's neighbours
# with it.
from config.governance._collections import (VALID_VERSION_LIFECYCLE,
                                            VERSION_LIFECYCLE_LIST)

HISTORY_COLLECTION_SPECS = {
    "version_history": {"label": "Versions", "id_prefix": "V", "fields": [
        {"key": "version", "label": "Version", "type": "text", "required": True},
        {"key": "date", "label": "Date", "type": "date"},
        {"key": "description", "label": "Description", "type": "text"},
        {"key": "author", "label": "Author", "type": "text"},
        {"key": "ref_document", "label": "Reference document", "type": "text"},
        {"key": "lifecycle", "label": "Lifecycle", "type": "choice",
         "options": VALID_VERSION_LIFECYCLE, "reference": VERSION_LIFECYCLE_LIST},
    ]},
    # What changed, when, and — since the four-tier engine landed — how far-reaching it
    # was. ``change_type`` was free text and, across the estate, blank on 24 of the 25
    # rows that exist: a column nobody could report on, sitting beside a change register
    # that classifies every proposal into Administrative, Bounded, Measurement or
    # Material.
    #
    # It takes the engine's vocabulary rather than a second one of its own. Two
    # vocabularies for the severity of a change is exactly what the spec meant by
    # triggers "running alongside" the engine, and one of them would have gone unread.
    #
    # Rows recorded before this keep whatever they carry: the collection is not
    # re-validated on read, so an existing value stays visible and is only asked for
    # when somebody next edits that row. Nothing was backfilled, because classifying 24
    # blank rows would be inventing judgements nobody made.
    "change_history": {"label": "Change history", "id_prefix": "CH", "fields": [
        {"key": "version", "label": "Version", "type": "text", "required": True},
        {"key": "date", "label": "Date", "type": "date"},
        {"key": "author", "label": "Author", "type": "text"},
        {"key": "change_type", "label": "Type", "type": "choice",
         "options": CHANGE_CLASSES},
        {"key": "description", "label": "Description", "type": "text"},
    ]},
}

__all__ = ["HISTORY_COLLECTION_SPECS"]
