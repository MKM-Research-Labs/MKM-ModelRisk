# Coding Rules — PhysicalRisk

**Status:** Living document. Started 2026-06-19 during the JSON→PostgreSQL migration
(`docs/json_to_postgres_migration.md`); intended to apply **project-wide and to all future
initiatives**. Add rules here as we agree them — this file is the single source of truth.

Each rule has: the rule, *why*, *how to comply*, and *how it's verified* (ideally a CI
audit, not just goodwill). A rule isn't "done" until there's a way to check it mechanically.

---

## R1 — No hardcoded parameters outside the `config` package

**Rule.** Every parameter — filenames, directory names, magic numbers, thresholds,
field-name lists, default modes, prefixes — lives in the `config/` package. No literal
parameter values anywhere else.

**Why.** One place to change a value; no drift; reviewable; makes data/layout/behaviour
changes safe and auditable. Extends the existing path-definition audit from *paths* to
*all parameters*.

**How to comply.**
- Put the constant in the right `config` module (e.g. data-layout literals in
  `config/data_layout.py`; pricing/model params in `config/...`).
- Import and reference it; never inline the literal.
- Derive, don't duplicate: e.g. a per-key filename comes from a configured pattern
  (`"gauge_{key}_hd.json"`) split on `{key}`, not from a second literal.

```python
# ✗ bad
path = base / "gauge.json"
# ✓ good
from config.data_layout import PORTFOLIO_FILES
path = base / PORTFOLIO_FILES["gauge"]
```

**Verified by.** The path-definition audit (`config/path/registry.py` + scanner) — to be
extended to flag literal parameters outside `config` (migration task 0.8).

---

## R2 — No file longer than 300 lines

**Rule.** No non-test source file exceeds 300 lines. When a file grows past it, split it
into a package of focused modules.

**Why.** Small files are readable, testable, and reviewable; they force clear seams and
single-responsibility modules.

**How to comply.**
- Split by concern, not arbitrarily (one module per domain/responsibility).
- Prefer a package (`foo/` with submodules) over one long file.
- A package's `__init__.py` re-exports; it does not hold logic (see R4).

> Worked example: the `database` package is 16 modules, largest ~130 lines, instead of
> one ~500-line file.

**Verified by.** The 300-line audit (existing repo initiative). Run ad hoc:
`find src -name '*.py' -not -path '*/tests/*' | xargs wc -l | awk '$1>300'`.

---

## R3 — ≥99% test coverage, verified after each stage

**Rule.** Maintain ≥99% line coverage. Check it at the end of **every stage**, not just at
the end of a project.

**Why.** Catches regressions immediately; keeps the safety net tight as the codebase grows;
makes refactors (like the file→DB backend swap) safe.

**How to comply.**
- Write tests alongside the code in the same stage.
- Run the package-scoped coverage before calling a stage done.

```bash
source /Users/newdavid/Documents/PhysicalRisk/.venv/bin/activate
python -m pytest tests/<area> --cov=<package> --cov-report=term-missing
```

**Verified by.** `pyproject.toml` `fail_under = 99`. NOTE: `core = "ctrace"` is set there to
avoid a Python 3.13.1 `sys.monitoring` bug that silently deflates whole-suite coverage by
~15 points; do not remove it.

---

## R4 — No functions in `__init__.py`

**Rule.** `__init__.py` files contain only imports and `__all__` — no `def`, no `lambda`,
no logic.

**Why.** Keeps package entry points to a clear, scannable public surface; pushes
implementation into named, testable modules; avoids import-time side effects.

**How to comply.**
- Implementations live in submodules (e.g. domain modules `portfolio.py`, `trading.py`).
- Shared private helpers go in a `_helpers.py`, not `__init__.py`.
- Cross-cutting state (e.g. backend selection) gets its own module (`backend.py`).

```python
# database/__init__.py — re-exports only
from .portfolio import list_gauges, get_gauge, save_gauges
__all__ = ["list_gauges", "get_gauge", "save_gauges"]
```

**Verified by.** Ad hoc: `grep -nE "^\s*(def |lambda)" **/__init__.py`. To be folded into
the structural audit.

---

## R5 — Every source file carries the canonical copyright header

**Rule.** Every first-party `.py` and `.js` file must begin with the exact 19-line MKM
Research Labs license header from `docs/shared/copyright.py` (after an optional shebang).

**Why.** Legal/licensing clarity on every file; uniformity; a single canonical source for
the text so it can be updated in one place.

**How to comply.**
- Copy the header verbatim from `docs/shared/copyright.py` — **including its intentional
  trailing whitespace** on a few lines; the audit compares lines exactly.
- Place it at the very top (after a shebang if present), before the module docstring.
- Never hand-retype it (whitespace drift fails the audit); copy from the canonical file.

**Verified by.** `docs/models/full_audit/sections_tests/copyright_headers.py` — a
**self-healing** audit (`is_compliant` / `fix_text` / `fix_repo`) exercised by
`tests/commands/test_copyright_headers_report.py`, which repairs headers in place under
`app.py test`. Note: run the repo-wide self-heal in the main checkout, not a worktree
(dry-run `fix_repo(root, apply=False)` only in worktrees).

---

## R6 — Never access the data store directly; only call `database` functions

**Rule.** All catchment-data access goes through the `database` package. No module outside
`src/database/` may contain SQL, a DB connection/session/cursor, or a `json.load` /
`json.dump` / `glob` of `data/input`. Callers only call `database`'s intent-named
functions (`get_property(...)`, `commit_prs_trade(...)`, …). There is no escape hatch
(no `execute_sql` / `raw_query`); if a query isn't exposed, add a named function to the
package.

**Why.** A single point of contact means the storage backend (JSON files today,
PostgreSQL tomorrow) can be migrated without touching any caller, and it is the one place
to enforce security, permissions, caching, and audit. This is the cornerstone of the
JSON→PostgreSQL migration (`docs/json_to_postgres_migration.md` §2.0).

**How to comply.**
- Read/write data only via `from database import <function>`.
- Need data not yet exposed? Add a function in the right `database` submodule (and a test),
  never reach around the package.
- Configure the backend once at startup (`database.use_file_backend()`); callers never
  construct a repository.

```python
# ✗ bad — direct file access in a route/report/model
data = json.load(open(config.get_input_path("property.json")))
# ✓ good
from database import list_properties
data = list_properties(catchment)
```

**Verified by.** The zero-tolerance data-access audit (migration task 0.8): CI fails if any
`SELECT/INSERT/UPDATE/DELETE`, `.execute(`, `sqlalchemy`/`psycopg` import, connection
handle, or `json.load`/`open` of `data/input` appears outside `src/database/`.

---

## Adding a new rule (template)

```
## R<N> — <one-line rule>

**Rule.** <precise statement>
**Why.** <the motivation / failure it prevents>
**How to comply.** <concrete guidance, ideally with a good/bad example>
**Verified by.** <the audit/test/command that enforces it — add one if missing>
```

Candidate rules to consider as the project matures: single data-access utility (all DB
access via `database/`, zero SQL elsewhere — see `docs/json_to_postgres_migration.md` §2.0);
no embedded JavaScript in `.py` files; no mutating runs in a worktree; copyright header on
every source file.

---

## Change log

- 2026-06-19 — Created with R1–R4. First applied to the `database` package (WP0 of the
  JSON→PostgreSQL migration): all four satisfied, 100% coverage.
- 2026-06-19 — Added R5 (canonical copyright header) and applied it to all WP0 files.
- 2026-06-19 — Added R6 (only access data via the `database` package; no direct data access).
