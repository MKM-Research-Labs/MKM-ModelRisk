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
- **Audit Reports** — an in-app tab that generates and serves PDF reports (the
  R1–R8 coding-rule audit, the Model Risk Report, and the User Guide).
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

You need two things installed; the other three are optional and only affect PDF
export and one extra audit check.

| Requirement | Required? | Install (macOS / Homebrew) |
|---|---|---|
| **PostgreSQL 16** | **Yes** — the database, run natively (no Docker). | `brew install postgresql@16` |
| **Python 3.13** | **Yes** — the application runtime. | `brew install python@3.13` |
| **tectonic** | Optional — LaTeX engine for the Meeting Pack, Model Risk Report, and the Audit Report PDFs (one per audit rule R1–R8 plus the consolidated coding-rule audit). Without it, those exports return a 503; everything else works. | `brew install tectonic` |
| **pandoc** | Optional — renders the User Guide PDF in the Audit Reports tab. | `brew install pandoc` |
| **Node + jscpd** | Optional — only the duplicate-code section of `python -m audit`. | `brew install node` |

> On **Intel** Macs Homebrew lives under `/usr/local`; on **Apple Silicon** under
> `/opt/homebrew`. `scripts/pg.sh` auto-detects `postgresql@16` in either. For a
> non-Homebrew PostgreSQL, set `MKM_PG_BIN` to the directory that contains `initdb`.

---

## Getting started

### Quick start — one command

From the repo root after cloning, this prompts for your **host id** (the identity
your changes are attributed to — the "Acting as" author), then sets up the virtual
environment, the local database cluster, and launches the app. It is
safe to re-run.

```bash
# Prompt for the identity recorded as the author of your changes.
read -rp "Host id (author of your changes) [dev@localhost]: " HOST_ID
export MKM_IDENTITY_DEV_FALLBACK="${HOST_ID:-dev@localhost}"

# Python venv + dependencies (runtime + dev tooling).
[ -d .venv ] || python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Local PostgreSQL cluster: initialise on first run, otherwise just start it.
if [ -d .pgdata ]; then scripts/pg.sh start 2>/dev/null || true; else scripts/pg.sh init; fi

# Create, migrate and serve the database.
python app.py

# Optional: populate the inventory with a few example models.
python scripts/seed_demo.py
```

