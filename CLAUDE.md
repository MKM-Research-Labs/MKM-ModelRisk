# Working on MKM-ModelRisk

Instructions and protocol for any session on this repo. Read this before running anything.
The coding rules themselves are `docs/rules/coding_rules.md` (R1–R9); this is how to work
without breaking them.

---

## 1. The rule that matters most: never write to the live database

`mkm_modelrisk` is the firm's governance record and its event log is **append-only** — a
junk write cannot be deleted, only retired through a committee. On 2026-08-06 two ad-hoc
debugging scripts sourced `.env` and registered junk models into it under the test suite's
identity. That is coding rule **R9**.

**Two ports, two databases:**

| | Port | Database | For |
|---|---|---|---|
| Live | 5015 | `mkm_modelrisk` | the real estate — the user runs this; **read-only for you** |
| Test | 5016 | `mkm_modelrisk_scratch` | everything you run |

```bash
scripts/restore_scratch.sh    # newest hourly dump -> mkm_modelrisk_scratch
scripts/dev_app.sh            # serves it on 5016; refuses to start on a protected DB
```

Then `preview_start {url: "http://127.0.0.1:5016"}`.

**Two traps that cause this exact accident:**

- `config/env.py` loads `.env` **on import**, so *any* process importing `config` inherits
  `DB_NAME=mkm_modelrisk` unless told otherwise. A throwaway `python -c "from src.web
  import create_app"` is pointed at production by default.
- `scripts/pg.sh` sources `.env` **after** your environment, so
  `DB_NAME=scratch scripts/pg.sh restore <dump>` restores **over live**. Use
  `scripts/restore_scratch.sh`, which passes the target explicitly.

Before the first write in any ad-hoc script, print what you actually resolved to:

```bash
python -c "from config.database import DatabaseConfig; print(DatabaseConfig.from_env().name)"
```

Reading production is fine. Anything that writes is not — including "just a quick test".

## 2. Environment

- **Postgres must be up:** `bash scripts/pg.sh start` (port 5433). A "connection refused"
  usually means the cluster is down because `starter.sh` aborted on the macOS accessibility
  prompt before reaching `pg.sh start` — run `pg.sh start` directly.
- **Worktrees have no `.venv` and no `.env`.** Run Python via the **main checkout's**
  interpreter (`<main-checkout>/.venv/bin/python`); a bare `python` is the system 3.9 and
  its pytest plugins fail to start. `.env` exists only in the main checkout.
- Uploads follow whichever `config` package got imported, so a script run with the
  worktree on `sys.path` writes uploads where the app never looks.

## 3. How to test

```bash
# Unit + integration. Derives its OWN database (mkm_modelrisk_test_p<pid>) and is
# guarded by assert_disposable — this suite cannot reach live data.
pytest                                    # e2e and journey excluded by default
coverage run -m pytest && coverage report # with the ≥99% gate (rule R3)

# Coding-rule audit. Exits non-zero on a gated finding.
python -m audit

# End-to-end (Playwright, drives a LIVE SERVER — point it at 5016, never 5015)
python -m playwright install chromium
pytest tests/e2e -m e2e
```

**Reading the gate.** A background run that "completed, exit code 0" with empty output is
**not** a pass — that exit code is the shell's. Always read the final line:
`PASS: 0 gated finding(s)` or `FINDINGS: N gated finding(s)`.

**Known-red at HEAD (verified 2026-08-07 on `main`) — 6 tests. Do not chase these:**

```
tests/audit/test_audit_large_files.py::test_source_tree_within_limit
tests/governance/test_monitoring.py::test_document_reports_an_empty_estate_without_claiming_activity
tests/governance/test_monitoring.py::test_document_reports_observed_portfolio_activity
tests/governance/test_monitoring.py::test_document_names_a_catchment_that_holds_no_portfolio
tests/web/test_product_api.py::test_raci_roles_collection_on_a_product
tests/web/test_product_risk_api.py::test_validation_and_events_collections_are_available
```

The audit's own gate sits at **2 findings** (two over-long source files). Anything beyond
these is yours — diff against `main` before assuming otherwise, since the list moves.

## 4. Verifying a UI change

Tests do not prove a screen. For anything visible, restore the scratch DB, serve it on
5016, and check it — never ask the user to look for you.

- **Template caching:** with `debug=False` Jinja caches `index.html`, so a **new `<script>`
  tag is not picked up until Flask restarts**. Static JS/CSS are fine (`asset_version`
  busts the browser cache).
- **Many UI surfaces are hand-curated, not spec-driven.** Adding a field to config is not
  enough — wire it into the relevant detail lists, the Admin tab bar, and the register form.
- If screenshots come back blank and `document.body.getBoundingClientRect().width === 0`,
  the browser pane is hidden on the user's side: use `resize_window`, verify through the
  DOM, and say that you could not produce a visual.

## 5. The tree is shared — never revert what you did not write

Several sessions work in this checkout at once, and the user commits alongside you. Before
committing, `git status` and stage **only your own files**. A modified file you did not
touch is somebody's work in progress, not debris. Two things that look like your doing but
are not:

- Feature work appearing mid-run in files you never opened.
- The licence-header tool rewriting tracked files during a test run.

Check what a change actually is before reverting it.

## 6. Git workflow

- Feature work on a branch (worktree), then `git merge --no-ff` into `main` and push.
  The user's dev server runs from the main checkout, so nothing reaches them until it is
  merged **and** they restart Flask.
- Run `python -m audit` and `pytest` on the merged tree before pushing.
- End commit messages with:
  `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`

## 7. Rules that bite most often

Full text in `docs/rules/coding_rules.md`.

- **R1** — parameters live in `config/`, never hardcoded in `src/`.
- **R2** — no file over 300 lines (source gated; web files reported).
- **R6** — **zero tolerance**: no SQL, driver import or connection outside `src/database/`.
  Use the named helpers (`append_event`, `read_stream`, `read_view`, …).
- **R9** — test against a restored backup, never the live database (§1).

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
