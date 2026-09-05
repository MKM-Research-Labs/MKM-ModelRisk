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
"""The monitoring measures, checked against arithmetic done by hand.

Every expected value below is written as the sum it comes from rather than as a
constant somebody once printed and pasted. A monitoring figure is challenged in a
committee, and a test that asserts 0.2747 because that is what the code returned proves
only that the code has not changed — it cannot tell you the code was ever right.

The degenerate cases matter as much as the arithmetic. Each states what comes back, and
none of them raises: "the sample was too small to say" and "no shift detected" are
different findings, and a monitoring pack that cannot tell them apart is worse than one
that reports nothing.
"""
from __future__ import annotations

import math

from config.governance._monitoring_measures import (MIN_SAMPLE, PSI,
                                                    RANK_CORRELATION,
                                                    STATUS_INSUFFICIENT_SAMPLE,
                                                    STATUS_NO_DATA, STATUS_OK,
                                                    STATUS_UNDEFINED,
                                                    TRANSITION_STABILITY, rag_for)
from src.governance.monitoring.measures import (psi, quantile_edges, rank_correlation,
                                                stability, transition_matrix)


# --- Population stability index ----------------------------------------------

def test_psi_of_identical_distributions_is_zero():
    """Exactly zero, not nearly: every bucket's share cancels against itself, and
    ln(1) is 0. A floor that moved a real answer would show up here first."""
    population = [i % 10 for i in range(200)]
    outcome = psi(population, population, categorical=True)
    assert outcome["value"] == 0.0
    assert outcome["status"] == STATUS_OK
    assert outcome["rag"] == "Green"


def test_psi_matches_the_sum_computed_by_hand():
    """Baseline 50/50 across two categories, current 25/75.

        (0.25 - 0.50) * ln(0.25 / 0.50)  =  -0.25 * -0.693147  =  0.173287
        (0.75 - 0.50) * ln(0.75 / 0.50)  =   0.25 *  0.405465  =  0.101366
                                                                  --------
                                                                  0.274653
    """
    expected = ["A"] * 50 + ["B"] * 50
    actual = ["A"] * 25 + ["B"] * 75
    by_hand = (0.25 - 0.50) * math.log(0.25 / 0.50) + (0.75 - 0.50) * math.log(0.75 / 0.50)

    outcome = psi(expected, actual, categorical=True)
    assert outcome["value"] == round(by_hand, 12) or abs(outcome["value"] - by_hand) < 1e-12
    assert abs(outcome["value"] - 0.274653) < 1e-6
    # 0.2747 is above the 0.25 boundary, so this is the shift a committee is told about.
    assert outcome["rag"] == "Red"


def test_psi_is_symmetric():
    """(a-e)·ln(a/e) is unchanged when the two are swapped, which is what makes the
    index a distance rather than a direction."""
    one = ["A"] * 50 + ["B"] * 50
    other = ["A"] * 25 + ["B"] * 75
    assert abs(psi(one, other, categorical=True)["value"]
               - psi(other, one, categorical=True)["value"]) < 1e-12


def test_psi_bins_the_current_period_with_the_baselines_ruler():
    """Cut points come from the baseline and are then applied to both. Recut each
    period they would compare two different rulers and report stability whatever
    happened — so a wholesale shift must still register."""
    baseline = [float(i % 100) for i in range(200)]
    shifted = [float(i % 100) + 100 for i in range(200)]
    outcome = psi(baseline, shifted)
    assert outcome["status"] == STATUS_OK
    assert outcome["rag"] == "Red"


def test_quantile_edges_come_from_the_baseline_and_collapse_on_ties():
    assert quantile_edges([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], bins=2) == [4.5]
    # Half the rows sharing one value genuinely leaves fewer distinguishable buckets.
    assert quantile_edges([1, 1, 1, 1, 2, 2, 2, 2], bins=4) == [1.0, 1.5, 2.0]


def test_psi_declines_on_a_sample_too_small_to_mean_anything():
    outcome = psi(["A"] * 60 + ["B"] * 40, ["A"] * 5 + ["B"] * 5, categorical=True)
    assert outcome["status"] == STATUS_INSUFFICIENT_SAMPLE
    assert outcome["value"] is None and outcome["rag"] is None
    assert str(MIN_SAMPLE[PSI]) in outcome["detail"]


