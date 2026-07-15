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
"""Data-lineage ingest endpoint.

A producer POSTs the ingest envelope; the spine validates it, stores the manifest,
and records a receipt. Validation failures raise ``SchemaValidationError``, mapped
to HTTP 422 by the app error handler.
"""
from __future__ import annotations

from flask import jsonify

from src.ingest import ingest_payload
from src.web._helpers import json_body
from src.web.api_ingest._bp import ingest_bp


@ingest_bp.post("/data-lineage")
def ingest_data_lineage():
    """Ingest a data-lineage manifest. 201 when stored, 200 when idempotent."""
    receipt, created = ingest_payload("data-lineage", json_body())
    return jsonify(receipt), (201 if created else 200)
