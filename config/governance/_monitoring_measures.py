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
"""The monitoring measures: every threshold, band and metric name, as data.

Numeric, categorical and ordinal output fields are monitored the same way whatever
produced them -- a scorecard, a gradient-boosted classifier or a generative system --
so there is one library and one set of thresholds behind it. What differs between those
records is what they output, not how a distribution shift is measured.

**Every number in this module is a judgement, not a fact.** The PSI bands below are the
convention the industry settled on rather than anything derived: 0.10 and 0.25 appear in
Siddiqi's scorecard work and have been repeated since, and an institution whose
portfolios are small or seasonal will find them too tight. The minimum sample sizes are
likewise a stance -- they say when WE would decline to report a number, and a firm may
draw that line elsewhere. They are here so that moving them is a configuration change
somebody can point at in a committee paper, which is the whole of R1's purpose.

Nothing here is imported by the measures for its own sake: the measures take their
thresholds through ``rag_for`` and ``min_sample``, so a caller cannot accidentally
apply one measure's bands to another's value.
"""
from __future__ import annotations

# --- The measures, by name ---------------------------------------------------
# Named because results are stored and read back: a result keyed by a string somebody
# typed is a result nothing can aggregate.
PSI = "psi"
TRANSITION_STABILITY = "transition_stability"
RANK_CORRELATION = "rank_correlation"
BACKTEST = "backtest"
MEASURES = (PSI, TRANSITION_STABILITY, RANK_CORRELATION, BACKTEST)

# --- What a result can say ----------------------------------------------------
# A measure that cannot be computed says so, in one of these words, and never raises
# and never returns a number that looks like an answer. "Not enough data to say" and
# "no shift detected" are different findings, and a monitoring report that cannot tell
# them apart is worse than one that reports nothing.
STATUS_OK = "ok"
STATUS_INSUFFICIENT_SAMPLE = "insufficient sample"
STATUS_UNDEFINED = "undefined"          # zero variance, one class, no overlap
STATUS_NO_DATA = "no data"
MEASURE_STATUSES = (STATUS_OK, STATUS_INSUFFICIENT_SAMPLE, STATUS_UNDEFINED,
                    STATUS_NO_DATA)

# --- How much data before we will report a number ----------------------------
# Below these, the measure returns ``insufficient sample`` rather than a figure. A PSI
# computed on forty rows is noise with a decimal point, and a committee shown one will
# act on it.
MIN_SAMPLE = {
    PSI: 100,
    TRANSITION_STABILITY: 50,
    RANK_CORRELATION: 30,
    BACKTEST: 50,
}

# --- Population Stability Index ----------------------------------------------
# Bands are (upper bound, rating): a value strictly below the bound takes that rating,
# and the last band has no bound. Ordered ascending; the resolver walks them in order,
# so reordering this changes every PSI rating in the estate.
PSI_BANDS = (
    (0.10, "Green"),
    (0.25, "Amber"),
    (None, "Red"),
)

# The number of quantile bins a continuous distribution is cut into before the index is
# computed. Ten is conventional; fewer hides a shift confined to one tail, more makes
# every bin small enough to be noisy.
PSI_BINS = 10

# A bin empty on one side sends the logarithm to infinity, so the share is floored
# here. Small enough not to move a real answer, large enough to keep one finite. This
# is the single most consequential number in the module: too large and it damps genuine
# shifts, too small and one empty bin dominates the index.
PSI_ZERO_FLOOR = 0.0001

# --- Transition matrices ------------------------------------------------------
# Stability is the share of the population that stayed where it was — the diagonal.
# High is good here, where a high PSI is bad, but the TABLE is written the same way
# regardless: ascending bounds, "a value below this bound takes this rating". Only the
# order of the ratings differs. Writing one table the other way round and leaving the
# resolver to work it out is how 95% stability came out Red the first time this ran.
TRANSITION_BANDS = (
    (0.75, "Red"),
    (0.90, "Amber"),
    (None, "Green"),
)

# --- Rank correlation ---------------------------------------------------------
# Spearman: Pearson's correlation computed on ranks, with ties taking the average of
# the ranks they span. Named in config because Kendall's tau is the other defensible
# choice and an institution may prefer it.
RANK_CORR_METHOD = "spearman"

