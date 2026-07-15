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
