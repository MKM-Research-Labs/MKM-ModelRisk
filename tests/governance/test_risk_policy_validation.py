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
"""What the committee is protected from proposing.

A risk policy is ratified once and then decides every model's rating in the
division until it is replaced. A malformed one is therefore not a validation
nicety: a grid with a missing cell silently stops rating the models that land in
it, and two bands sharing a name make the heatmap ambiguous in a way nobody sees
until a rating is challenged. Each refusal below names what is wrong, because the
person meeting it is an administrator editing a form, not a developer.
"""
from __future__ import annotations

import pytest

from src.governance.errors import DomainError
from src.governance.risk_policy import default_policy, set_policy_document
from src.governance.risk_policy.commands import _validate_policy
from src.governance.risk_policy.document import build_policy_document_tex


def _seed(**changes):
    policy = default_policy()
    policy.update(changes)
    return policy


def test_a_policy_that_is_not_an_object_is_refused():
    with pytest.raises(DomainError, match="risk policy must be an object"):
        _validate_policy(["not", "a", "policy"])


# --- Dimensions ---------------------------------------------------------------

def test_a_dimension_without_a_label_is_refused():
    """The label is what every screen and every document calls the dimension, so a
    blank one leaves the division's own vocabulary with a hole in it."""
    policy = default_policy()
    policy["dimensions"]["complexity"]["label"] = "   "
    with pytest.raises(DomainError, match="dimension 'complexity' needs a label"):
        _validate_policy(policy)


def test_a_dimension_with_no_bands_is_refused():
    policy = default_policy()
    policy["dimensions"]["materiality"]["bands"] = []
    with pytest.raises(DomainError, match="needs at least one band"):
        _validate_policy(policy)


def test_two_bands_of_one_dimension_cannot_share_a_name():
    """The grid keys on the band name, so a duplicate makes a cell ambiguous."""
    policy = default_policy()
    bands = policy["dimensions"]["materiality"]["bands"]
    bands[1] = {**bands[1], "name": bands[0]["name"]}
    with pytest.raises(DomainError, match="duplicate band names"):
        _validate_policy(policy)


# --- Bands --------------------------------------------------------------------

def test_a_band_that_is_not_an_object_is_refused():
    policy = default_policy()
    policy["dimensions"]["complexity"]["bands"] = ["High"]
    with pytest.raises(DomainError, match="each band must be an object"):
        _validate_policy(policy)


@pytest.mark.parametrize("key", ["name", "colour", "explanation", "score"])
def test_a_band_missing_any_part_of_the_quad_is_refused(key):
    """A band is a name, a colour, an explanation and a score. The explanation is
    the one people try to leave out, and it is the one a challenge turns on."""
    policy = default_policy()
    band = dict(policy["risk_ratings"][0])
    band.pop(key)
    policy["risk_ratings"][0] = band
    with pytest.raises(DomainError, match=f"missing '{key}'"):
        _validate_policy(policy)


def test_a_band_with_a_blank_name_is_refused():
    policy = default_policy()
    policy["dimensions"]["complexity"]["bands"][0] = {
        **policy["dimensions"]["complexity"]["bands"][0], "name": "  "}
    with pytest.raises(DomainError, match="a band has no name"):
        _validate_policy(policy)


# --- Risk ratings -------------------------------------------------------------

def test_a_policy_with_no_risk_ratings_is_refused():
    with pytest.raises(DomainError, match="at least one risk rating"):
        _validate_policy(_seed(risk_ratings=[]))


def test_two_risk_ratings_cannot_share_a_name():
    policy = default_policy()
    policy["risk_ratings"][1] = {**policy["risk_ratings"][1],
                                 "name": policy["risk_ratings"][0]["name"]}
    with pytest.raises(DomainError, match="duplicate names"):
        _validate_policy(policy)


# --- The grid -----------------------------------------------------------------

def test_a_table_that_does_not_cover_every_cell_is_refused():
    """A missing cell is the dangerous one: models landing there simply stop being
    rated, and nothing on any screen says why."""
    policy = default_policy()
    first = next(iter(policy["grid"]))
    cells = dict(policy["grid"][first])
    cells.pop(next(iter(cells)))
    policy["grid"][first] = cells
    with pytest.raises(DomainError, match="must cover every"):
        _validate_policy(policy)


# --- The audit section --------------------------------------------------------

def test_an_audit_section_that_is_not_an_object_is_refused():
    with pytest.raises(DomainError, match="audit section must be an object"):
        _validate_policy(_seed(audit=[1, 2, 3]))


def test_a_negative_audit_setting_is_refused():
    """Every one of them is a threshold, a weight or a number of days; a negative
    value inverts the escalation it is supposed to drive."""
    with pytest.raises(DomainError, match="cannot be negative"):
        _validate_policy(_seed(audit={"acceptable_at": -1}))


# --- The written policy document ----------------------------------------------

def test_a_policy_document_must_belong_to_a_division():
    """The aggregate IS the division, so a blank one would file the firm's policy
    under a stream nobody can find again."""
    with pytest.raises(DomainError, match="must belong to a division"):
        set_policy_document(division="  ", filename="rp.pdf",
                            original_name="Risk Policy v4.pdf", actor="admin")


def test_the_categorisation_document_says_where_the_written_policy_is_filed():
    """Two different documents with confusable names: this one is the grid the MRC
    ratifies, and the reader has to be told the prose policy exists separately."""
    tex = build_policy_document_tex(
        "Risk", {"live": default_policy(), "state": "approved",
                 "document": {"original_name": "Risk Policy v4.pdf"}},
        {"fields": {"org_name": "MKM"}})
    assert "\\section{Risk Policy document}" in tex
    assert "Risk Policy v4.pdf" in tex
