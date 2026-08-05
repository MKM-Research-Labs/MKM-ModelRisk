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
"""Flask application factory for the MKM-ModelRisk governance console."""
from __future__ import annotations

from flask import Flask, jsonify, request

from src.command import ConfirmationRequired
from src.database import run_migrations
from src.governance.errors import DomainError
from src.governance.reference import (ensure_default_model_types,
                                      ensure_default_reference_lists)
from src.ingest import SchemaValidationError
from src.web.api_audit import audit_bp
from src.web.api_audit_reports import audit_reports_bp
from src.web.api_client import client_bp
from src.web.api_documents import documents_bp
from src.web.api_handoffs import handoffs_bp
from src.web.api_models import models_bp
from src.web import api_models_signoff  # noqa: F401 — attaches endpoints to models_bp
from src.web import api_model_documents  # noqa: F401 — attaches endpoints to models_bp
from src.web.api_mrc import mrc_bp
from src.web.api_mrc_settings import settings_bp
from src.web.api_product import product_bp
from src.web import api_product_signoff  # noqa: F401 — attaches endpoints to product_bp
from src.web import api_product_risk  # noqa: F401 — attaches endpoints to product_bp
from src.web import api_product_documents  # noqa: F401 — attaches endpoints to product_bp
from src.web.api_ingest import ingest_bp
from src.web.api_reference import reference_bp
from src.web.api_risk_policy import risk_policy_bp
from src.web.views import views_bp
from src.web._startup import reconcile_read_models


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(DomainError)
    def _domain_error(exc: DomainError):
        return jsonify({"error": str(exc)}), 400

    @app.errorhandler(ConfirmationRequired)
    def _confirmation_required(exc: ConfirmationRequired):
        return jsonify({"error": str(exc), "needs_confirmation": True}), 409

    @app.errorhandler(SchemaValidationError)
    def _schema_validation_error(exc: SchemaValidationError):
        return jsonify({"error": str(exc), "details": exc.errors}), 422


def create_app(run_db_migrations: bool = True) -> Flask:
    """Build the Flask app. Applies DB migrations unless told not to."""
    if run_db_migrations:
        run_migrations()
        # Model types are admin-managed, but an empty list degrades the field to
        # free text — so a fresh database is given the defaults once.
        ensure_default_model_types()
        # Data source + vendor lists back the model's data_sources / vendor
        # fields; seed their defaults on a fresh database for the same reason.
        ensure_default_reference_lists()
        # Read-models are derived caches maintained incrementally on writes; if one
        # drifts out of sync with the event log (e.g. after a restore or a data-dir
        # migration, where no command runs to refresh it) intact records render
        # blank. Recompute them from the log on startup so a stale cache self-heals
        # instead of masquerading as data loss. Rewrites only cache tables, never
        # the log; set REBUILD_VIEWS_ON_STARTUP=0 to skip. See src/web/_startup.py.
        reconcile_read_models()
    # Front-end assets live under src/static and src/templates (coding rule R7).
    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.register_blueprint(views_bp)
    app.register_blueprint(models_bp)
    app.register_blueprint(handoffs_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(client_bp)
    app.register_blueprint(mrc_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(reference_bp)
    app.register_blueprint(risk_policy_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(audit_reports_bp)
    app.register_blueprint(ingest_bp)
    _register_error_handlers(app)

    # Never cache the front-end assets: the console is a single-page app whose
    # JS/CSS change often, and a stale cached bundle silently breaks buttons
    # (edit/remove/etc.) because the old handlers no longer match the new DOM.
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    @app.after_request
    def _no_store_static(response):
        if request.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-store, max-age=0"
        return response

    return app
