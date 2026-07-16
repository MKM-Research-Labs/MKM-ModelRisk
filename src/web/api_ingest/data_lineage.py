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
