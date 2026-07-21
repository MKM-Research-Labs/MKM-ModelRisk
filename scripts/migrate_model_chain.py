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
"""One-off migration: move a source repo's model chain into ModelRisk.

This is the first component to actually cross the boundary. It reads the "string
of pearls" dependency graph out of a source repo's ``model_inventory.json`` and
pushes it through the real ingest contract (``ingest_payload``) — the same path a
producer uses — so the move is audit evidence, not a side-channel write. It is
idempotent (a re-run with unchanged content is a no-op) and re-runnable, so it
doubles as a documented record of the data move.

Run against the configured ModelRisk database:

    python -m scripts.migrate_model_chain \
        --source /path/to/PhysicalRisk/docs/models/governance_data/model_inventory.json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.database import run_migrations
from src.governance.model_chain import get_chain
from config.paths import PRODUCER_INVENTORY
from src.ingest import ingest_payload

PRODUCER = "migrate_model_chain"
PRODUCER_VERSION = "1.0.0"
# The canonical location of the governance data in the source repo.
DEFAULT_SOURCE = Path(
    str(PRODUCER_INVENTORY)
)


def _git_commit(near: Path) -> str:
    """The source repo's HEAD commit, so the move is pinned to a known revision."""
    try:
        out = subprocess.run(
            ["git", "-C", str(near.parent), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        )
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def extract_chain(inventory: dict[str, Any]) -> dict[str, Any]:
    """Pull the chain out of a ``model_inventory.json`` structure."""
    chain = inventory.get("model_chain")
    if not isinstance(chain, dict) or not chain.get("links"):
        raise ValueError("source has no model_chain.links to migrate")
    return chain


def load_model_chain(
    source_path: Path, *, source_repo: str = "PhysicalRisk",
    commit: str | None = None, generated_at: str | None = None, config=None,
) -> tuple[dict[str, Any] | None, bool]:
    """Read the chain from ``source_path`` and ingest it. Returns (receipt, created)."""
    inventory = json.loads(source_path.read_text(encoding="utf-8"))
    chain = extract_chain(inventory)
    envelope = {
        "schema_version": "v1",
        "artifact": "model-chain",
        "provenance": {
            "source_repo": source_repo,
            "commit": commit or _git_commit(source_path),
            "producer": PRODUCER,
            "producer_version": PRODUCER_VERSION,
            "generated_at": generated_at
            or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "payload": chain,
    }
    return ingest_payload("model-chain", envelope, config=config)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migrate a repo's model chain into ModelRisk.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE,
                        help="path to the source model_inventory.json")
    parser.add_argument("--repo", default="PhysicalRisk", help="source_repo name for provenance")
    args = parser.parse_args(argv)

    if not args.source.is_file():
        print(f"source not found: {args.source}", file=sys.stderr)
        return 1

    run_migrations()  # ensure model_chain_view exists
    receipt, created = load_model_chain(args.source, source_repo=args.repo)
    stored = get_chain(args.repo)
    links = (stored or {}).get("data", {}).get("link_count", "?")
    verb = "migrated" if created else "already present (idempotent no-op)"
    print(f"model chain {verb}: {links} links from {args.repo}")
    print(f"receipt: {json.dumps(receipt, indent=2) if receipt else 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
