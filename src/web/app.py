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
"""Flask application factory for the MKM-ModelRisk governance console."""
from __future__ import annotations

from flask import Flask, jsonify, request

from src.command import ConfirmationRequired
from src.database import run_migrations
from src.governance.errors import DomainError
from src.web.api_audit import audit_bp
from src.web.api_audit_reports import audit_reports_bp
from src.web.api_bibliography import bib_bp
from src.web.api_documents import documents_bp
from src.web.api_models import models_bp
from src.web import api_models_signoff  # noqa: F401 — attaches endpoints to models_bp
from src.web.api_mrc import mrc_bp
from src.web.api_mrc_settings import settings_bp
from src.web.api_product import product_bp
from src.web import api_product_signoff  # noqa: F401 — attaches endpoints to product_bp
from src.web.api_reference import reference_bp
from src.web.views import views_bp


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(DomainError)
    def _domain_error(exc: DomainError):
        return jsonify({"error": str(exc)}), 400

    @app.errorhandler(ConfirmationRequired)
    def _confirmation_required(exc: ConfirmationRequired):
        return jsonify({"error": str(exc), "needs_confirmation": True}), 409


def create_app(run_db_migrations: bool = True) -> Flask:
    """Build the Flask app. Applies DB migrations unless told not to."""
    if run_db_migrations:
        run_migrations()
    # Front-end assets live under src/static and src/templates (coding rule R7).
    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.register_blueprint(views_bp)
    app.register_blueprint(models_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(mrc_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(reference_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(bib_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(audit_reports_bp)
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
