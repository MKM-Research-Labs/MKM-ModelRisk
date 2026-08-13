# Coding Rules — MKM-ModelRisk

**Status:** Living document. Inherited from the MKM engagement coding standards and
adapted for this repo (a generic, model-agnostic model-risk-governance platform that is
event-sourced and PostgreSQL-backed). Applies **repo-wide and to all future work**.
This file is the single source of truth; add rules here as we agree them.

Each rule has: the rule, *why*, *how to comply*, and *how it's verified*. A rule isn't
"done" until it can be checked mechanically.

---

## R1 — No hardcoded parameters outside the `config` package

**Rule.** Every parameter — filenames, ports, header names, field lists, value sets,
thresholds, default modes — lives in the `config/` package. No literal parameter values
anywhere else.

**Why.** One place to change a value; no drift; reviewable.

**How to comply.** Put the constant in the right `config` module (DB settings in
`config/database.py`; identity headers in `config/identity.py`; governance vocabulary and
field metadata in `config/governance.py`; web host/port in `config/web.py`). Import it;
never inline the literal. Derive, don't duplicate (e.g. `EDITABLE_FIELDS` and
`FIELD_CHOICES` are derived from `MODEL_FIELD_SPECS`).

**Verified by.** To be enforced by the ported path/parameter audit (Phase 0). Until then,
reviewed by hand.

---

## R2 — No file longer than 300 lines

**Rule.** No non-test source file exceeds 300 lines. Split into a package of focused
modules when it grows past it; a package's `__init__.py` re-exports only (see R4).

**Why.** Small files are readable, testable, reviewable; they force clear seams.

**Verified by.** Ad hoc: `find src config -name '*.py' | xargs wc -l | awk '$1>300'`.
To be folded into the structural audit (Phase 0).

---

## R3 — ≥99% test coverage, verified after each stage

**Rule.** Maintain ≥99% line+branch coverage. Check it at the end of **every stage**.

**Why.** Catches regressions immediately; keeps refactors (e.g. projection rebuilds) safe.

**How to comply.** Write tests alongside the code. Run before calling a stage done:

```bash
source .venv/bin/activate
python -m pytest --cov --cov-report=term-missing
```

**Verified by.** `pyproject.toml` `fail_under = 99`. NOTE: `core = "ctrace"` is set there to
avoid a Python 3.13.x `sys.monitoring` bug that silently deflates whole-suite coverage; do
not remove it.

---

## R4 — No functions in `__init__.py`

**Rule.** `__init__.py` files contain only imports and `__all__` — no `def`, no `lambda`,
no logic.

**Why.** Keeps package entry points to a clear, scannable public surface; pushes
implementation into named, testable modules.

**Verified by.** Ad hoc: `grep -nE "^\s*(def |lambda)" **/__init__.py`.

---

## R5 — Every source file carries the canonical copyright header

**Rule.** Every first-party `.py` and `.js` file begins with the exact MKM Research Labs
licence header from `docs/shared/copyright.py` (after an optional shebang). `.js` files use
the same lines with `//` in place of `#`.

**Every other first-party file carries a one-line licence notice** in its own comment syntax
(`--` for `.sql`, `/* */` for `.css`, `<!-- -->` for `.html`/`.md`, `#` for `.sh`/`.toml`/
dotfiles) rather than the full block. A file that *cannot* hold a comment — JSON forbids
them, binaries have no comment syntax — is marked by a sibling `<name>.license` file
(REUSE-style), so the exemption is recorded as a decision rather than an oversight.

**Why.** Legal/licensing clarity on every file; a single canonical source for the text.
Every file states its terms or points at `LICENSE`; none is silently unmarked.

**How to comply.** Don't hand-retype it — copy the block from `docs/shared/copyright.py`
verbatim (preserving any shebang above it).

**Verified by.** Nobody, automatically — and deliberately so. R5 is **not checked by
`python -m audit` and does not gate the build**: whose name belongs at the top of a file is
a commercial question for whoever owns the code, and a failing build forces that question at
the wrong moment and in the wrong place. The maintainer runs the check by hand from a
local-only tool that does not ship with the repo.

`tests/test_licence.py` still asserts that `LICENSE` and `docs/shared/copyright.py` exist and
state the same terms, so the two cannot drift apart — that is about the licence itself, not
about which files carry a header.

---

## R6 — Never access the data store directly; only call `src/database` functions

**Rule.** All persistence goes through the `src/database/` package. No module outside it
may contain SQL, a DB connection/cursor/session, a driver import (`psycopg`, …), or open a
connection. Callers use the package's intent-named functions (`append_event`, `read_stream`,
`replay`, …). There is no escape hatch; if a query isn't exposed, add a named function.

