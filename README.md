# MKM-ModelRisk

A generic, model-agnostic **model-risk-governance platform**. It manages the
full governance lifecycle around *whatever* quantitative models an institution
owns — the model inventory, validation against the SR 26-2 / supervisory
questions, remediation tracking, the model chain and its field-level handoffs,
products, Model Risk Committee (MRC) meetings, document control, and committee
reporting — on top of an **immutable, event-sourced (CQRS) store on PostgreSQL**.

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
- **Model chain** — the "string of pearls" derived from each model's declared
  dependencies, split into **Chain / Terminal / Hibernated** views. Every edge
  carries a **handoff**: the provider-field ↔ consumer-field lineage and a
  compatibility note the MRC reviews.
- **Products** — bind a product to its analytics model, market-data model and
  calculating agent, with **RACI roles** and **operational events** that feed up
  to the MRC as agenda items for the committee to receive.
- **MRC meetings** — schedule meetings with agenda, minutes, participants,
  models-in-scope, decisions, and actions; export a **Meeting Pack PDF**.
- **Document control** — upload supporting documents per model (nine categories,
  from Core Documentation and Test Results to Event and Remediation Evidence)
  and governance-wide.
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

You need **two** things: PostgreSQL 16 and Python 3.13. The other three are
optional and only affect PDF export and one extra audit check.

| Requirement | Required? | Purpose |
|---|---|---|
| **PostgreSQL 16** | **Yes** | The database, run natively (no Docker). |
| **Python 3.13** | **Yes** | The application runtime. |
| **tectonic** | Optional | LaTeX engine for the Meeting Pack, Model Risk Report and Audit Report PDFs. Without it those exports return a 503; everything else works. |
| **pandoc** | Optional | Renders the User Guide PDF in the Audit Reports tab. |
| **Node + jscpd** | Optional | Only the duplicate-code section of `python -m audit`. |

### Install them

**Debian / Ubuntu**

```bash
sudo apt update
sudo apt install -y git postgresql-16 python3.13 python3.13-venv
# Optional extras
sudo apt install -y tectonic pandoc nodejs npm
```

