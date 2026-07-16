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
"""Resolve the acting principal from trusted SSO request headers.

Pluggable seam: the only thing the rest of the app needs is a ``Principal``.
Today that comes from perimeter-SSO headers; a different identity source can be
swapped in here without touching command handlers.
"""
from __future__ import annotations

from typing import Any, Mapping

from config.identity import (
    IDENTITY_DEV_FALLBACK,
    IDENTITY_HEADER,
    IDENTITY_NAME_HEADER,
)
from src.identity._principal import (
    SOURCE_FALLBACK,
    SOURCE_INGEST,
    SOURCE_SSO_HEADER,
    Principal,
)


class IdentityError(RuntimeError):
    """Raised when no authenticated principal is present and none is allowed."""


def _lookup(headers: Mapping[str, str], name: str) -> str | None:
    """Case-insensitive header lookup (HTTP header names are case-insensitive)."""
    target = name.lower()
    for key, value in headers.items():
        if key.lower() == target:
            return value
    return None


def resolve_principal(
    headers: Mapping[str, str], *, allow_fallback: bool = True
) -> Principal:
    """Build a ``Principal`` from request headers.

    When the trusted identity header is absent and ``allow_fallback`` is set, a
    local development actor is returned; otherwise an ``IdentityError`` is raised.
    """
    actor = _lookup(headers, IDENTITY_HEADER)
    if actor:
        name = _lookup(headers, IDENTITY_NAME_HEADER) or actor
        return Principal(actor=actor, display_name=name, source=SOURCE_SSO_HEADER)
    if not allow_fallback:
        raise IdentityError("no authenticated principal in request")
    return Principal(
        actor=IDENTITY_DEV_FALLBACK,
        display_name=IDENTITY_DEV_FALLBACK,
        source=SOURCE_FALLBACK,
    )


def ingest_principal(provenance: Mapping[str, Any]) -> Principal:
    """A synthetic principal attributing an ingested payload to its source system.

    ``actor`` is ``ingest:<source_repo>`` so a producer's events are unmistakably
    machine-originated in the audit trail; ``display_name`` names the producer.
    """
    repo = provenance["source_repo"]
    producer = provenance.get("producer") or repo
    return Principal(actor=f"ingest:{repo}", display_name=producer, source=SOURCE_INGEST)
