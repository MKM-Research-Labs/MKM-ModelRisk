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
"""Database utility — the single sanctioned entry point for data access (R6).

No other package may import a driver, open a connection, or write SQL. Everything
goes through the functions re-exported here.
"""
from src.database._connection import app_connection, create_database, owner_connection
from src.database._migrate import migration_files, run_migrations
from src.database.eventstore import (
    ConcurrencyError,
    Event,
    append_event,
    read_all,
    read_stream,
    verify_chain,
)
from src.database.projections import read_view, replace_view, replay

__all__ = [
    "app_connection",
    "owner_connection",
    "create_database",
    "migration_files",
    "run_migrations",
    "ConcurrencyError",
    "Event",
    "append_event",
    "read_all",
    "read_stream",
    "verify_chain",
    "replay",
    "replace_view",
    "read_view",
]
