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
"""The data-source catalogue, and getting it onto an estate that predates it.

Two things are worth holding here. The catalogue must stay a list of NAMED providers
rather than drifting back into categories -- "Market data" as a data source tells a
reviewer nothing about provenance. And the backfill must never overrule a curator: a
source somebody deleted stays deleted, and a kind somebody set stays theirs.
"""
from __future__ import annotations

from config.governance import DATA_SOURCE_LIST, DEFAULT_DATA_SOURCES
from scripts.backfill_data_sources import backfill_data_sources
from src.governance.reference import add_option, get_reference_lists, update_option


def _values() -> list[str]:
    return [row["value"] for row in get_reference_lists()[DATA_SOURCE_LIST]]


def _row(value: str) -> dict:
    return next(r for r in get_reference_lists()[DATA_SOURCE_LIST]
                if r["value"] == value)


# --- The catalogue -----------------------------------------------------------

def test_every_entry_names_a_provider_and_declares_its_kind():
    for entry in DEFAULT_DATA_SOURCES:
        assert entry["value"].strip(), "an entry with no name is not a source"
        assert entry["kind"] in ("Internal", "External")


def test_sensitivity_and_egress_are_left_to_the_institution():
    """What a firm considers confidential, and what its contract permits leaving, are
    its own judgements — the same reason the estimator seed carries no versions."""
    for entry in DEFAULT_DATA_SOURCES:
        assert set(entry) == {"value", "kind"}


def test_the_catalogue_reaches_past_market_data():
    """A catalogue that stops at Bloomberg cannot describe a flood model's provenance,
    and physical risk is a first-class use of this platform."""
    values = {entry["value"] for entry in DEFAULT_DATA_SOURCES}
    assert {"Bloomberg", "ICE", "Reuters"} <= values
    assert {"Met Office", "NOAA", "ECMWF"} <= values


def test_simulated_and_manual_are_first_class_internal_sources():
    """Not placeholders for a feed nobody has named yet. A stochastic event set is the
    input to a catastrophe model, and on this estate it is the common case."""
    kinds = {entry["value"]: entry["kind"] for entry in DEFAULT_DATA_SOURCES}
    assert kinds["Simulated"] == "Internal"
    assert kinds["Manual"] == "Internal"


def test_no_duplicate_names():
    values = [entry["value"].casefold() for entry in DEFAULT_DATA_SOURCES]
    assert len(values) == len(set(values))


# --- The backfill ------------------------------------------------------------

def test_an_empty_list_is_left_to_the_first_run_seed():
    assert "list empty" in backfill_data_sources()
    assert get_reference_lists().get(DATA_SOURCE_LIST) in (None, [])


def test_it_adds_only_what_is_missing_and_is_idempotent():
    add_option(list_name=DATA_SOURCE_LIST, fields={"value": "Simulated"}, actor="admin")
    result = backfill_data_sources()

    assert "added" in result
    assert _values() == ["Simulated"] + [e["value"] for e in DEFAULT_DATA_SOURCES
                                         if e["value"] != "Simulated"]
    assert "nothing to do" in backfill_data_sources()


def test_re_running_after_a_deletion_puts_it_back():
    """The honest limit of this script, asserted so nobody mistakes it for a seed.

    A reference list keeps no record of a removal, so the backfill cannot tell "never
    had it" from "deleted it on purpose". That is why it is a script an operator runs
    once and deliberately, rather than anything that fires at startup — the first-run
    seed's promise never to repopulate a curated list is NOT a promise this one makes.
    """
    add_option(list_name=DATA_SOURCE_LIST, fields={"value": "Manual"}, actor="admin")
    backfill_data_sources()
    from src.governance.reference import remove_option
    remove_option(list_name=DATA_SOURCE_LIST, item_id=_row("Met Office")["item_id"],
                  actor="admin")
    assert "Met Office" not in _values()

    backfill_data_sources()
    assert "Met Office" in _values()


def test_a_blank_kind_is_filled_but_a_set_one_is_never_overwritten():
    add_option(list_name=DATA_SOURCE_LIST, fields={"value": "Simulated"}, actor="admin")
    add_option(list_name=DATA_SOURCE_LIST, fields={"value": "Bloomberg",
                                                   "kind": "Internal"}, actor="admin")
    backfill_data_sources()

    # Blank was an absence, so the catalogue's answer fills it.
    assert _row("Simulated")["kind"] == "Internal"
    # Set was a decision, so it stands — even though the catalogue disagrees.
    assert _row("Bloomberg")["kind"] == "Internal"


def test_matching_ignores_case_and_spacing():
    """"met  office" is the Met Office, and adding a second row would break the strict
    reference the whole list exists to provide."""
    add_option(list_name=DATA_SOURCE_LIST, fields={"value": "met  office"},
               actor="admin")
    backfill_data_sources()
    assert len([v for v in _values() if v.casefold().replace(" ", "")
                == "metoffice"]) == 1


def test_it_reports_what_it_did():
    add_option(list_name=DATA_SOURCE_LIST, fields={"value": "Simulated"}, actor="admin")
    result = backfill_data_sources()
    assert "Met Office" in result and "Simulated (Internal)" in result
