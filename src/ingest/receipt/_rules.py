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
"""Pure decision logic for the ingest-receipt aggregate.

A receipt is recorded only after a payload has been validated and stored, so the
rule just assembles the ``PayloadIngested`` event. No I/O.
"""
from __future__ import annotations

from typing import Any

from src.ingest.receipt._state import EVENT_INGESTED, ReceiptState


def decide_record(
    state: ReceiptState, *, artifact: str, source_repo: str,
    content_hash: str, provenance: dict[str, Any], summary: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Assemble a ``PayloadIngested`` event for an accepted ingestion."""
    payload = {
        "artifact": artifact,
        "source_repo": source_repo,
        "content_hash": content_hash,
        "provenance": provenance,
        "summary": summary,
    }
    return EVENT_INGESTED, payload
