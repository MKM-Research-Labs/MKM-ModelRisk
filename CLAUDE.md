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

**Known-red at HEAD: nothing. `pytest` is green (verified 2026-08-26 on `main`).**

The list was one test — `tests/audit/test_audit_large_files.py::test_source_tree_within_limit`
— and it is now passing, because the two files it named were split. Do not add an
entry here without a date and a reason; do not leave one once it stops being true.

This list shrinks as well as grows. The two product-API entries that sat here were
tests asserting a retired design — a Product seeds four RACI roles at registration, and
its validation questions were deliberately removed — so they were fixed, not excused.
The three `tests/governance/test_monitoring.py` failures were never a `main` failure at
all: they left `configured` to resolve off disk, so they passed in the main checkout and
failed in a worktree, which is exactly the sort of entry that rots. Treat this list the
same way as the audit baseline below — a claim with a date on it, not a standing fact. A
stale entry costs more than a missing one, because it excuses a real regression.

**The e2e suite is a separate baseline, and it is not green.** `pytest` excludes it, so
the gate above says nothing about it. Verified 2026-08-12 on `main`: inventory,
reference, committee and collections pass; `tests/e2e/test_e2e_mrc.py` (9),
`test_e2e_mrc_meeting.py` (2), `test_e2e_product.py` (6) and `test_e2e_documents.py` (3)
still fail, all of them tests that have drifted from screens that moved. Two traps if
you run it:

- The harness uses one fixed database (`mkm_modelrisk_e2e`) and truncates it before
  every test, so **two e2e runs at once destroy each other's data**. Run one at a time;
  concurrent runs look like flakiness, not like a collision.
- Killing a run leaves `tests/e2e/_runserver.py` orphaned (parent PID 1). It serves
  stale JS on a port nothing points at. Check for strays before blaming a change.

The audit's own gate reads **`PASS: 0 gated finding(s)`**, verified 2026-08-26 on
`main`. **Any finding you see is yours.** That is a stronger position than the baseline
this file carried for months, and it is worth keeping: with a zero gate a regression is
unmistakable, where a gate of 2 meant reading the list every time to see whether the
number had moved for your reason or somebody else's.

The last two entries went in the same week, and both split along a seam the code already
had rather than at a line count:

- `src/governance/client/pack.py` (384) → 228, with `_pack_sources.py` (what the pack
  covers — shared, because `pack_manifest` previews without compiling and is only honest
  while both walk the same sources) and `_pack_cover.py` (how the pack explains itself).
- `src/web/api_mrc/lifecycle.py` (326) → 224, with `models_scope.py` beside the
  `products_scope.py` that already existed. Lifecycle is what happens TO a meeting;
  those two are what it is ABOUT.

Before them, during the ML Application work, `api_models.py` dropped from 301 to 263 when
its `_grouped_specs` / `_collection_specs` moved to `src/web/_helpers.py`. Four APIs had a
copy of those and only the inventory's carried ``option_labels``, so a status vocabulary
renamed in Admin displayed by its stored value on every screen but a model's. One helper
now, and one fewer gated finding — the recurring lesson being that an over-long file is
usually two things that were never one.

**Test files are gated too, at 400 lines.** It is not in the list above only because
nothing currently exceeds it, and a few added comments are enough to trip it — run the
audit, not just `pytest`, before calling a test change done.

## 4. Verifying a UI change

Tests do not prove a screen. For anything visible, restore the scratch DB, serve it on
5016, and check it — never ask the user to look for you.

- **Template caching:** with `debug=False` Jinja caches `index.html`, so a **new `<script>`
  tag is not picked up until the server restarts**. Static JS/CSS are fine
  (`asset_version` busts the browser cache).
- **`kill -HUP` does NOT pick up changed Python.** This entry used to say it did; it does
  not, and the failure is silent — the endpoint keeps answering with the old code and you
  conclude your change is broken. `preload_app = False`, but the *master* has already
  imported the app to bootstrap, so forked workers inherit its `sys.modules`. **Stop and
  restart `dev_app.sh`** after any change under `src/` or `config/` (verified 2026-08-25,
  twice, while building the dashboard).
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

**Authorship is gated (permissions P1).** Against a protected database, a change must be
authored by somebody in Admin → People — matched on name or email — or the request is
refused with 403. `system` and `ingest:*` pass; an empty People list stands the rule down.
Policy is `config/permissions.py` (`ENFORCE_KNOWN_ACTORS`); the check lives in `authorize()`
in `src/command/dispatch.py` and in `request_actor()` for upload paths. If a write returns
403 saying the actor is not registered, that is this rule — send a real identity rather
than turning it off.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
