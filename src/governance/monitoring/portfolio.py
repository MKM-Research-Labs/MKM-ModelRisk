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
"""Reading the producing repo's port output: what portfolios exist to monitor.

Port generates a portfolio per catchment. This module reports what it left
behind — which catchments hold a portfolio, how many records of each kind, and
when it was written — so a monitoring document states observed activity rather
than asserting it.

A catchment directory holds many derived variants of the same population
(``propertybri``, ``propertybaw``, …), each one model's view of it. Only the
files named in ``PORTFOLIO_FILES`` are counted, so the population is reported
once rather than once per lens.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from config.governance import PORTFOLIO_FILES
from config.paths import PRODUCER_PORTFOLIO_DIR


def _record_count(payload: Any) -> int:
    """How many records a portfolio file holds.

    The files are not uniformly shaped: some are a bare list, others an object
    wrapping the list beside metadata. Taking the longest contained list finds
    the population in both without the reader needing a schema per file.
    """
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        lists = [len(v) for v in payload.values() if isinstance(v, list)]
        return max(lists) if lists else len(payload)
    return 0


def _read(path: Path) -> tuple[int, str] | None:
    """``(records, iso date)`` for one portfolio file, or None if unreadable.

    An unreadable file is skipped rather than fatal: a monitoring document that
    reports the catchments it could read is more useful than one that refuses to
    generate because a single artefact is malformed.
    """
    try:
        with path.open() as handle:
            # R6 flags .json I/O under src/ because this platform's own state
            # persists through Postgres. This is not that: it reads an artefact
            # the *producing* repo wrote, the same way the phys migration reads
            # PRODUCER_INVENTORY. Nothing here is platform state.
            payload = json.load(handle)
    except (OSError, ValueError):
        return None
    written = date.fromtimestamp(path.stat().st_mtime).isoformat()
    return _record_count(payload), written


def catchments(root: Path | None = None) -> list[dict[str, Any]]:
    """Every catchment under the port output, with its portfolio contents.

    Catchments with no portfolio are still returned, carrying an empty
    ``populations``: an empty catchment is an observation, and dropping it would
    leave the reader unable to tell it from one that was never run.
    """
    base = Path(root or PRODUCER_PORTFOLIO_DIR)
    if not base.is_dir():
        return []
    found = []
    for directory in sorted(p for p in base.iterdir() if p.is_dir()):
        populations, written = [], []
        for filename, label in PORTFOLIO_FILES:
            result = _read(directory / filename)
            if result is None:
                continue
            count, stamp = result
            populations.append({"label": label, "records": count, "written": stamp})
            written.append(stamp)
        found.append({
            "catchment": directory.name,
            "populations": populations,
            "records": sum(p["records"] for p in populations),
            # The most recent file in the catchment: a portfolio is written as a
            # set, so the newest of them is when that catchment was last built.
            "last_built": max(written) if written else "",
        })
    return found


def summary(found: list[dict]) -> dict[str, Any]:
    """Estate-level totals: what the monitoring population actually is."""
    populated = [c for c in found if c["populations"]]
    return {
        "catchments": len(found),
        "populated": len(populated),
        "records": sum(c["records"] for c in populated),
        "last_built": max((c["last_built"] for c in populated), default=""),
    }
