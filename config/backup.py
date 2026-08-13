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
"""Database-backup scheduling parameters (coding rule R1).

The dump itself is ``scripts/backup_db.sh`` (``config.paths.BACKUP_SCRIPT``);
the schedule it runs on lives here.
"""
from __future__ import annotations

import os

# Whether the running app keeps the schedule at all. Off for anything that is
# not the real deployment — notably the verification app on 5016, which serves a
# scratch copy and has no business driving the estate's backup schedule. Note
# that backup_db.sh sources .env for its own credentials, so it dumps whatever
# .env names however the app process was pointed: a verification app left with
# the schedule on would be dumping the live database, not the copy it serves.
BACKUP_ENABLED = os.environ.get("BACKUP_ENABLED", "1").strip().lower() not in (
    "0", "false", "no", "off")

# How often the running app dumps the database.
BACKUP_INTERVAL_SECONDS = int(os.environ.get("BACKUP_INTERVAL_SECONDS", "3600"))

# Grace period before the first dump, so schema migrations and the read-model
# rebuild have settled and the snapshot is of a coherent database.
BACKUP_STARTUP_DELAY_SECONDS = int(os.environ.get("BACKUP_STARTUP_DELAY_SECONDS", "20"))

# A dump that has not finished in this long is abandoned; the next tick retries.
BACKUP_TIMEOUT_SECONDS = int(os.environ.get("BACKUP_TIMEOUT_SECONDS", "300"))
