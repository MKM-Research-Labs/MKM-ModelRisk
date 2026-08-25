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
"""Reading the registers for the dashboard — the I/O half.

Kept apart from the rules, the queue and the summary so all three stay pure and
can be exercised against fixtures. Everything here is a read: the dashboard never
writes, because an executive clearing an item from a screen would be an ungoverned
decision with no minute attached to it.

One completeness scan feeds the whole page. It is the expensive read — it stats
every recorded document to establish that the evidence can actually be produced —
and calling it once is what lets the queue, the operational feed and the direction
feed be three views of one set of facts rather than three opinions of it.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from src.governance.attention import history, position, queue, summary
from src.governance.completeness.scan import (ML_APPLICATION_KIND, MODEL_KIND,
                                              PRODUCT_KIND, ratified_divisions, scan)
from src.governance.ml_application.projection import list_ml_applications
from src.governance.model_inventory.projection import list_models
from src.governance.mrc.projection import matching_mrc, outstanding_actions
from src.governance.product.projection import list_products
from src.governance.reference import get_reference_lists

# Each register, the kind the audit files it under, and the column its id lives in.
# Named once here because the three registers are otherwise identical to this
# module, and a fourth should be one line rather than a fourth branch.
REGISTERS = (
    (MODEL_KIND, list_models, "model_id", "name"),
    (PRODUCT_KIND, list_products, "product_id", "product"),
    (ML_APPLICATION_KIND, list_ml_applications, "ml_application_id", "name"),
)


def records(config=None) -> list[dict[str, Any]]:
    """Every live record on every register, in the one shape the queue reads.

    Retired records are out: both projections exclude them by default, and a
    hibernated model carries no governance obligation anybody is going to meet.
    """
    rows = []
    for kind, lister, id_key, name_key in REGISTERS:
        for row in lister(config=config):
            data = row.get("data") or {}
            rows.append({"kind": kind, "id": row.get(id_key),
                         "name": data.get(name_key) or "", "data": data})
    return rows


def unratified_divisions(config=None) -> list[dict[str, Any]]:
    """Divisions running on a risk policy their own committee never approved.

    The complement of ``ratified_divisions``: ISO 31000 6.3.4 asks the organisation
    to *define* its risk criteria, and inheriting the firm-wide seed is the absence
    of that decision rather than the making of it. Each carries the committee that
    would have to ratify it, so the row names somebody.
    """
    models = list_models(config=config)
    ratified = ratified_divisions(models, config)
    refs = get_reference_lists(config)
    divisions = {(m.get("data") or {}).get("division") for m in models}
    rows = []
    for division in sorted(d for d in divisions if d and d not in ratified):
        committee, _ = matching_mrc(division, None, refs)
        rows.append({
            "division": division,
            "committee": (committee or {}).get("value") or "",
            "chair": (committee or {}).get("chair") or "",
        })
    return rows


def dashboard(as_of: str | None = None, config=None) -> dict[str, Any]:
    """Everything the dashboard and the ERM API serialise, from one set of reads.

    The two surfaces differ in what they *emit*, never in what they *know*: the
    console adds ids for its deep links, the ERM emits the frozen contract, and
    both are shaped from this. That is the only thing guaranteeing the executive's
    screen and the ERM's model-risk tile can never disagree.
    """
    as_of = as_of or date.today().isoformat()
    live = records(config=config)
    audit_rows = scan(as_of, config=config)
    # The finding history, if anything has ever looked. Absent, every finding stays
    # with its owner rather than being called late on an age nobody measured.
    ages = history.ages(as_of, config=config)
    items = queue.build(
        as_of=as_of, records=live, audit_rows=audit_rows,
        committee_actions=outstanding_actions(config=config),
        unratified_divisions=unratified_divisions(config=config), ages=ages)
    return {
        "as_of": as_of,
        "verdict": summary.verdict(items),
        "queue": summary.rows(items),
        "estate": position.estate(live),
        "operational": position.operational(audit_rows, items),
        "direction": position.direction(audit_rows, trend=history.trend(config=config)),
        "items": items,
    }


def observe(as_of: str | None = None, config=None) -> dict:
    """Look once and write down what the audit is reporting.

    Called on a schedule (``src.web._history``), never from a request: the console
    and the ERM surface are reads, and a GET that quietly wrote would make both of
    those claims false.
    """
    as_of = as_of or date.today().isoformat()
    audit_rows = scan(as_of, config=config)
    return history.observe(as_of, audit_rows,
                           position.direction(audit_rows), config=config)
