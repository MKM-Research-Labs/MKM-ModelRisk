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
"""Build the provenance block stamped on every ingest payload.

Provenance is the collector's BCBS 239 audit trail: it ties a stored artifact
back to the exact repo + commit + producer that generated it. The git commit is
discovered automatically; everything else is supplied by the producer.
"""
from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from typing import Any, Callable


def _git_commit(cwd: str | None = None, runner: Callable[..., Any] = subprocess.run) -> str | None:
    """The current HEAD commit of the repo at ``cwd``, or ``None`` if unavailable."""
    try:
        result = runner(
            ["git", "rev-parse", "HEAD"], cwd=cwd,
            capture_output=True, text=True, check=True,
        )
    except Exception:
        return None
    return result.stdout.strip() or None


def _now_rfc3339() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_provenance(
    *, source_repo: str, producer: str, producer_version: str,
    commit: str | None = None, generated_at: str | None = None,
    cwd: str | None = None,
) -> dict[str, str]:
    """Assemble a provenance block matching the ingest contract's envelope.

    ``commit`` defaults to the repo's current HEAD; ``generated_at`` defaults to
    now (RFC 3339, UTC).
    """
    return {
        "source_repo": source_repo,
        "commit": commit or _git_commit(cwd) or "unknown",
        "producer": producer,
        "producer_version": producer_version,
        "generated_at": generated_at or _now_rfc3339(),
    }
