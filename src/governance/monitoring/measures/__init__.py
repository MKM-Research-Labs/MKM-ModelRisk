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
"""The monitoring measures: one implementation, both workflows.

Numeric, categorical and ordinal output fields are monitored the same way whatever
produced them. A model, an ML Application and an AI System that all emit a severity
band are asked the same question about it -- has the mix moved, did the same subjects
move, does the ordering still hold, and did what it predicted happen -- so the answer
comes from here rather than from three implementations that would diverge.

Every measure returns the same shape (``measure``, ``value``, ``rag``, ``n``,
``status``, ``detail``), resolves its own rating from config, and declines rather than
raises: a sample too small, a distribution with one value, a series with no ordering
all come back as stated statuses. See ``_result`` for why.

Thresholds are in ``config/governance/_monitoring_measures.py`` and nowhere else.
"""
from src.governance.monitoring.measures._distribution import (psi, quantile_edges,
                                                              stability,
                                                              transition_matrix)
from src.governance.monitoring.measures._outcome import backtest
from src.governance.monitoring.measures._rank import rank_correlation
from src.governance.monitoring.measures._result import result

__all__ = ["backtest", "psi", "quantile_edges", "rank_correlation", "result",
           "stability", "transition_matrix"]
