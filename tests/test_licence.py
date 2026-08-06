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
"""The licensing artefacts must survive, and must agree with each other.

Two files carry the licence, and both are handover artefacts:

* ``LICENSE`` — the grant that ships with the code.
* ``docs/shared/copyright.py`` — the canonical block every source file's header
  is copied from.

They have gone missing from the working tree once. Losing either is quiet and
expensive: without ``LICENSE`` the code ships with no stated grant, and without
the template there is nothing to copy a header from. Worse than either is the
two drifting apart, which would leave every file's header claiming something the
LICENSE does not say. These tests make any of that a named failure — they are
about the licence itself, not about which files carry a header (R5 is checked by
hand, not by the audit).
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LICENCE = REPO_ROOT / "LICENSE"
HEADER_TEMPLATE = REPO_ROOT / "docs" / "shared" / "copyright.py"

# Sentences that identify the MIT grant in both files.
GRANT = "Permission is hereby granted, free of charge, to any person obtaining a copy"
CONDITION = "The above copyright notice and this permission notice shall be included in all"
HOLDER = "Copyright (c) 2022-2026 MKM Research Labs"


def _uncommented(text: str) -> str:
    """The header template's prose, with its leading ``#`` markers removed."""
    return "\n".join(line.lstrip("#").strip() for line in text.splitlines())


def test_licence_file_is_present_and_states_mit():
    assert LICENCE.is_file(), "LICENSE is missing — the code would ship with no stated grant"
    text = LICENCE.read_text(encoding="utf-8")
    assert "MIT License" in text
    assert HOLDER in text
    assert GRANT in text


def test_header_template_is_present():
    assert HEADER_TEMPLATE.is_file(), (
        "docs/shared/copyright.py is missing — audit R5 stamps every file from it "
        "and cannot run without it"
    )
    assert HEADER_TEMPLATE.read_text(encoding="utf-8").startswith("# Copyright (c)")


def test_header_template_states_the_same_licence_as_the_licence_file():
    """Every file's header comes from the template, so it must not claim a
    different licence from the one actually being granted."""
    header = _uncommented(HEADER_TEMPLATE.read_text(encoding="utf-8"))
    licence = LICENCE.read_text(encoding="utf-8")
    for sentence in (HOLDER, GRANT, CONDITION):
        assert sentence in header, f"header template lost: {sentence!r}"
        assert sentence in licence, f"LICENSE lost: {sentence!r}"
