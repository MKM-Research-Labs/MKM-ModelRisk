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
"""Startup read-model reconciliation rebuilds every view from the event log."""
from __future__ import annotations

import re

from audit._walk import REPO_ROOT
from src.database import append_event
from src.governance.mrc.projection import get_meeting
from src.web._startup import _REBUILDERS, reconcile_read_models

_REBUILD_DEF = re.compile(r"^def (rebuild_\w+_view)\b", re.MULTILINE)


def _defined_rebuilders() -> set[str]:
    """Every ``rebuild_*_view`` the source tree defines, found by reading it.

    Deliberately not by import: ``_REBUILDERS`` names its modules as strings so the
    imports stay lazy, and a test that imported them all to find the functions would
    lose the very property that keeps a broken feature module from taking down startup.
    """
    return {match.group(1)
            for path in REPO_ROOT.glob("src/**/projection.py")
            for match in _REBUILD_DEF.finditer(path.read_text(encoding="utf-8"))}


def test_every_defined_rebuilder_is_registered_for_startup():
    """No projection may define a rebuild and be left out of ``_REBUILDERS``.

    ``ml_application`` was exactly that for as long as the record type existed: its
    migration and its ``rebuild_ml_application_view`` were both in place, but nothing
    reconciled the view at startup, so it could drift from the event log and present
    as data loss when the log was intact. The comparison below is against the source
    tree rather than against ``_REBUILDERS`` itself -- the test above compares that
    list with its own labels, which can never catch something missing from it.
    """
    registered = {func for _label, _module, func in _REBUILDERS}
    assert _defined_rebuilders() - registered == set()


def test_reconcile_rebuilds_every_registered_view():
    """It rebuilds each registered view and returns a count per label."""
    result = reconcile_read_models()
    assert set(result) == {label for label, _module, _fn in _REBUILDERS}
    assert all(isinstance(n, int) for n in result.values())


def test_reconcile_repopulates_a_stale_meeting_view():
    """An event with no command-driven view update is picked up on reconcile.

    Appending straight to the log leaves the ``mrc_meeting_view`` cache untouched
    (no command ran), so the meeting is absent from the read model until a rebuild
    — exactly the drift that made an intact meeting look deleted in production.
    """
    append_event(
        aggregate_type="MRCMeeting",
        aggregate_id="MTG-RECON-TEST",
        event_type="MeetingScheduled",
        payload={"meeting_id": "MTG-RECON-TEST", "title": "Reconcile Test",
                 "date": "2030-01-01", "status": "Scheduled", "mrc": "MRC-PR"},
        actor="system",
    )
    assert get_meeting("MTG-RECON-TEST") is None  # cache not yet built

    reconcile_read_models()

    meeting = get_meeting("MTG-RECON-TEST")
    assert meeting is not None
    assert meeting["data"]["title"] == "Reconcile Test"
