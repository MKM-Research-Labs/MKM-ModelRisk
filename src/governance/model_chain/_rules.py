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
"""Pure decision logic for the model-chain aggregate.

Payload shape and graph integrity are already checked at the ingest boundary, so
the rule here just assembles the event to append (with the derived link count).
No I/O.
"""
from __future__ import annotations

from typing import Any

from src.governance.errors import DomainError
from src.governance.model_chain._state import EVENT_INGESTED, ChainState


def decide_ingest(
    state: ChainState, *, chain: dict[str, Any],
    provenance: dict[str, Any], content_hash: str,
) -> tuple[str, dict[str, Any]]:
    """Assemble a ``ModelChainIngested`` event for the pushed chain."""
    if not isinstance(chain, dict):
        raise DomainError("chain must be an object")
    payload = {
        "chain": chain,
        "provenance": provenance,
        "content_hash": content_hash,
        "link_count": len(chain.get("links", [])),
    }
    return EVENT_INGESTED, payload
