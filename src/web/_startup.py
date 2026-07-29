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
"""Startup reconciliation: rebuild every read-model from the event log.

The read-models (the ``*_view`` tables) are derived caches, maintained
incrementally as commands are applied. If one drifts out of sync with the event
log — e.g. after a database restore or a data-directory migration, where no
command runs to refresh it — the affected records render blank in the UI even
though the event log, the source of truth, is intact. (This bit in production on
2026-07-29: an MRC meeting appeared deleted because only its view had gone
stale.) Rebuilding every view at startup makes that self-healing — the derived
state is recomputed from the log on each boot, so a stale cache cannot outlive a
restart. The rebuild only ever rewrites cache tables; it never touches the log.

Set ``REBUILD_VIEWS_ON_STARTUP=0`` to skip it (e.g. a deployment large enough
that a full replay per boot is undesirable).
"""
from __future__ import annotations

import importlib
import logging
import os

logger = logging.getLogger(__name__)

_DISABLE_ENV = "REBUILD_VIEWS_ON_STARTUP"

# (label, module, function) for every read-model rebuild. A table rather than
# direct imports so adding a projection is a one-line change and the imports
# stay lazy — a broken feature module cannot take down app startup, and one
# entry per view keeps this list obviously exhaustive.
_REBUILDERS: tuple[tuple[str, str, str], ...] = (
    ("meetings", "src.governance.mrc.projection", "rebuild_meeting_view"),
    ("models", "src.governance.model_inventory.projection", "rebuild_inventory_view"),
    ("handoffs", "src.governance.model_handoff.projection", "rebuild_handoff_view"),
    ("products", "src.governance.product.projection", "rebuild_product_view"),
    ("model_chain", "src.governance.model_chain.projection", "rebuild_model_chain_view"),
    ("data_lineage", "src.governance.data_lineage.projection", "rebuild_data_lineage_view"),
    ("field_lineage", "src.governance.field_lineage.projection", "rebuild_field_lineage_view"),
    ("clients", "src.governance.client.projection", "rebuild_client_view"),
    ("receipts", "src.ingest.receipt.projection", "rebuild_receipts_view"),
)


def reconcile_read_models(config=None) -> dict[str, int]:
    """Rebuild every read-model view from the event log; return ``{label: rows}``.

    Best-effort and isolated: each view is rebuilt independently, and a failure
    in one is logged and skipped rather than aborting startup or the other views
    — serving one stale view is better than refusing to boot. Skipped entirely
    (returns ``{}``) when ``REBUILD_VIEWS_ON_STARTUP`` is set to a falsey value.
    """
    if os.environ.get(_DISABLE_ENV, "1").strip().lower() in ("0", "false", "no", "off"):
        logger.info("read-model rebuild on startup disabled via %s", _DISABLE_ENV)
        return {}

    counts: dict[str, int] = {}
    for label, module_path, func_name in _REBUILDERS:
        try:
            module = importlib.import_module(module_path)
            counts[label] = getattr(module, func_name)(config=config)
        except Exception:  # noqa: BLE001 — one bad view must not break startup
            logger.exception("failed to rebuild the %s read-model", label)
    logger.info("rebuilt read-models from the event log: %s", counts)
    return counts
