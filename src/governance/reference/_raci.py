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
"""The RACI role list: seeding it, and reading what a new Product is scaffolded with."""
from __future__ import annotations

from config.governance._raci import DEFAULT_RACI, RACI_ROLE_LIST, VALID_RACI_CODES
from config.identity import SYSTEM_ACTOR
from src.governance.reference._store import get_reference_lists, load
from src.governance.reference.commands import add_option


def _roles_in_use(config) -> list[str]:
    """Every role a model or Product RACI entry already carries, first seen first.

    The role was free text before the list existed, so the estate holds words of its
    own. Each becomes an entry storing exactly that word: it stays pickable and can be
    renamed in Admin, rather than surviving only as a value nobody can choose again.
    """
    from src.governance.model_inventory import list_models  # lazy: import cycle
    from src.governance.product import list_products
    records = (list_models(config=config, include_retired=True)
               + list_products(config=config))
    seen: dict[str, None] = {}
    for record in records:
        for entry in (record.get("data") or {}).get("raci_roles") or ():
            role = str(entry.get("role") or "").strip() if isinstance(entry, dict) else ""
            if role:
                seen.setdefault(role)
    return list(seen)


def ensure_default_raci_roles(*, actor: str = SYSTEM_ACTOR, config=None) -> int:
    """Seed the RACI role list on first run; return how many were added.

    The four roles Products were scaffolded with before the list existed, each marked
    with its accountability, then any other role already on record, unmarked. Every
    stored value equals the word the estate carries, so nothing has to migrate. Seeds
    a vacuum, never reconciles a list somebody has since curated.
    """
    collections, _ = load(config)
    if collections.get(RACI_ROLE_LIST):
        return 0
    rows = [{"label": role, "value": role, "raci": raci} for raci, role in DEFAULT_RACI]
    shipped = {role for _raci, role in DEFAULT_RACI}
    rows += [{"label": role, "value": role}
             for role in _roles_in_use(config) if role not in shipped]
    for fields in rows:
        add_option(list_name=RACI_ROLE_LIST, fields=fields, actor=actor,
                   reason="Seed the RACI roles on first run", config=config)
    return len(rows)


def raci_seed_items(config=None) -> list[dict]:
    """The RACI entries a newly registered Product starts with, from the admin list.

    One entry per role marked with an accountability, in R/A/C/I order. A list that
    has never been seeded falls back to what it would be seeded with, so registration
    on such a database still scaffolds the four accountabilities.
    """
    roles = get_reference_lists(config).get(RACI_ROLE_LIST) or [
        {"value": role, "raci": raci} for raci, role in DEFAULT_RACI]
    return [{"role": item["value"], "raci": raci}
            for raci in VALID_RACI_CODES
            for item in roles if item.get("raci") == raci and item.get("value")]