def test_psi_on_no_data_says_so():
    assert psi([], [])["status"] == STATUS_NO_DATA
    assert psi([1.0] * 200, [])["status"] == STATUS_NO_DATA


def test_psi_on_a_single_valued_baseline_is_undefined():
    """A baseline with one value has no quantiles to cut, so there is nothing to
    compare against — which is not a stability of zero."""
    outcome = psi([7.0] * 200, [float(i) for i in range(200)])
    assert outcome["status"] == STATUS_UNDEFINED
    assert outcome["value"] is None


def test_a_category_absent_from_the_baseline_does_not_send_it_to_infinity():
    """The floor is what keeps one empty bucket from swamping the index. Without it
    this is a division by zero inside a logarithm."""
    outcome = psi(["A"] * 100, ["A"] * 50 + ["B"] * 50, categorical=True)
    assert outcome["status"] == STATUS_OK
    assert math.isfinite(outcome["value"])
    assert outcome["rag"] == "Red"


def test_blanks_and_sentinels_in_a_numeric_field_are_dropped_not_coerced():
    """A field monitored as continuous still carries the odd blank, "n/a" or True.
    Dropping those is honest; coercing them puts invented numbers into the baseline,
    and float(True) is 1.0, which is exactly the kind of silent 1 that moves an index.
    """
    clean = [float(i % 50) for i in range(200)]
    dirty = clean + [None, "n/a", "", True, False]
    outcome = psi(dirty, dirty)
    assert outcome["status"] == STATUS_OK
    assert outcome["n"] == 200, "the five junk values are not counted as observations"
    assert outcome["value"] == 0.0


def test_quantile_edges_of_nothing_is_nothing():
    assert quantile_edges([]) == []


def test_a_categorical_side_that_is_entirely_missing_is_no_data():
    assert psi([], ["A"] * 200, categorical=True)["status"] == STATUS_NO_DATA
    assert psi([None] * 200, ["A"] * 200, categorical=True)["status"] == STATUS_NO_DATA


# --- Transition matrices ------------------------------------------------------

def test_a_transition_matrix_counts_the_moves_not_the_totals():
    """Two books with identical marginals: one where nobody moved, one where equal
    numbers crossed in both directions. The whole reason this exists beside PSI."""
    still = transition_matrix(["A"] * 50 + ["B"] * 50, ["A"] * 50 + ["B"] * 50)
    churned = transition_matrix(["A"] * 50 + ["B"] * 50, ["B"] * 50 + ["A"] * 50)

    assert still["rows"]["A"]["A"] == 50 and still["rows"]["A"]["B"] == 0
    assert churned["rows"]["A"]["B"] == 50 and churned["rows"]["A"]["A"] == 0
    assert stability(still)["value"] == 1.0
    assert stability(churned)["value"] == 0.0


def test_stability_is_the_diagonal_over_the_pairs():
    """88 of 100 stayed: 0.88, which is below the 0.90 bound and so Amber."""
    matrix = transition_matrix(["A"] * 60 + ["B"] * 40,
                               ["A"] * 55 + ["B"] * 5 + ["B"] * 33 + ["A"] * 7)
    outcome = stability(matrix)
    assert outcome["n"] == 100
    assert outcome["value"] == 0.88
    assert outcome["detail"] == {"stayed": 88, "moved": 12}
    assert outcome["rag"] == "Amber"


def test_an_unpaired_observation_is_dropped_rather_than_shifted():
    """Element i of each side is the same subject. A missing value must not slide the
    rest of the column onto somebody else's row."""
    matrix = transition_matrix(["A", None, "B", "C"], ["A", "B", None, "C"])
    assert matrix["n"] == 2
    assert matrix["rows"]["A"]["A"] == 1 and matrix["rows"]["C"]["C"] == 1


