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
"""One-time startup work: schema migrations, seeded defaults, read-model rebuild.

``bootstrap()`` is everything that must happen once before the app serves a
request, and — importantly — **once per boot, not once per worker**. Under the
development server that distinction does not arise; under gunicorn it very much
does, which is why this is a callable the master can run before it forks rather
than something buried in ``create_app``. See ``bootstrap()`` for what goes wrong
if several workers run it at the same time.

The read-model rebuild that ``bootstrap()`` finishes with is the delicate part,
and has its own history:

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

from config.web import BOOTSTRAP_DONE_ENV

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


def bootstrap(config=None) -> None:
    """Apply migrations, seed the admin-managed defaults, rebuild the read-models.

    Run this **once per boot**. Under gunicorn that means the master process,
    before it forks, with the workers building their app with
    ``create_app(run_db_migrations=False)``.

    Concurrent runs are not merely wasteful, they are unsafe. ``run_migrations``
    reads the applied set and applies the rest in a single transaction with no
    lock held, so two workers starting together both see a migration as pending,
    both execute its DDL, and the loser blocks on the ``schema_migrations``
    primary key until the winner commits and then dies on a unique violation —
    a worker that crashes on boot for no visible reason. The full read-model
    replay behind it would likewise run once per worker.
    """
    from src.database import run_migrations
    from src.governance.reference import (ensure_default_estimators,
                                          ensure_default_ml_application_questions,
                                          ensure_default_ml_training_vocabularies,
                                          ensure_default_model_types,
                                          ensure_default_reference_lists,
                                          ensure_default_review_questions,
                                          ensure_default_standing_agenda,
                                          ensure_default_status_vocabularies)

    run_migrations(config)
    # Model types are admin-managed, but an empty list degrades the field to
    # free text — so a fresh database is given the defaults once.
    ensure_default_model_types()
    # Data source + vendor lists back the model's data_sources / vendor fields;
    # seed their defaults on a fresh database for the same reason.
    ensure_default_reference_lists()
    ensure_default_review_questions()
    ensure_default_standing_agenda()
    ensure_default_status_vocabularies()
    # The Estimator menu and the ML Application questionnaire: the same "seed a
    # vacuum" rule, for the ML side of the estate.
    ensure_default_estimators()
    ensure_default_ml_application_questions()
    ensure_default_ml_training_vocabularies()
    reconcile_read_models(config)


def bootstrap_once(config=None) -> bool:
    """Run :func:`bootstrap` unless a parent process already did.

    Returns whether the work was actually done. The marker is an environment
    variable because that is what survives ``fork`` — the gunicorn master sets
    it after bootstrapping and every worker inherits it, without the two ever
    needing to talk to each other.
    """
    if os.environ.get(BOOTSTRAP_DONE_ENV) == "1":
        logger.info("startup work already done by a parent process; skipping")
        return False
    bootstrap(config)
    os.environ[BOOTSTRAP_DONE_ENV] = "1"
    return True


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
