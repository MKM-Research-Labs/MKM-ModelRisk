# MKM-ModelRisk

A generic, model-agnostic **model-risk-governance platform**. It manages the
full governance lifecycle around *whatever* quantitative models an institution
owns — the model inventory, validation against the SR 26-2 / supervisory
questions, remediation tracking, Model Risk Committee (MRC) meetings, document
control, a literature bibliography, and committee reporting — on top of an
**immutable, event-sourced (CQRS) store on PostgreSQL**.

Every change is captured as an event in an append-only, hash-chained log, so the
audit trail is the system of record rather than an afterthought. Identity comes
from the institution's SSO at the perimeter; every authenticated user may amend,
gated by an explicit confirmation step, with each change attributed to its author
and reason.

> **New here?** The [**User Guide**](docs/user_guide.md) walks through every
> screen and feature. This README covers installation and the architecture.

---

## Key capabilities

- **Model inventory** — register and maintain a rich model record (organisation,
  classification, tier, methodology, governance, review dates, testing status),
  with a tabbed detail view.
- **Validation & risk rating** — nine SR 26-2 validation questions seeded on
  registration; a weighted composite **risk rating** (Acceptable / Conditional /
  Unacceptable) computed from validation coverage, remediation health, review
  currency, and assumption/limitation risk.
- **Structured registers** — assumptions, limitations, versions, change history,
  remediation steps, and model dependencies, all event-sourced.
- **MRC meetings** — schedule meetings with agenda, minutes, participants,
  models-in-scope, decisions, and actions; export a **Meeting Pack PDF**.
- **Document control** — upload supporting documents per model (four categories)
  and governance-wide.
- **Bibliography** — manage references and export **BibTeX**.
- **Model Risk Report** — a committee-facing **PDF status report** across the
  whole inventory.
- **Immutable audit trail** — every mutation recorded with actor, timestamp,
  reason, and a tamper-evident hash chain.

---

## Architecture at a glance

| Concern | Approach |
|---|---|
| **Persistence** | PostgreSQL, accessed only through `src/database/` (one sanctioned utility). |
| **Model of record** | Event sourcing / CQRS — an append-only `events` table; read models (projections) are rebuilt from it. |
| **Immutability** | Enforced at the database-grant level: the runtime `mkm_app` role can `SELECT`/`INSERT` but never `UPDATE`/`DELETE`/`TRUNCATE`. Each event chains to the previous event's SHA-256 hash, so tampering is detectable. |
| **Authorisation** | No built-in auth — identity arrives from SSO at the perimeter. All users may amend; a confirmation step is mandatory and the actor + reason are stamped on every event. |
| **Web layer** | A Flask app factory + blueprints, with a dependency-free vanilla-JS console. |
| **Documents & PDFs** | Uploads stored on disk with metadata in the event stream; PDFs rendered via LaTeX (tectonic). |

The codebase is held to six **coding rules**, mechanically enforced (see
[Quality gates](#quality-gates)): parameters live only in `config/`; source files
stay under 300 lines; ≥99% test coverage per stage; no logic in `__init__.py`; a
canonical copyright header on every source file; and all database access through
the single `src/database/` utility.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| **Docker** | Runs PostgreSQL via `docker-compose.yml` (host port `5433`). |
| **Python 3.13** | The application runtime. |
| **tectonic** *(optional)* | A LaTeX engine, required only for the Meeting Pack and Model Risk Report PDFs. Install with `brew install tectonic`. |
| **Node + jscpd** *(optional)* | Only for the duplicate-code section of `python -m audit`. |

---

## Getting started

```bash
# 1. Clone
git clone git@github.com:MKM-Research-Labs/MKM-ModelRisk.git
cd MKM-ModelRisk

# 2. Start PostgreSQL (host port 5433, to avoid colliding with other local DBs)
docker compose up -d

# 3. Create the virtualenv and install
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"          # add ,e2e for the browser test suite

# 4. (Optional) Seed a few example models so the inventory isn't empty
PYTHONPATH=. python scripts/seed_demo.py

# 5. Run the governance console (database migrations are applied on startup)
python app.py                    # serves http://127.0.0.1:5015
```

Open **http://127.0.0.1:5015** and you'll land on the **Model Inventory** tab.
Set the **Acting as** field (top right) to your name/email — that identity is
recorded on every change you make. From there, follow the
[**User Guide**](docs/user_guide.md).

> **Tip:** the database is the only stateful piece. It lives in the Docker volume
> `modelrisk_mkm_modelrisk_pgdata` and persists across `docker compose stop/start`.
> Stopping the container doesn't lose data; only `docker compose down -v` would.

---

## Running the tests & quality gates

```bash
# Unit + integration suite (applies migrations automatically), with coverage
pytest --cov                                     # ~256 tests, 100% coverage

# End-to-end browser suite (Playwright; needs the [e2e] extra + a browser)
pip install -e ".[dev,e2e]"
python -m playwright install chromium
pytest tests/e2e -m e2e                          # 19 tests against a live server

# Coding-rule audit (large files, hardcoding, embedded JS, __init__, duplication)
python -m audit
```

The unit and e2e suites use **separate databases** (`mkm_modelrisk_test` and
`mkm_modelrisk_e2e`), created automatically inside the same Docker container, so
they never touch your dev data in `mkm_modelrisk`.

### Quality gates

`python -m audit` reports against the coding rules and exits non-zero on any
gated finding. The test suite additionally enforces ≥99% coverage and asserts a
clean tree for embedded JavaScript, substantive `__init__.py`, hardcoded
parameters, and over-long files.

---

## Configuration

Defaults match `docker-compose.yml`; override via environment variables (copy
`.env.example` to `.env`):

| Variable | Default | Purpose |
|---|---|---|
| `MKM_DB_HOST` / `MKM_DB_PORT` | `127.0.0.1` / `5433` | Database host/port |
| `MKM_DB_NAME` | `mkm_modelrisk` | Database name |
| `MKM_DB_OWNER_USER` / `MKM_DB_OWNER_PASSWORD` | `mkm_owner` / `mkm_dev_pw` | Owner role (migrations) |
| `MKM_DB_APP_USER` / `MKM_DB_APP_PASSWORD` | `mkm_app` / `mkm_app_dev_pw` | Runtime role (insert-only) |
| `MKM_WEB_HOST` / `MKM_WEB_PORT` | `127.0.0.1` / `5015` | Console host/port |
| `MKM_UPLOAD_DIR` | `./uploads` | Where uploaded files are stored |

A WSGI server can serve the app object directly, e.g. `gunicorn app:app`.

---

## Project layout

```
config/        Parameters only (rule R1) — DB, web, governance vocabulary, audit thresholds
src/
  database/    The only data-access utility (rule R6): event store, hash chain, migrations
  command/     Confirm-to-amend dispatch (threads the SSO actor + reason)
  identity/    Resolves the acting user from SSO headers (dev fallback)
  governance/  The domain: model_inventory, mrc, reference, documents, bibliography, collections
  files/       Upload storage
  web/         Flask app factory, API blueprints, and the vanilla-JS console (static/, templates/)
audit/         Self-checking coding-rule audit suite (python -m audit)
scripts/       Operational scripts (e.g. seed_demo.py)
tests/         Unit/integration tests + tests/e2e (Playwright browser suite)
docs/          User guide, architecture/build plan, coding rules
```

See [`docs/mkm_modelrisk_extraction_plan.md`](docs/mkm_modelrisk_extraction_plan.md)
for the architecture and build plan, and [`docs/rules/`](docs/rules/) for the
coding rules.

---

© 2022–2026 MKM Research Labs. All rights reserved.
