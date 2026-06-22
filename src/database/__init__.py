# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
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
from src.database._connection import app_connection, owner_connection
from src.database._migrate import migration_files, run_migrations
from src.database.eventstore import (
    ConcurrencyError,
    Event,
    append_event,
    read_all,
    read_stream,
    verify_chain,
)
from src.database.projections import replay

__all__ = [
    "app_connection",
    "owner_connection",
    "migration_files",
    "run_migrations",
    "ConcurrencyError",
    "Event",
    "append_event",
    "read_all",
    "read_stream",
    "verify_chain",
    "replay",
]
