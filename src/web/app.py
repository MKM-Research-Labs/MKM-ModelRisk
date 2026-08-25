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
from src.governance.errors import DomainError
from src.identity import UnrecognisedActor
from src.ingest import SchemaValidationError
from src.web.api_audit import audit_bp
from src.web.api_artefacts import artefacts_bp
from src.web.api_audit_reports import audit_reports_bp
from src.web.api_client import client_bp
from src.web.api_dashboard import dashboard_bp
from src.web.api_documents import documents_bp
from src.web.api_erm import erm_bp
from src.web.api_handoffs import handoffs_bp
from src.web.api_models import models_bp
from src.web import api_models_signoff  # noqa: F401 — attaches endpoints to models_bp
from src.web import api_models_review  # noqa: F401 — attaches endpoints to models_bp
from src.web import api_models_review_notes  # noqa: F401 — same blueprint
from src.web import api_models_review_signoff  # noqa: F401 — same blueprint
from src.web import api_model_documents  # noqa: F401 — attaches endpoints to models_bp
from src.web.api_mrc import mrc_bp
from src.web.api_mrc_settings import settings_bp
from src.web.api_ml_application import ml_application_bp
from src.web import api_ml_application_documents  # noqa: F401 — attaches endpoints to ml_application_bp
from src.web import api_ml_application_signoff  # noqa: F401 — attaches endpoints to ml_application_bp
from src.web.api_product import product_bp
from src.web import api_product_signoff  # noqa: F401 — attaches endpoints to product_bp
from src.web import api_product_risk  # noqa: F401 — attaches endpoints to product_bp
from src.web import api_product_documents  # noqa: F401 — attaches endpoints to product_bp
from src.web.api_ingest import ingest_bp
from src.web.api_reference import reference_bp
from src.web.api_theme import theme_bp
from src.web.api_risk_policy import risk_policy_bp
from src.web.api_vendor_documents import vendor_documents_bp
from src.web.views import views_bp
from src.web._startup import bootstrap


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

    # An unregistered identity may not author a change (permissions P1). 403 rather than
    # 401: the caller is authenticated as far as the perimeter is concerned — the
    # institution simply does not know who that is.
    @app.errorhandler(UnrecognisedActor)
    def _unrecognised_actor(exc: UnrecognisedActor):
        return jsonify({"error": str(exc), "unrecognised_actor": True}), 403


def create_app(run_db_migrations: bool = True) -> Flask:
    """Build the Flask app. Applies DB migrations unless told not to.

    ``run_db_migrations`` covers all the one-time startup work — migrations, the
    seeded admin defaults, and the read-model rebuild (see
    ``src/web/_startup.py``). Pass ``False`` when something else has already
    done it: the test suites do, and so does ``wsgi.py``, where the gunicorn
    master bootstraps once before forking rather than every worker racing.
    """
    if run_db_migrations:
        bootstrap()
    # Front-end assets live under src/static and src/templates (coding rule R7).
    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.register_blueprint(views_bp)
    app.register_blueprint(theme_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(models_bp)
    app.register_blueprint(handoffs_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(ml_application_bp)
    app.register_blueprint(client_bp)
    app.register_blueprint(mrc_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(reference_bp)
    app.register_blueprint(risk_policy_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(artefacts_bp)
    app.register_blueprint(vendor_documents_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(audit_reports_bp)
    app.register_blueprint(ingest_bp)
    app.register_blueprint(erm_bp)
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