def test_stability_declines_on_too_few_pairs_and_on_none():
    assert stability(transition_matrix([], []))["status"] == STATUS_NO_DATA
    small = transition_matrix(["A"] * 10, ["A"] * 10)
    assert stability(small)["status"] == STATUS_INSUFFICIENT_SAMPLE


# --- Rank correlation ---------------------------------------------------------

def test_a_preserved_ordering_correlates_perfectly():
    outcome = rank_correlation(list(range(40)), [x * 3 + 7 for x in range(40)])
    assert outcome["value"] == 1.0
    assert outcome["rag"] == "Green"
    assert outcome["detail"]["inverted"] is False


def test_an_inverted_ordering_is_reported_as_broken_not_as_agreement():
    """rho is -1; the RATING reads the absolute value, and the sign is kept in detail.
    A score that has inverted has not decayed — it has broken — and rating it on the
    signed value would hide that behind a strong-looking number."""
    outcome = rank_correlation(list(range(40)), list(range(40))[::-1])
    assert outcome["detail"]["rho"] == -1.0
    assert outcome["detail"]["inverted"] is True
    assert outcome["value"] == 1.0


def test_ties_share_the_average_of_the_ranks_they_span():
    """An ordinal field is mostly ties. Ranking them by arrival order would invent
    agreement out of the order the rows happened to arrive in."""
    ordered = [1, 1, 2, 2] * 10
    shuffled = [1, 1, 2, 2] * 10
    assert rank_correlation(ordered, shuffled)["value"] == 1.0


def test_a_series_with_no_variation_has_no_ordering_to_agree_with():
    outcome = rank_correlation([5] * 40, list(range(40)))
    assert outcome["status"] == STATUS_UNDEFINED
    assert outcome["value"] is None, "not a correlation of zero, which reads as measured"


def test_rank_correlation_drops_unusable_values_rather_than_coercing_them():
    # Both sides unusable on the same row, so the pair is dropped by the coercion
    # guard rather than by the missing-value guard — they are different paths.
    xs = list(range(40)) + [None, "n/a", "n/a"]
    ys = list(range(40)) + ["n/a", None, "also not a number"]
    outcome = rank_correlation(xs, ys)
    assert outcome["n"] == 40
    assert outcome["value"] == 1.0


def test_rank_correlation_declines_on_too_few_and_on_none():
    assert rank_correlation([], [])["status"] == STATUS_NO_DATA
    few = rank_correlation(list(range(5)), list(range(5)))
    assert few["status"] == STATUS_INSUFFICIENT_SAMPLE
    assert str(MIN_SAMPLE[RANK_CORRELATION]) in few["detail"]


# --- The bands ----------------------------------------------------------------

def test_crossing_a_band_changes_the_rating():
    """One value either side of each configured boundary, for every measure that has
    them. A band table read the wrong way round is invisible until exactly this runs —
    it was, and 95% stability came back Red."""
    assert rag_for(PSI, 0.0999) == "Green" and rag_for(PSI, 0.10) == "Amber"
    assert rag_for(PSI, 0.2499) == "Amber" and rag_for(PSI, 0.25) == "Red"

    assert rag_for(TRANSITION_STABILITY, 0.7499) == "Red"
    assert rag_for(TRANSITION_STABILITY, 0.75) == "Amber"
    assert rag_for(TRANSITION_STABILITY, 0.8999) == "Amber"
    assert rag_for(TRANSITION_STABILITY, 0.90) == "Green"

    assert rag_for(RANK_CORRELATION, 0.6999) == "Red"
    assert rag_for(RANK_CORRELATION, 0.70) == "Amber"
    assert rag_for(RANK_CORRELATION, 0.8499) == "Amber"
    assert rag_for(RANK_CORRELATION, 0.85) == "Green"


def test_high_is_good_and_low_is_good_measures_do_not_share_a_direction():
    """PSI rates a high value Red; stability rates a high value Green. Both tables are
    written the same way — ascending bounds — so only the ratings differ."""
    assert rag_for(PSI, 0.9) == "Red"
    assert rag_for(TRANSITION_STABILITY, 0.99) == "Green"


def test_a_measure_with_no_value_has_no_rating():
    assert rag_for(PSI, None) is None
