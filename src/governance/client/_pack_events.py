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
"""The operational-event write-ups PDF carried inside a client pack.

Pure ``build_event_writeups_tex`` (products + settings -> LaTeX); ``render_*``
compiles it with tectonic in the shared house style.
"""
from __future__ import annotations

from typing import Any

from src.governance.latex import (
    _para_table, _section, front_matter, history_page, logo_asset, preamble,
)
from src.governance.mrc import pack


def event_rows(products: list[dict]) -> list[list[Any]]:
    """One row per operational-failure event across every product, newest first."""
    rows: list[list[Any]] = []
    for product in products:
        product_id = product.get("product_id")
        for event in (product.get("data") or {}).get("operational_failure_events") or []:
            rows.append([
                product_id, event.get("date"), event.get("description"),
                event.get("remediation"), event.get("mrc_status") or "--",
                event.get("review_comments") or "--",
            ])
    rows.sort(key=lambda r: str(r[1] or ""), reverse=True)
    return rows


def build_event_writeups_tex(products: list[dict], settings: dict, as_of: str,
                             logo: bool = False) -> str:
    """Render the LaTeX source for the operational-event write-ups."""
    org = (settings.get("fields") or {}).get("org_name", "")
    rows = event_rows(products)
    # Column layout for the event table: the "what happened" and remediation
    # narratives get the width; the identifiers and status flags stay narrow.
    body = (_para_table(
        ["Product", "Date", "What happened", "Remediation", "MRC status", "MRC comments"],
        rows, [0.13, 0.10, 0.29, 0.19, 0.12, 0.17],
        caption="Operational failure events across linked products") if rows
            else "No operational events have been recorded across the linked products.")
    return (
        preamble("Operational Event Write-ups", org_name=org) + "\\begin{document}\n"
        + front_matter("Operational Event Write-ups", "Client Pack", org_name=org,
                       date=as_of, logo=logo)
        + _section("Operational events", body)
        + history_page(as_of, "Client pack event write-ups generated", org_name=org)
        + "\\end{document}\n"
    )


def render_event_writeups_pdf(products: list[dict], settings: dict, as_of: str) -> bytes:
    """Build and compile the operational-event write-ups to PDF bytes."""
    assets = logo_asset(settings)
    return pack.compile_tex(
        build_event_writeups_tex(products, settings, as_of, logo=bool(assets)), assets)
