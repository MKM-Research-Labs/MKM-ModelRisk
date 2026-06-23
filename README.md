# MKM-ModelRisk

A generic, model-agnostic **model-risk-governance platform**. It captures model
documentation, risk-assessment status, MRC meetings, BCBS 239 self-assessment,
RACI, document control and data lineage on an **immutable, event-sourced (CQRS)
store on PostgreSQL**. Identity is provided by the client's SSO at the perimeter;
every authenticated user may amend, gated by a confirmation step, with every
change attributed in a tamper-evident audit line.

See [`docs/mkm_modelrisk_extraction_plan.md`](docs/mkm_modelrisk_extraction_plan.md)
for the full architecture and build plan.

## Status

Event-store spine (plan Phase 1): append-only event log, per-stream hash chain,
database-grant immutability, projection replay. Next: governance domains on top.

## Development quickstart

Requires Docker and Python 3.13. The Meeting Pack PDF additionally needs a LaTeX
engine — install [tectonic](https://tectonic-typesetting.github.io/)
(`brew install tectonic`).

```bash
# 1. Start PostgreSQL (host port 5433, to avoid colliding with other local DBs)
docker compose up -d

# 2. Create the virtualenv and install
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 3. Run the test suite (applies migrations automatically)
pytest --cov

# 4. Run the governance console (applies migrations on startup)
python app.py            # serves http://127.0.0.1:5015
```

Copy `.env.example` to `.env` to override any connection settings; defaults
match `docker-compose.yml`. The web host/port are configurable via
`MKM_WEB_HOST` / `MKM_WEB_PORT` (default `127.0.0.1:5015`). A WSGI server can
serve the app object directly, e.g. `gunicorn app:app`.

## Architecture notes

- **`config/`** — the only home for parameters (coding rule R1), including all
  database connection settings.
- **`src/database/`** — the single sanctioned entry point for data access (R6).
  Nothing else opens a connection or writes SQL.
  - Append-only `events` table; immutability enforced at the database-grant
    level (the runtime `mkm_app` role cannot UPDATE/DELETE/TRUNCATE).
  - Each event chains to the previous event's SHA-256 hash, so any privileged
    tampering is detectable via `verify_chain`.
  - Plain numbered SQL migrations under `src/database/migrations/`, applied by
    the owner role and recorded in `schema_migrations`.
- Coding rules (ported from the parent engagement): params in `config/`, files
  under 300 lines, ≥99% test coverage per stage, no logic in `__init__.py`,
  canonical copyright header on every source file.
