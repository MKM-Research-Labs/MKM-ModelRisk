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
"""Low-level database connections.

The only module that opens connections to PostgreSQL. Everything else in the
codebase reaches the database through ``src.database`` (coding rule R6).
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg

from config import DatabaseConfig


@contextmanager
def app_connection(
    config: DatabaseConfig | None = None,
) -> Iterator[psycopg.Connection]:
    """Open a connection as the runtime application role (append/read only)."""
    cfg = config or DatabaseConfig.from_env()
    with psycopg.connect(**cfg.app_conninfo()) as conn:
        yield conn


@contextmanager
def owner_connection(
    config: DatabaseConfig | None = None,
) -> Iterator[psycopg.Connection]:
    """Open a connection as the schema-owner role (migrations, test resets)."""
    cfg = config or DatabaseConfig.from_env()
    with psycopg.connect(**cfg.owner_conninfo()) as conn:
        yield conn