Then open **http://127.0.0.1:5015** — the **Acting as** field is pre-filled with
the host id you entered. (Prerequisites: **PostgreSQL 16** and **Python 3.13**; see
[Prerequisites](#prerequisites) above.)

### First-time setup, step by step (macOS)

Follow these in order from a fresh clone. **Steps 0–4 are one-off**; after that,
running the app again is just the three commands in
[Running it again](#running-it-again). Each step says what you should see, so you
can confirm it worked before moving on.

**Step 0 — Install the tools (one-off).** Skip to Step 1 if `brew --version`,
`psql --version` and `python3.13 --version` already work.

```bash
# Homebrew — skip if `brew --version` already prints a version
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# The two required tools (PostgreSQL 16 + Python 3.13)
brew install postgresql@16 python@3.13

# Optional — only needed for PDF exports (Meeting Pack, reports, User Guide)
brew install tectonic pandoc
```

Verify before continuing:

```bash
psql --version         # → psql (PostgreSQL) 16.x
python3.13 --version   # → Python 3.13.x
```

If either is `command not found`, Homebrew isn't on your `PATH` — see
[Troubleshooting](#troubleshooting).

**Step 1 — Get the code.**

```bash
git clone https://github.com/MKM-Research-Labs/MKM-ModelRisk.git
cd MKM-ModelRisk
```

**Step 2 — Create the Python environment.**

```bash
python3.13 -m venv .venv
source .venv/bin/activate          # ← run this in EVERY new terminal
pip install -e ".[dev]"
```

✓ Your prompt now shows `(.venv)` and `python --version` prints `3.13.x`.

**Step 3 — Create the database cluster (one-off).**

```bash
bash scripts/pg.sh init            # creates ./.pgdata on port 5433, then starts it
```

✓ You should see `Cluster ready on port 5433; database 'mkm_modelrisk' created.`
Confirm it is up with `bash scripts/pg.sh status` → `... accepting connections`.

**Step 4 — Launch the app.**

```bash
python app.py                      # creates + migrates mkm_modelrisk on first run
```

✓ You should see `Running on http://127.0.0.1:5015`.

**Step 5 — Open it.** Visit **http://127.0.0.1:5015**, set the **Acting as** field
(top-right) to your name/email — that identity is stamped on every change — and
follow the [**User Guide**](docs/user_guide.md).

#### Running it again

In a fresh terminal (the database persists between runs):

```bash
cd MKM-ModelRisk
source .venv/bin/activate
bash scripts/pg.sh start
python app.py
```

Stop the app with **Ctrl-C**; stop the database with `bash scripts/pg.sh stop`.

> **Note.** The database starts empty; `python scripts/seed_demo.py` populates the
> inventory with a few example models. Defaults work out of the box; only create a
> `.env` (`cp .env.example .env`) to change ports/credentials — see
> [Configuration](#configuration).

#### Troubleshooting

| Symptom | Fix |
|---|---|
| `command not found: python3.13` or `psql` | Homebrew's tools aren't on your `PATH`. Ensure `/opt/homebrew/bin` (Apple Silicon) or `/usr/local/bin` (Intel) is on `PATH`, then open a **new** terminal. Re-run `brew install postgresql@16 python@3.13` if needed. |
| `scripts/pg.sh: Permission denied` | Invoke it via `bash scripts/pg.sh …` (as shown above). |
| `pg_ctl: could not start server` on `init`/`start` | A cluster is **already running** on port 5433 — check `bash scripts/pg.sh status`. If a different PostgreSQL owns 5433, stop it (or set `MKM_DB_PORT`). |
| `psql: could not connect` / `connection refused` | The cluster isn't running: `bash scripts/pg.sh start`. |
| `Address already in use` on port 5015 | An app instance is still up: `lsof -tiTCP:5015 \| xargs kill`, then retry. |
| PDF exports return **503** | Install the optional engines: `brew install tectonic pandoc`. |
| Want a clean slate | `bash scripts/pg.sh start && dropdb -h localhost -p 5433 -U mkm_owner --if-exists mkm_modelrisk && python app.py`. |

### Verify the checkout (optional but recommended)

```bash
python -m audit                  # coding-rule audit — exits non-zero on any finding
pytest --cov                     # unit + integration suite, 100% coverage
```

> **Tip:** the database is the only stateful piece. It lives in the cluster's data
> directory (`./.pgdata` by default, gitignored). Manage it with
> `scripts/pg.sh start|stop|status`; the data persists across stop/start.

---

## Running the tests & quality gates

```bash
# Unit + integration suite (applies migrations automatically), with coverage
pytest --cov                                     # ~317 tests, 100% coverage

# End-to-end browser suite (Playwright against a live server). The Python
# packages are part of `[dev]`; only the browser binary is a separate step.
python -m playwright install chromium
pytest tests/e2e -m e2e

# Coding-rule audit (large files, hardcoding, embedded JS, __init__, duplication)
python -m audit
```

The unit and e2e suites use **separate databases** (`mkm_modelrisk_test` and
`mkm_modelrisk_e2e`), created automatically in the same PostgreSQL cluster, so
they never touch your dev data in `mkm_modelrisk`.

### Quality gates

`python -m audit` reports against the coding rules and exits non-zero on any
gated finding. The test suite additionally enforces ≥99% coverage and asserts a
clean tree for embedded JavaScript, substantive `__init__.py`, hardcoded
parameters, and over-long files.

---

## Configuration

Defaults match `scripts/pg.sh`; override via environment variables (copy
`.env.example` to `.env`):

| Variable | Default | Purpose |
|---|---|---|
| `MKM_DB_HOST` / `MKM_DB_PORT` | `127.0.0.1` / `5433` | Database host/port |
| `MKM_DB_NAME` | `mkm_modelrisk` | Database name |
| `MKM_DB_OWNER_USER` / `MKM_DB_OWNER_PASSWORD` | `mkm_owner` / `mkm_dev_pw` | Owner role (migrations) |
| `MKM_DB_APP_USER` / `MKM_DB_APP_PASSWORD` | `mkm_app` / `mkm_app_dev_pw` | Runtime role (insert-only) |
| `MKM_WEB_HOST` / `MKM_WEB_PORT` | `127.0.0.1` / `5015` | Console host/port |
| `MKM_PG_DATA_DIR` | `./.pgdata` | Cluster data directory (`scripts/pg.sh`) |
| `MKM_UPLOAD_DIR` | `./uploads` | Where uploaded files (and audit PDFs) are stored |

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
  web/         Flask app factory + API blueprints
  static/      Front-end assets — js/ and css/ (rule R7)
  templates/   Jinja templates (rule R7)
audit/         Self-checking coding-rule audit suite (python -m audit)
scripts/       Operational scripts (seed_demo.py, pg.sh)
tests/         Unit/integration tests + tests/e2e (Playwright browser suite)
docs/          User guide, architecture/build plan, coding rules
```

See [`docs/mkm_modelrisk_extraction_plan.md`](docs/mkm_modelrisk_extraction_plan.md)
for the architecture and build plan, and [`docs/rules/`](docs/rules/) for the
coding rules.

## Licence

Released under the MIT License — see [`LICENSE`](LICENSE) for the full text.
The per-file header that every first-party source file carries (coding rule R5)
is generated from [`docs/shared/copyright.py`](docs/shared/copyright.py), which
is the single source of truth for that text.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