> **Ubuntu 24.04 and older ship Python 3.12, not 3.13.** If `apt` cannot find
> `python3.13`, add the deadsnakes PPA first:
> ```bash
> sudo add-apt-repository -y ppa:deadsnakes/ppa && sudo apt update
> sudo apt install -y python3.13 python3.13-venv
> ```
> Likewise, if `postgresql-16` is unavailable, add the PostgreSQL APT repository
> (<https://www.postgresql.org/download/linux/ubuntu/>).

**Fedora / RHEL**

```bash
sudo dnf install -y git postgresql16-server python3.13
sudo dnf install -y tectonic pandoc nodejs        # optional extras
```

**macOS (Homebrew)**

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install postgresql@16 python@3.13
brew install tectonic pandoc node                 # optional extras
```

**Windows 10/11 (winget, in PowerShell)**

```powershell
winget install -e --id Git.Git
winget install -e --id Python.Python.3.13
winget install -e --id PostgreSQL.PostgreSQL.16
winget install -e --id JohnMacFarlane.Pandoc      # optional extras
winget install -e --id OpenJS.NodeJS
```

> Close and reopen PowerShell afterwards so the new `PATH` takes effect. The
> PostgreSQL installer puts its binaries in `C:\Program Files\PostgreSQL\16\bin`,
> which `start.ps1` finds automatically — you do **not** need them on `PATH`, and
> you do **not** need the bundled server running as a Windows service (the repo
> runs its own cluster in `.\.pgdata` on port 5433).

Verify before continuing — both must succeed:

```bash
python3.13 --version                       # → Python 3.13.x

# PostgreSQL 16 — at least one of these should print a path or a version
initdb --version 2>/dev/null || ls -d /usr/lib/postgresql/16 /usr/pgsql-16 \
  /opt/homebrew/opt/postgresql@16 /usr/local/opt/postgresql@16 2>/dev/null
```

> **Finding PostgreSQL.** `scripts/pg.sh` looks for the version-16 binaries in
> the usual places — Homebrew (`/opt/homebrew`, `/usr/local`), Debian/Ubuntu
> (`/usr/lib/postgresql/16/bin`), Fedora/RHEL (`/usr/pgsql-16/bin`), and finally
> your `PATH`. On Debian/Ubuntu the binaries are deliberately **not** on `PATH`,
> which is normal — the script finds them anyway. If yours lives somewhere else,
> set `PG_BIN` to the directory containing `initdb`.

---

## Getting started

### Quick start — one command

After [installing the prerequisites](#prerequisites) and cloning, one script does
everything: checks the toolchain, creates the virtualenv, installs dependencies,
brings up the local PostgreSQL cluster, and launches the app. **Safe to re-run** —
every step is idempotent, and it leaves an already-running cluster alone.

**Linux / macOS**

```bash
git clone https://github.com/MKM-Research-Labs/MKM-ModelRisk.git
cd MKM-ModelRisk
bash scripts/start.sh
```

**Windows 10/11 (PowerShell)**

```powershell
git clone https://github.com/MKM-Research-Labs/MKM-ModelRisk.git
cd MKM-ModelRisk
powershell -ExecutionPolicy Bypass -File scripts\start.ps1
```

> **No command line at all?** Double-click **`START-HERE.bat`** in the repo root.
> It installs Python and PostgreSQL via winget if they are missing, then runs the
> setup — no terminal, no git, nothing pre-installed.
> [**docs/windows-setup.md**](docs/windows-setup.md) is a click-by-click walkthrough
> from downloading a ZIP onwards, written for a non-technical user.

> Run it as your **normal user, not elevated** — `initdb` refuses to run as
> Administrator, and the cluster lives inside the repo so no admin rights are needed.

Then open **http://127.0.0.1:5015**. The script asks for the identity your changes
are attributed to (the "Acting as" author) and pre-fills it.

Both scripts take the same options:

| Option (bash / PowerShell) | Effect |
|---|---|
| `--no-run` / `-NoRun` | Set everything up but don't launch the app |
| `--seed` / `-Seed` | Also load a few example models |
| `--identity me@corp` / `-Identity me@corp` | Skip the prompt and use this author id |
| `--help` / `-StopDb` | Show usage / stop the database cluster |

### First-time setup, step by step

Works the same on Linux and macOS. Follow these in order from a fresh clone.
**Steps 0–4 are one-off**; after that, running the app again is just the three
commands in [Running it again](#running-it-again). Each step says what you should
see, so you can confirm it worked before moving on.

**Step 0 — Install the tools (one-off).** See
[Prerequisites](#prerequisites) above for the `apt` / `dnf` / `brew` commands.
Skip to Step 1 if `python3.13 --version` already prints a version and PostgreSQL 16
is installed.

**Step 1 — Get the code.**

```bash
git clone https://github.com/MKM-Research-Labs/MKM-ModelRisk.git
cd MKM-ModelRisk
```

**Step 2 — Create the Python environment.**

*Linux / macOS*

```bash
python3.13 -m venv .venv
source .venv/bin/activate          # ← run this in EVERY new terminal
pip install -e ".[dev]"
```

*Windows (PowerShell)*

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1         # ← run this in EVERY new terminal
pip install -e ".[dev]"
```

✓ Your prompt now shows `(.venv)` and `python --version` prints `3.13.x`.

**Step 3 — Create the database cluster (one-off).**

*Linux / macOS*

```bash
bash scripts/pg.sh init            # creates ./.pgdata on port 5433, then starts it
```

*Windows (PowerShell)* — there is no `pg.sh` on Windows; the start script does the
cluster setup (it will skip the venv work already done in Step 2):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start.ps1 -NoRun
```

✓ You should see `Cluster ready on port 5433; database 'mkm_modelrisk' created.`
On Linux/macOS confirm with `bash scripts/pg.sh status` → `... accepting connections`.

**Step 4 — Launch the app.**

```bash
python app.py                      # creates + migrates mkm_modelrisk on first run
```

✓ You should see `Running on http://127.0.0.1:5015`.

**Step 5 — Open it.** Visit **http://127.0.0.1:5015**, set the **Acting as** field
(top-right) to your name/email — that identity is stamped on every change — and
follow the [**User Guide**](docs/user_guide.md).

#### Running it again

Simplest: re-run the start script — `bash scripts/start.sh` (or
`powershell -ExecutionPolicy Bypass -File scripts\start.ps1`). It skips whatever is
already done and just launches the app.

To do it by hand in a fresh terminal (the database persists between runs):

*Linux / macOS*

```bash
cd MKM-ModelRisk
source .venv/bin/activate
bash scripts/pg.sh start
python app.py
```

*Windows (PowerShell)*

```powershell
cd MKM-ModelRisk
.venv\Scripts\Activate.ps1
powershell -ExecutionPolicy Bypass -File scripts\start.ps1 -NoRun   # starts the cluster
python app.py
```

Stop the app with **Ctrl-C**. Stop the database with `bash scripts/pg.sh stop`
(Linux/macOS) or `powershell -ExecutionPolicy Bypass -File scripts\start.ps1 -StopDb`
(Windows).

> **Note.** The database starts empty; `python scripts/seed_demo.py` populates the
> inventory with a few example models. Defaults work out of the box; only create a
> `.env` (`cp .env.example .env`) to change ports/credentials — see
> [Configuration](#configuration).

#### Troubleshooting

| Symptom | Fix |
|---|---|
| `PostgreSQL 16 not found` from `pg.sh` | The version-16 binaries aren't in a known location. Find them (`ls /usr/lib/postgresql/*/bin` on Debian/Ubuntu, `ls /usr/pgsql-*/bin` on Fedora/RHEL) and set `PG_BIN` to that directory. |
| `command not found: python3.13` | **Linux:** install it (see [Prerequisites](#prerequisites)); on Ubuntu ≤24.04 you need the deadsnakes PPA. **macOS:** Homebrew isn't on `PATH` — add `/opt/homebrew/bin` (Apple Silicon) or `/usr/local/bin` (Intel) and open a **new** terminal. |
| `No module named venv` / `ensurepip is not available` (Debian/Ubuntu) | The venv module is a separate package: `sudo apt install python3.13-venv`. |
| `initdb: invalid locale` / `locale not found` | Your image lacks the locale. `pg.sh` now falls back to `C.UTF-8`/`C` automatically — if you still hit it, force one: `PG_LOCALE=C.UTF-8 bash scripts/pg.sh init`. |
| `scripts/pg.sh: Permission denied` | Invoke it via `bash scripts/pg.sh …` (as shown above). |
| `initdb: cannot be run as root` | Run as your normal user, not with `sudo`. The cluster lives in the repo's `./.pgdata`, so no root is needed. |
| **Windows:** `… cannot be loaded because running scripts is disabled` | Execution policy. Launch it as `powershell -ExecutionPolicy Bypass -File scripts\start.ps1` (no permanent change needed). |
| **Windows:** `initdb: cannot be run as Administrator` | Close the elevated prompt and run in a **normal** PowerShell window. |
| **Windows:** `PostgreSQL 16 not found` | Install it (`winget install -e --id PostgreSQL.PostgreSQL.16`), or point at it: `$env:PG_BIN = 'D:\PostgreSQL\16\bin'`. |
| **Windows:** `Python 3.13+ not found` | `winget install -e --id Python.Python.3.13`, then **reopen PowerShell** so `PATH` refreshes. |
| `pg_ctl: could not start server` on `init`/`start` | A cluster is **already running** on port 5433 — check `bash scripts/pg.sh status`. If a different PostgreSQL owns 5433, stop it (or set `DB_PORT`). On Debian/Ubuntu the distro auto-starts a cluster on 5432, which does **not** clash. |
| `psql: could not connect` / `connection refused` | The cluster isn't running. `bash scripts/pg.sh start` (Linux/macOS) or `scripts\start.ps1 -NoRun` (Windows). |
| `Address already in use` on port 5015 | An app instance is still up: `lsof -tiTCP:5015 \| xargs kill` (or `fuser -k 5015/tcp` on Linux), then retry. |
| PDF exports return **503** | Install the optional engines — `sudo apt install tectonic pandoc` / `brew install tectonic pandoc`. |
| Want a clean slate | Drop and recreate the database: `dropdb -h localhost -p 5433 -U mkm_owner --if-exists mkm_modelrisk && python app.py` (start the cluster first). On Windows use `"C:\Program Files\PostgreSQL\16\bin\dropdb.exe"` with the same arguments. To wipe everything, delete the `.pgdata` folder and re-run the start script. |

### Verify the checkout (optional but recommended)

```bash
python -m audit                  # coding-rule audit — exits non-zero on any finding
pytest                           # unit + integration suite (e2e excluded by default)
```

> **Tip:** the database is the only stateful piece. It lives in the cluster's data
> directory (`./.pgdata` by default, gitignored). Manage it with
> `bash scripts/pg.sh start|stop|status` on Linux/macOS, or
> `scripts\start.ps1 -NoRun` / `-StopDb` on Windows; the data persists across
> stop/start.

---

## Running the tests & quality gates

```bash
# Unit + integration suite (applies migrations automatically), with coverage
coverage run -m pytest && coverage report        # ~747 tests, ≥99% coverage (gated)

# End-to-end browser suite (Playwright against a live server). The Python
# packages are part of `[dev]`; only the browser binary is a separate step.
python -m playwright install chromium
pytest tests/e2e -m e2e

# Coding-rule audit (large files, hardcoding, embedded JS, __init__, duplication)
python -m audit
```

These commands are identical on Windows once the virtualenv is active
(`.venv\Scripts\Activate.ps1`) and the cluster is up.

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

Defaults match `scripts/pg.sh`. Copy `.env.example` to `.env` and override there —
`config/env.py` loads it at import, so every entry point (`python app.py`, a WSGI
server, the start scripts, pytest) sees the same settings. A real environment
variable always wins over the file.

| Variable | Default | Purpose |
|---|---|---|
| `DB_HOST` / `DB_PORT` | `127.0.0.1` / `5433` | Database host/port |
| `DB_NAME` | `mkm_modelrisk` | Database name |
| `DB_OWNER_USER` / `DB_OWNER_PASSWORD` | `mkm_owner` / `mkm_dev_pw` | Owner role (migrations) |
| `DB_APP_USER` / `DB_APP_PASSWORD` | `mkm_app` / `mkm_app_dev_pw` | Runtime role (insert-only) |
| `WEB_HOST` / `WEB_PORT` | `127.0.0.1` / `5015` | Console host/port |
| `PG_DATA_DIR` | `./.pgdata` | Cluster data directory (`scripts/pg.sh`); point at an external volume to keep the clone free of data |
| `PG_BIN` | auto-detected | Directory holding `initdb`/`pg_ctl`, if PostgreSQL 16 isn't in a standard location (`scripts/pg.sh`) |
| `PG_LOCALE` | auto-detected | Locale used to `initdb` the cluster; falls back `en_US.UTF-8` → `C.UTF-8` → `C` (`scripts/pg.sh`) |
| `IDENTITY_DEV_FALLBACK` | `dev@localhost` | Local "Acting as" identity when there is no SSO header |
| `UPLOAD_DIR` | `./uploads` | Where uploaded files (and audit PDFs) are stored |
| `PRODUCER_ROOT` | `../PhysicalRisk` | Root of the producing repo a migration reads from |

A WSGI server can serve the app object directly, e.g. `gunicorn app:app`.

---

## Project layout

```
config/        Parameters only (rule R1) — DB, web, governance vocabulary, audit thresholds
src/
  database/    The only data-access utility (rule R6): event store, hash chain, migrations
  command/     Confirm-to-amend dispatch (threads the SSO actor + reason)
  identity/    Resolves the acting user from SSO headers (dev fallback)
  governance/  The domain: model_inventory, model_chain, model_handoff, product,
               mrc, mrc_settings, reference, documents, data_lineage, collections
  ingest/      Inbound artifact contract (schema-validated ingest from producers)
  files/       Upload storage
  web/         Flask app factory + API blueprints
  static/      Front-end assets — js/ and css/ (rule R7)
  templates/   Jinja templates (rule R7)
audit/         Self-checking coding-rule audit suite (python -m audit)
scripts/       Setup + operations: start.sh / start.ps1 (one-command bootstrap),
               pg.sh (cluster), seed_demo.py, migration/backfill loaders
tests/         Unit/integration tests + tests/e2e (Playwright browser suite)
docs/          User guide, dependency manifest, coding rules
```

See [`docs/user_guide.md`](docs/user_guide.md) for a walkthrough of every screen,
and [`docs/rules/`](docs/rules/) for the coding rules.

## Licence

Released under the MIT License — see [`LICENSE`](LICENSE) for the full text.
Third-party dependencies and their licences are listed in
[`docs/dependencies.md`](docs/dependencies.md).
The per-file header that every first-party source file carries (coding rule R5)
is generated from [`docs/shared/copyright.py`](docs/shared/copyright.py), which
is the single source of truth for that text.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
