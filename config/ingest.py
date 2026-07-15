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
    "data-lineage": "data_lineage.schema.json",
    "field-lineage": "field_lineage.schema.json",
    "document": "document.schema.json",
}

# Largest single payload accepted (bytes). Enforced at the HTTP boundary.
MAX_PAYLOAD_BYTES = int(os.environ.get("MKM_INGEST_MAX_BYTES", str(8 * 1024 * 1024)))

# Phase 0 shared-token auth stub. A real API-key / mTLS scheme replaces this
# before any external (e.g. Moody's) producer is onboarded.
INGEST_TOKEN_HEADER = os.environ.get("MKM_INGEST_TOKEN_HEADER", "X-Ingest-Token")
INGEST_DEV_TOKEN = os.environ.get("MKM_INGEST_DEV_TOKEN", "dev-ingest-token")
