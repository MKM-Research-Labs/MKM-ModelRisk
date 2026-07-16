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
"""Projection support: rebuild read models by replaying the event log.

In CQRS the event log is the source of truth; read models are derived and fully
rebuildable. ``replay`` streams events in global order to a handler so a
projection can be built from zero or caught up from a checkpoint.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable, Sequence

from psycopg import sql
from psycopg.types.json import Jsonb

from src.database._connection import app_connection
from src.database.eventstore import Event, read_all


def replace_view(
    table: str, columns: Sequence[str], rows: Iterable[Sequence[Any]], *, config=None,
) -> int:
    """Atomically replace a read-model view: ``DELETE`` every row, then ``INSERT``
    each row in ``rows`` (a value sequence aligned to ``columns``). ``dict`` values
    are JSON-encoded automatically. The single sanctioned way for a projection to
    rebuild its view table (R6) — callers pass data, never SQL.
    """
    delete = sql.SQL("DELETE FROM {table}").format(table=sql.Identifier(table))
    insert = sql.SQL("INSERT INTO {table} ({cols}) VALUES ({vals})").format(
        table=sql.Identifier(table),
        cols=sql.SQL(", ").join(sql.Identifier(c) for c in columns),
        vals=sql.SQL(", ").join(sql.Placeholder() for _ in columns),
    )
    count = 0
    with app_connection(config) as conn, conn.cursor() as cur:
        cur.execute(delete)
        for row in rows:
            cur.execute(insert, tuple(Jsonb(v) if isinstance(v, dict) else v for v in row))
            count += 1
    return count


def read_view(
    table: str, columns: Sequence[str], *,
    where: str | None = None, value: Any = None, order_by: str | None = None, config=None,
) -> list[dict[str, Any]]:
    """Read rows from a read-model view as dicts keyed by ``columns``, optionally
    filtered by ``where = value`` and/or ordered by ``order_by``. The sanctioned
    read path for projection queries (R6)."""
    query = sql.SQL("SELECT {cols} FROM {table}").format(
        cols=sql.SQL(", ").join(sql.Identifier(c) for c in columns),
        table=sql.Identifier(table),
    )
    params: tuple = ()
    if where is not None:
        query = query + sql.SQL(" WHERE {col} = {ph}").format(
            col=sql.Identifier(where), ph=sql.Placeholder())
        params = (value,)
    if order_by is not None:
        query = query + sql.SQL(" ORDER BY {col}").format(col=sql.Identifier(order_by))
    with app_connection(config) as conn, conn.cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()
    return [dict(zip(columns, row)) for row in rows]


def replay(
    handler: Callable[[Event], None],
    *,
    after_global_seq: int = 0,
    config=None,
) -> int:
    """Apply ``handler`` to every event after ``after_global_seq``.

    Returns the number of events replayed and the caller can read the last
    ``global_seq`` from the events it received to persist a checkpoint.
    """
    count = 0
    for event in read_all(after_global_seq=after_global_seq, config=config):
        handler(event)
        count += 1
    return count
