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
"""The finding-history observer's parameters (coding rule R1).

Ageing a finding needs to know when it first appeared, and the audit has no memory:
it is computed fresh each run. So something has to look, on a schedule, and write
down what it saw. These are that observer's settings.

Modelled on ``config.backup``, and for the same reason — in-app rather than a system
scheduler, because macOS blocks a background LaunchAgent from reading the repo under
~/Documents while the app inherits the launching shell's permissions.
"""
from __future__ import annotations

import os

# Whether the observer runs at all. An adopter who does not want the history (or a
# throwaway environment) turns it off and loses the trend line and finding ages;
# nothing else on the dashboard depends on it.
HISTORY_ENABLED = os.environ.get("HISTORY_ENABLED", "1") not in ("0", "false", "no")

# How long after start-up the first observation runs. Long enough that a restart
# during a busy period does not add a completeness scan to the stampede.
HISTORY_STARTUP_DELAY_SECONDS = float(os.environ.get("HISTORY_STARTUP_DELAY", "120"))

# How often to look. Daily: the finding set moves at the speed of a committee, and
# an hourly observation would record the same numbers twenty-four times.
HISTORY_INTERVAL_SECONDS = float(os.environ.get("HISTORY_INTERVAL", str(24 * 60 * 60)))

# How much trend the dashboard and the ERM carry. A year, so a reader sees a full
# governance cycle rather than a slope with no context.
TREND_DAYS = int(os.environ.get("TREND_DAYS", "365"))

# How long a closed finding stays on the history. Kept well past the longest
# remediation SLA so "opened and closed" counts are still answerable for a
# committee looking back over the year; pruned eventually so the table does not
# grow without limit on a large estate.
CLOSED_FINDING_RETENTION_DAYS = int(os.environ.get("CLOSED_FINDING_RETENTION", "730"))
