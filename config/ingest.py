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
"""Ingest parameters (coding rule R1).

The collector accepts producer payloads at ``/api/ingest/*`` against the frozen
v1 contract (``contracts/ingest/v1``). ``INGEST_ARTIFACTS`` maps each accepted
artifact to the schema its payload is validated against; only artifacts wired to
a handler in :mod:`src.ingest.service` are actually reachable end-to-end.
"""
from __future__ import annotations

import os

# The contract version this collector speaks.
CONTRACT_VERSION = "v1"

# artifact name -> schema file under contracts/ingest/<CONTRACT_VERSION>/.
INGEST_ARTIFACTS = {
    "model-inventory": "model_inventory.schema.json",
    "model-chain": "model_chain.schema.json",
    "data-lineage": "data_lineage.schema.json",
    "field-lineage": "field_lineage.schema.json",
    "document": "document.schema.json",
    "ml-training-run": "ml_training_run.schema.json",
}

# Largest single payload accepted (bytes). Enforced at the HTTP boundary.
MAX_PAYLOAD_BYTES = int(os.environ.get("INGEST_MAX_BYTES", str(8 * 1024 * 1024)))

# Phase 0 shared-token auth stub. A real API-key / mTLS scheme replaces this
# before any external producer is onboarded.
INGEST_TOKEN_HEADER = os.environ.get("INGEST_TOKEN_HEADER", "X-Ingest-Token")
INGEST_DEV_TOKEN = os.environ.get("INGEST_DEV_TOKEN", "dev-ingest-token")
