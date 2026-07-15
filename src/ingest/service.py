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
"""The generic ingest pipeline.

``ingest_payload`` is the single entry point the HTTP layer calls: validate the
envelope, validate the artifact payload (schema + cross-refs), attribute it to a
synthetic producer principal, store it via the artifact's write-domain, and
record a receipt. It returns ``(receipt, created)`` — ``created`` is ``False``
when the payload was byte-identical to the last one (idempotent no-op).
"""
from __future__ import annotations

from typing import Any, Callable

from src.governance.data_lineage import ingest_data_lineage, rebuild_data_lineage_view
from src.identity import ingest_principal
from src.ingest._envelope import content_hash
from src.ingest._validate import (
    SchemaValidationError,
    validate_envelope,
    validate_payload,
)
from src.ingest.receipt import get_receipt, rebuild_receipts_view, record_receipt


def _ingest_data_lineage(
    payload: dict[str, Any], provenance: dict[str, Any], actor: str, config,
) -> tuple[dict[str, Any] | None, bool]:
    source_repo = provenance["source_repo"]
    chash = content_hash(payload)
    event = ingest_data_lineage(
        source_repo=source_repo, manifest=payload, provenance=provenance,
        content_hash=chash, actor=actor, reason="ingest data-lineage", config=config,
    )
    if event is None:  # idempotent: identical manifest already stored
        return get_receipt("data-lineage", source_repo, config=config), False
    rebuild_data_lineage_view(config=config)
    summary = {
        "run_count": event.payload["run_count"],
        "step_count": event.payload["step_count"],
        "manifest_seq": event.global_seq,
    }
    record_receipt(
        artifact="data-lineage", source_repo=source_repo, content_hash=chash,
        provenance=provenance, summary=summary, actor=actor,
        reason="ingest data-lineage", config=config,
    )
    rebuild_receipts_view(config=config)
    return get_receipt("data-lineage", source_repo, config=config), True


# artifact -> handler(payload, provenance, actor, config) -> (receipt, created).
# Only wired artifacts are reachable; others 422 via the guard below.
_HANDLERS: dict[str, Callable[..., tuple[dict[str, Any] | None, bool]]] = {
    "data-lineage": _ingest_data_lineage,
}


def ingest_payload(
    artifact: str, body: Any, *, config=None,
) -> tuple[dict[str, Any] | None, bool]:
    """Validate and store one ingest request; return ``(receipt, created)``."""
    validate_envelope(body)
    handler = _HANDLERS.get(artifact)
    if handler is None:
        raise SchemaValidationError(
            f"artifact '{artifact}' has no ingest handler",
            [f"'{artifact}' is not wired for ingestion"],
        )
    payload = body["payload"]
    provenance = body["provenance"]
    validate_payload(artifact, payload)
    actor = ingest_principal(provenance).actor
    return handler(payload, provenance, actor, config)
