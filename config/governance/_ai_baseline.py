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
"""The variability envelope: how much a system's output moves under a fixed configuration.

A generative system gives different answers to the same input. That is not a fault, and
the question governance asks is not "is it deterministic" but "how much does it move,
and is that within what we accepted". The envelope is the accepted range, measured by
running the same input N times under a pinned configuration.

**The dangerous failure is a narrow envelope from too few runs.** Three runs that happen
to agree produce a tight range that reads like a well-behaved system, and it is the most
flattering possible reading of the least evidence. So a run count below the minimum is
REFUSED rather than reported narrowly — the platform declines to state an envelope it
cannot support, and says how many runs it would need.

Every number here is a judgement an institution may set differently, which is why it is
config: 20 runs is enough to place a 10th and 90th percentile without pretending to a
tail, and a firm wanting the 5th and 95th needs more runs, not a wider guess.
"""
from __future__ import annotations

# Runs under one pinned configuration before an envelope may be stated. Below this the
# platform refuses; it does not narrow.
MIN_ENVELOPE_RUNS = 20

# What the platform asks for when it is asked to run a baseline. More than the minimum
# on purpose: a baseline built to the floor has no room for a failed run.
DEFAULT_ENVELOPE_RUNS = 30

# The limits the envelope is expressed as. Not min and max: the extreme of twenty runs
# is one run's bad day, and an envelope somebody has to defend should not be set by it.
ENVELOPE_PERCENTILES = (10, 90)

# The reason an envelope cannot be stated, when it cannot. Named so the console, the
# report and the tests use one word for it.
ENVELOPE_TOO_FEW_RUNS = "too few runs"
ENVELOPE_NO_RUNS = "no runs recorded"
ENVELOPE_STALE = "configuration moved"
ENVELOPE_OK = "ok"

ENVELOPE_STATUSES = (ENVELOPE_OK, ENVELOPE_NO_RUNS, ENVELOPE_TOO_FEW_RUNS,
                     ENVELOPE_STALE)

__all__ = ["DEFAULT_ENVELOPE_RUNS", "ENVELOPE_NO_RUNS", "ENVELOPE_OK",
           "ENVELOPE_PERCENTILES", "ENVELOPE_STALE", "ENVELOPE_STATUSES",
           "ENVELOPE_TOO_FEW_RUNS", "MIN_ENVELOPE_RUNS"]