**Why.** A single point of contact: the storage backend can evolve, and it is the one place
to enforce immutability (the event log's `UPDATE/DELETE` are revoked at the DB-grant level),
hashing, and audit. This is the cornerstone of the event-sourced design.

```python
# ✗ bad — SQL or a driver outside src/database/
import psycopg; conn = psycopg.connect(...)
# ✓ good
from src.database import append_event, read_stream
```

**Verified by.** To be enforced by the ported zero-tolerance data-access audit (Phase 0).
Until then, reviewed by hand.

---

## R7 — Front-end assets live under `src/static` and `src/templates`

**Rule.** JavaScript and CSS live under `src/static/js/` and `src/static/css/`; Jinja
templates under `src/templates/`. They do **not** sit beside the Flask app module
(`src/web/`). The app factory points Flask at these folders explicitly
(`Flask(__name__, static_folder="../static", template_folder="../templates")`).
Embedding JavaScript or CSS **inside a `.py` file is forbidden** — it belongs in a
dedicated `.js` / `.css` file under `src/static/`.

**Why.** A single, predictable home for front-end assets — independent of which blueprint
serves them — keeps the layout discoverable and matches the parent engagement's structure.
JS/CSS buried in Python strings is unlintable, untestable, and easy to break silently.

```
src/static/js/    *.js          # one file per UI module
src/static/css/   app.css
src/templates/    index.html
```

**Verified by.** The embedded-JS/CSS audit (`python -m audit`) flags JavaScript or CSS
inside `.py` files; the directory layout is reviewed by hand, and a misplaced asset shows
up as a 404 in the e2e smoke suite, which loads every script.

---

## R8 — Avoid duplication; extract shared logic into a utility

**Rule.** Where practical, do not duplicate logic — lift it into a named utility function
and call that from both sites. There is **zero tolerance** for duplication that spans two
models: shared model logic must live in exactly one place that both import.

**Why.** Duplication multiplies technical debt and the cost of ownership: every copy is a
place a fix can be missed and behaviour can silently diverge.

**How to comply.** When you find yourself copying more than a few lines, stop and extract a
helper into the nearest shared module (or a dedicated utility module). Across models, never
copy — promote the logic to a common location.

```python
# ✗ bad — the same calculation pasted into two places
# ✓ good
from src.governance.shared import compute_thing   # one definition, many callers
```

**Verified by.** The duplicate-code audit (`python -m audit`, jscpd) reports the
duplication percentage; cross-model duplication is treated as a hard fault in review.

---

## R9 — Test and verify against a restored backup, never the live database

**Rule.** No tool, script, REPL or verification app may write to a protected database
(`mkm_modelrisk`, `mkm_modelrisk_demo`). Work against a scratch database restored from the
hourly backups — `scripts/restore_scratch.sh` builds one — or let `pytest` derive its own.
Reading the live database is permitted; anything that writes is not. This binds ad-hoc work
as tightly as committed code: the breach that prompted this rule came from a throwaway
debugging script, not from the suite.

**Two ports, two databases.** `5015` serves the live estate; **everything under test runs on
`5016` against the scratch copy** (`scripts/dev_app.sh`, which refuses to start against a
protected database however `DB_NAME` was set). The port split is what makes the mistake
visible at a glance; the refusal is what makes it impossible. Note the port alone guarantees
nothing — an app on 5016 that sourced `.env` unmodified is just as live, which is why the
guard checks the resolved database and not the port.

**Why.** The live database is the firm's governance record, and the event log is
append-only by design: a junk write cannot simply be deleted, only retired through the MRC.
On 2026-08-06 two debug scripts sourced `.env` — which points `DB_NAME` at `mkm_modelrisk` —
and registered models ZZ1/ZZ2 into the real estate under the test suite's identity. The
records are permanent; removing them from the active inventory needed a committee.

**How to comply.** `.env` aims everything at production, and `config/env.py` loads it on
import, so *any* process that imports `config` inherits the live database unless told
otherwise. Set `DB_NAME` to a scratch database explicitly, and confirm what it resolves to
before the first write:

```bash
# ✗ bad — inherits DB_NAME=mkm_modelrisk from .env
set -a; . ./.env; set +a
python -c "from src.web import create_app; create_app().run(port=5015)"

# ✗ bad — pg.sh sources .env AFTER your environment, so this restores over LIVE
DB_NAME=scratch scripts/pg.sh restore <dump>

# ✓ good — scratch database from the latest backup, verified before use
scripts/restore_scratch.sh                       # restores into mkm_modelrisk_scratch
set -a; . ./.env; set +a; export DB_NAME=mkm_modelrisk_scratch
python -c "from config.database import DatabaseConfig; print(DatabaseConfig.from_env().name)"
```

**Verified by.** Reviewed by hand — there is no mechanical gate yet, which is the weakness
of this rule as it stands. `assert_disposable` guards the destructive *test fixtures* only;
ordinary writes to a protected database pass unchallenged, and that is exactly the gap R9
describes. The intended enforcement is the identity guard (refuse an actor that is not a
registered person while `DB_NAME` is protected), which is designed but **not yet built**.

---

## Change log

- 2026-08-07 — Added R9 (test against a restored backup, never the live database), after two
  ad-hoc debugging scripts wrote junk models into the production event log.

- 2026-08-06 — R5 stopped being an automated check. The header and licence-notice scans left
  the audit (and the repo) for a local-only tool the maintainer runs by hand; `python -m audit`
  no longer reports or gates on them, and there is no longer an R5 report PDF. The rule itself
  stands — every first-party file still carries its header.
- 2026-07-16 — Relicensed to MIT (`LICENSE` at the repo root). R5 extended: its scope is
  repo-wide (root files, `tests/`, `docs/`), and every non-`.py`/`.js` file carries a
  one-line notice.
- 2026-06-25 — Added R8 (avoid duplication / extract utilities; zero-tolerance across
  models). Extended R7 to forbid embedding JS/CSS in `.py` files.
- 2026-06-25 — Added R7 (front-end assets under `src/static` / `src/templates`).
- 2026-06-22 — Created for MKM-ModelRisk, adapting R1–R6 from the parent engagement.
  R6 reframed around the `src/database/` event store. Mechanical audits (R1/R2/R4/R5/R6
  gates) to be ported in Phase 0.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
