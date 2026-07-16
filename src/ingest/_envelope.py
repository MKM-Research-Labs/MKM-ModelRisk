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
"""Envelope helpers: canonical hashing of a payload (pure, no I/O).

The content hash is the idempotency key: a re-pushed byte-identical payload
hashes the same, so the collector can no-op it. Hashing is over a canonical JSON
encoding (sorted keys, no insignificant whitespace) so key ordering never changes
the hash.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(payload: Any) -> str:
    """Deterministic JSON encoding used for hashing."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def content_hash(payload: Any) -> str:
    """SHA-256 hex digest of a payload's canonical JSON encoding."""
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