# Bands on the ABSOLUTE correlation: what is being asked is "does the ordering still
# hold", and a strong negative correlation answers that as well as a strong positive
# one does — a score that has inverted is not a score that has decayed.
RANK_CORRELATION_BANDS = (
    (0.70, "Red"),
    (0.85, "Amber"),
    (None, "Green"),
)

# --- Backtesting --------------------------------------------------------------
# What "how did it do" means depends on what the field is. The estate has both kinds
# and reporting AUC for a depth-damage curve is how a monitoring pack stops being read.
FIELD_TYPE_CLASSIFICATION = "classification"
FIELD_TYPE_REGRESSION = "regression"
BACKTEST_FIELD_TYPES = (FIELD_TYPE_CLASSIFICATION, FIELD_TYPE_REGRESSION)

BACKTEST_METRICS = {
    FIELD_TYPE_CLASSIFICATION: ("accuracy", "precision", "recall", "f1"),
    FIELD_TYPE_REGRESSION: ("rmse", "mae", "r2", "bias"),
}

# Which single metric carries the RAG for each field type, and its bands. A backtest
# returns several numbers and a report needs one colour; choosing here rather than in
# the renderer keeps the choice arguable in a committee.
BACKTEST_HEADLINE = {
    FIELD_TYPE_CLASSIFICATION: "f1",
    FIELD_TYPE_REGRESSION: "r2",
}
BACKTEST_BANDS = {
    # Both headline metrics run 0..1 upwards, so both take lower bounds.
    FIELD_TYPE_CLASSIFICATION: ((0.60, "Red"), (0.80, "Amber"), (None, "Green")),
    FIELD_TYPE_REGRESSION: ((0.50, "Red"), (0.75, "Amber"), (None, "Green")),
}

# --- Resolution ---------------------------------------------------------------
# Every band table above obeys one rule: bounds ascend, and a value strictly below a
# bound takes that bound's rating; the last bound is None and catches the rest. Which
# end the good ratings sit at is the only thing that varies, and it is visible in the
# table rather than encoded in a direction flag somebody has to remember to set.
_BANDS = {
    PSI: PSI_BANDS,
    TRANSITION_STABILITY: TRANSITION_BANDS,
    RANK_CORRELATION: RANK_CORRELATION_BANDS,
}


def bands_for(measure: str, field_type: str | None = None) -> tuple:
    """The band table a measure's value is read against."""
    if measure == BACKTEST:
        return BACKTEST_BANDS[field_type or FIELD_TYPE_CLASSIFICATION]
    return _BANDS[measure]


def rag_for(measure: str, value: float | None, field_type: str | None = None) -> str | None:
    """The rating a measured value falls into, or ``None`` where there is no value.

    One resolver for every measure, so no caller reimplements the mapping — which is
    how the same PSI comes to be Amber on one screen and Green on another.
    """
    if value is None:
        return None
    for bound, rating in bands_for(measure, field_type):
        if bound is None or value < bound:
            return rating
    return None  # pragma: no cover - the last band has no bound


def min_sample(measure: str) -> int:
    return MIN_SAMPLE[measure]


__all__ = [
    "BACKTEST", "BACKTEST_BANDS", "BACKTEST_FIELD_TYPES", "BACKTEST_HEADLINE",
    "BACKTEST_METRICS", "FIELD_TYPE_CLASSIFICATION", "FIELD_TYPE_REGRESSION",
    "MEASURES", "MEASURE_STATUSES", "MIN_SAMPLE", "PSI", "PSI_BANDS", "PSI_BINS",
    "PSI_ZERO_FLOOR", "RANK_CORRELATION", "RANK_CORRELATION_BANDS",
    "RANK_CORR_METHOD", "STATUS_INSUFFICIENT_SAMPLE", "STATUS_NO_DATA", "STATUS_OK",
    "STATUS_UNDEFINED", "TRANSITION_BANDS", "TRANSITION_STABILITY", "bands_for",
    "min_sample", "rag_for",
]
