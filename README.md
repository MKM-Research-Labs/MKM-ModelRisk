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

> **New here?** The [**User Guide**](<docs/Integration guide/user_guide.md>) walks through every
> screen and feature. This README covers installation and the architecture.

> **Installing on Windows 11?** Go straight to
> [**Installing on Windows 11 with Claude**](#installing-on-windows-11-with-claude) —
> a step-by-step runbook written to be followed by an AI assistant, with the
> checks and the corporate-laptop failure modes spelled out.

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
- **Document control** — upload supporting documents per model (thirteen categories,
  from Core Documentation and Test Results to Event and Remediation Evidence)
  and governance-wide.
- **Model Risk Report** — a committee-facing **PDF status report** across the
  whole inventory.
- **Audit Reports** — an in-app tab that generates and serves PDF reports (the
  coding-rule audit, the Model Risk Report, and the User Guide).
- **Immutable audit trail** — every mutation recorded with actor, timestamp,
  reason, and a tamper-evident hash chain.

---

## Architecture at a glance

| Concern | Approach |
|---|---|
| **Persistence** | PostgreSQL, accessed only through `src/database/` (one sanctioned utility). |
| **Model of record** | Event sourcing / CQRS — an append-only `events` table; read models (projections) are rebuilt from it. |
| **Immutability** | Enforced at the database-grant level: the runtime `mkm_app` role can `SELECT`/`INSERT` but never `UPDATE`/`DELETE`/`TRUNCATE`. Those grants are PostgreSQL DDL and do **not** cross to another engine — for SQL Server see [`docs/MS Sql/mssql-immutability.md`](<docs/MS Sql/mssql-immutability.md>). Each event chains to the previous event's SHA-256 hash, so tampering is detectable. |
| **Authorisation** | No built-in auth — identity arrives from SSO at the perimeter. All users may amend; a confirmation step is mandatory and the actor + reason are stamped on every event. |
| **Web layer** | A Flask app factory + blueprints, with a dependency-free vanilla-JS console. |
| **Documents & PDFs** | Uploads stored on disk with metadata in the event stream; PDFs rendered via LaTeX (tectonic). |

The codebase is held to nine **coding rules** (R1-R9), mechanically enforced (see
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

## Installing on Windows 11 with Claude

This section is written to be **followed by an AI assistant** (Claude) driving the
install on a Windows 11 machine, and to be readable by the person watching it.
Work through it **in order**. Every step ends in a check — do not move past a check
that fails; go to [When a step fails](#when-a-step-fails) instead.

> **The short version for a human.** Download the repo, double-click
> **`START-HERE.bat`**, and answer the prompt. It installs what is missing and
> launches the app. Everything below exists for when that is not allowed to work,
> which on a managed corporate laptop is the normal case.

### Three facts that cause most Windows failures

Read these first; they are the reason the steps are shaped the way they are.

1. **Python must be 3.13 or newer.** Typing `python` on a clean Windows 11 box
   often opens the Microsoft Store instead of running anything — that stub is not
   a Python. Use the `py` launcher (`py -3.13`) to be certain which one you have.
2. **gunicorn is not used on Windows and is not installed there.** It needs
   `fcntl`, which is POSIX-only, so `pyproject.toml` marks it
   `sys_platform != "win32"`. On Windows the app runs with **`python model.py`**.
   Do not try to install gunicorn; do not follow the Linux run commands.
3. **Never run any of this elevated.** `initdb` refuses to run as Administrator.
   The database cluster lives inside the repo folder (`.\.pgdata`) and needs no
   admin rights at all. If a step seems to want Administrator, that is a signal
   something else is wrong.

### Step 1 — Preflight

```powershell
winget --version
py -3.13 --version
git --version
```

**Check:** `py -3.13 --version` prints `Python 3.13.x`. If all three print a
version, skip to [Step 3](#step-3--set-up-and-launch).

### Step 2 — Install the packages

This is the step most likely to need a human with rights. Two are required; the
rest only affect PDF export.

```powershell
winget install -e --id Python.Python.3.13
winget install -e --id PostgreSQL.PostgreSQL.16
winget install -e --id Git.Git
# Optional: PDF export and one audit section
winget install -e --id JohnMacFarlane.Pandoc
winget install -e --id OpenJS.NodeJS
```

Then **close PowerShell and open a new one** — `PATH` is only re-read by new
processes, and skipping this makes a correct install look like a failed one.

**Check:**

```powershell
py -3.13 --version                                  # Python 3.13.x
Test-Path 'C:\Program Files\PostgreSQL\16\bin\initdb.exe'   # True
```

`tectonic` is not in winget and has its own step — see
[Step 2b](#step-2b--install-tectonic-needed-for-every-pdf).

### Step 2b — Install tectonic (needed for every PDF)

Skip only if the pilot does not need PDFs. Without tectonic the **Meeting Pack**,
**Model Risk Report** and **Audit Report** exports return **503**; every other
screen works normally.

Two things make this different from the other packages:

- **There is no winget package.** That request is still open upstream, so
  `winget install tectonic` will not find anything.
- **The app finds it on `PATH` and nowhere else.** `compile_tex` resolves it with
  `shutil.which("tectonic")` and there is no setting to point at a path, so
  wherever `tectonic.exe` lands it must be on `PATH`.

Pick the first of these that your machine allows.

**Option A — Scoop (per-user, no Administrator).** Usually the best fit for a
managed laptop: Scoop installs into your profile and puts its shims on `PATH` for
you.

```powershell
# Install Scoop itself, if you do not already have it
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression

scoop install tectonic
```

**Option B — Download the release archive (no package manager at all).** The most
likely to work when installers are blocked, because it is just a file.

1. Download the Windows archive from
   <https://github.com/tectonic-typesetting/tectonic/releases> (the
   `x86_64-pc-windows-msvc` asset).
2. Unpack it and put `tectonic.exe` somewhere permanent, e.g.
   `%LOCALAPPDATA%\Programs\tectonic\`.
3. Add that folder to your user `PATH` — no Administrator needed:

```powershell
$dir = "$env:LOCALAPPDATA\Programs\tectonic"
[Environment]::SetEnvironmentVariable(
  'PATH', [Environment]::GetEnvironmentVariable('PATH','User') + ";$dir", 'User')
```

**Option C — The official installer script.** Note what it does: it drops
`tectonic.exe` **in the directory you run it from**, which is almost certainly not
on `PATH` — so finish with the `PATH` step from Option B.

```powershell
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://drop-ps1.fullyjustified.net'))
```

**Option D — Build it with Cargo.** Only if the Rust toolchain is already there;
it is a long compile and needs no admin.

```powershell
cargo install tectonic
```

**Check — in a new PowerShell window**, so it picks up the changed `PATH`:

```powershell
tectonic --version          # → Tectonic 0.x.x
```

Then confirm the app can see it. `shutil.which` reads the `PATH` of the **running
process**, so an app that was already running when you installed tectonic will
keep returning 503 until it is restarted:

```powershell
# stop the app with Ctrl-C, then
python model.py
```

and download a Meeting Pack PDF from any meeting.

> **First run needs the internet.** Tectonic ships as a single executable and
> downloads the TeX support files it needs on the fly, caching them for later. On
> a restricted network that first fetch is the thing most likely to fail, and it
> looks like a hang or a PDF timeout rather than a network error. If the machine
> goes through a proxy, set it before the first PDF:
> ```powershell
> $env:HTTPS_PROXY = 'http://proxy.corp:8080'
> ```
> Once the support files are cached, later PDFs do not need the network.

### Step 3 — Set up and launch

From the repo folder:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start.ps1
```

It creates the virtualenv, installs the Python dependencies, initialises the
PostgreSQL cluster in `.\.pgdata` on port 5433, applies migrations and starts the
app. It is **safe to re-run** — every step is idempotent and it leaves a running
cluster alone. Useful variants:

| Command | Effect |
|---|---|
| `... start.ps1 -NoRun` | Set everything up, do not launch |
| `... start.ps1 -Seed` | Also load a few example models |
| `... start.ps1 -Identity you@corp` | Skip the identity prompt |
| `... start.ps1 -StopDb` | Stop the database cluster |

**Check:** the console is served at **http://127.0.0.1:5015**.

```powershell
(Invoke-WebRequest http://127.0.0.1:5015 -UseBasicParsing).StatusCode   # 200
```

To run it again later in a fresh terminal, the cluster having persisted:

```powershell
.venv\Scripts\Activate.ps1
powershell -ExecutionPolicy Bypass -File scripts\start.ps1 -NoRun   # starts the cluster
python model.py
```

### Step 4 — Confirm the install is sound

```powershell
.venv\Scripts\Activate.ps1
python -m audit
pytest
```

**Check:** `python -m audit` ends with a `FINDINGS:` or `PASS:` line — read that
line, not the exit code of the shell. `pytest` is expected to report a small
number of known failures; see [Quality gates](#quality-gates). A wall of errors
about databases or imports means the setup did not complete, not that the code is
broken.

### When a step fails

Corporate Windows blocks things a home machine does not. These are the ones worth
knowing before they happen.

| Symptom | What it means, and what to do |
|---|---|
| `winget` is not recognised | It ships as **App Installer**. Install or update App Installer from the Microsoft Store, then reopen PowerShell. |
| winget runs but every install is blocked | Group policy is refusing installs. Download the installers directly — Python from <https://www.python.org/downloads/windows/> (tick **Add python.exe to PATH**), PostgreSQL 16 from <https://www.enterprisedb.com/downloads/postgres-postgresql-downloads>. Both offer a per-user install that does not need Administrator. |
| Neither installer is permitted at all | PostgreSQL only needs its **binaries** on disk — the repo runs its own cluster. Unzip a PostgreSQL 16 binary bundle anywhere and point at it: `$env:PG_BIN = 'D:\pg16\bin'`, then re-run `start.ps1`. |
| `pip` cannot reach the network / SSL errors | You are behind the corporate proxy. `$env:HTTPS_PROXY = 'http://proxy.corp:8080'` (and `HTTP_PROXY`) before re-running, or configure an internal index with `pip config set global.index-url ...`. |
| `... cannot be loaded because running scripts is disabled` | PowerShell execution policy. The commands above already pass `-ExecutionPolicy Bypass`, which needs no permanent change — use them exactly as written. |
| `initdb: cannot be run as Administrator` | You are in an elevated prompt. Close it, open a normal PowerShell window. |
| `Python 3.13+ not found` after installing it | `PATH` is stale in this window. Open a **new** PowerShell. |
| `connection refused` on port 5433 | The cluster is not running: `powershell -ExecutionPolicy Bypass -File scripts\start.ps1 -NoRun`. |
| `Address already in use` on 5015 | An instance is still up. `Get-NetTCPConnection -LocalPort 5015 \| Select-Object -ExpandProperty OwningProcess \| ForEach-Object { Stop-Process -Id $_ }` |
| PDF exports return **503** | `tectonic` is not installed. Optional — see Step 2. |
| `ModuleNotFoundError: gunicorn` | Something is following the Linux instructions. On Windows the app runs with `python model.py`. |

### If you are Claude, doing this install

- Run the checks and **read their output** before continuing. A command that
  printed nothing has not passed.
- Do not substitute `python` for `py -3.13` when verifying the version — that is
  the check that catches the Microsoft Store stub.
- Do not elevate, and do not install gunicorn, whatever an error suggests.
- The database and the uploaded files are two halves of one record: if you move
  `PG_DATA_DIR`, move `UPLOAD_DIR` with it, or documents will list but not download.
- Nothing here writes outside the repo folder except the package installs in
  Step 2.

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
> [**docs/Integration guide/windows-setup.md**](<docs/Integration guide/windows-setup.md>) is a click-by-click walkthrough
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
gunicorn --config gunicorn.conf.py wsgi:application   # migrates mkm_modelrisk on first run
```

✓ You should see `Listening at: http://127.0.0.1:5015`.

On Windows, where gunicorn does not run, use `python model.py` instead.

**Step 5 — Open it.** Visit **http://127.0.0.1:5015**, set the **Acting as** field
(top-right) to your name/email — that identity is stamped on every change — and
follow the [**User Guide**](<docs/Integration guide/user_guide.md>).

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
gunicorn --config gunicorn.conf.py wsgi:application
```

For local development, `python model.py` instead — the Flask development server,
which reloads as you edit and carries the debugger. It serves the same app; what
differs is the server in front of it. Under gunicorn there is no reloader, so a
change to the code or to `index.html` needs a restart — `kill -HUP <master pid>`
recycles the workers gracefully, finishing in-flight requests first.

*Windows (PowerShell)*

```powershell
cd MKM-ModelRisk
.venv\Scripts\Activate.ps1
powershell -ExecutionPolicy Bypass -File scripts\start.ps1 -NoRun   # starts the cluster
python model.py
```

Stop the app with **Ctrl-C**. Stop the database with `bash scripts/pg.sh stop`
(Linux/macOS) or `powershell -ExecutionPolicy Bypass -File scripts\start.ps1 -StopDb`
(Windows). `start` and `stop` are both idempotent — running either twice is a
no-op, not an error.

> **Stop the database before shutting down or unmounting its volume.** The
> cluster does not auto-start, so after a reboot `python model.py` fails with
> `connection to server at "127.0.0.1", port 5433 failed: Connection refused` —
> that just means the database is not running, so `bash scripts/pg.sh start`
> fixes it. Pulling the volume out from under a *running* cluster is the harmful
> case: it forces crash recovery on the next start and can leave a stale
> `postmaster.pid`.

> **Keeping the data off the working copy.** `PG_DATA_DIR` and `UPLOAD_DIR` both
> default to inside the clone. Point them at another volume in `.env` to keep the
> checkout free of data — but move **both** together: the database holds each
> document's metadata while `UPLOAD_DIR` holds its bytes, so splitting them leaves
> documents that list but will not download.

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
| Want a clean slate | Drop and recreate the database: `dropdb -h localhost -p 5433 -U mkm_owner --if-exists mkm_modelrisk && python model.py` (start the cluster first). On Windows use `"C:\Program Files\PostgreSQL\16\bin\dropdb.exe"` with the same arguments. To wipe everything, delete the `.pgdata` folder and re-run the start script. |

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
coverage run -m pytest && coverage report        # ~1,300 tests, >=99% coverage (gated)

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
`config/env.py` loads it at import, so every entry point (`python model.py`, a WSGI
server, the start scripts, pytest) sees the same settings. A real environment
variable always wins over the file.

| Variable | Default | Purpose |
|---|---|---|
| `DB_HOST` / `DB_PORT` | `127.0.0.1` / `5433` | Database host/port |
| `DB_NAME` | `mkm_modelrisk` | Database name |
| `DB_OWNER_USER` / `DB_OWNER_PASSWORD` | `mkm_owner` / `mkm_dev_pw` | Owner role (migrations) |
| `DB_APP_USER` / `DB_APP_PASSWORD` | `mkm_app` / `mkm_app_dev_pw` | Runtime role (insert-only) |
| `WEB_HOST` / `WEB_PORT` | `127.0.0.1` / `5015` | Console host/port |
| `WEB_WORKERS` / `WEB_THREADS` | `4` / `4` | gunicorn worker processes and threads each. Peak database connections are the product of the two — the stock `max_connections` is 100 |
| `WEB_TIMEOUT` | `300` | Seconds before gunicorn kills a stuck worker. Generous because report PDFs shell out to tectonic |
| `WEB_WORKER_CLASS` | `gthread` | gunicorn worker type |
| `BACKUP_ENABLED` | `1` | Whether the running app keeps the hourly backup schedule. The verification app sets `0` |
| `BACKUP_INTERVAL_SECONDS` | `3600` | How often the app dumps the database |
| `PG_DATA_DIR` | `./.pgdata` | Cluster data directory (`scripts/pg.sh`); point at an external volume to keep the clone free of data |
| `PG_BIN` | auto-detected | Directory holding `initdb`/`pg_ctl`, if PostgreSQL 16 isn't in a standard location (`scripts/pg.sh`) |
| `PG_LOCALE` | auto-detected | Locale used to `initdb` the cluster; falls back `en_US.UTF-8` → `C.UTF-8` → `C` (`scripts/pg.sh`) |
| `IDENTITY_DEV_FALLBACK` | `david.kelly@mkmresearchlabs.com` | Local "Acting as" identity when there is no SSO header |
| `UPLOAD_DIR` | `./uploads` | Where uploaded files (and audit PDFs) are stored |
| `PRODUCER_ROOT` | `../PhysicalRisk` | Root of the producing repo a migration reads from |

The console is served by gunicorn against `wsgi:application`, configured by
`gunicorn.conf.py` at the repo root (which takes every value from `config/web.py`).
The startup work — migrations, seeded defaults and the read-model rebuild — and the
hourly backup both run **once in the gunicorn master, before it forks**, not once per
worker; see `src/web/_startup.py` and `src/web/_backup.py`. Any other WSGI server can
serve `wsgi:application` too, and will do that startup work on import instead.

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

See [`docs/user_guide.md`](<docs/Integration guide/user_guide.md>) for a walkthrough of every screen,
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
