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

**Why.** Legal/licensing clarity on every file; a single canonical source for the text.

**How to comply.** Copy the header verbatim from `docs/shared/copyright.py`; place it at the
very top, before the module docstring; never hand-retype it.

**Verified by.** The self-healing header audit (to be ported in Phase 0). Until then,
reviewed by hand against `docs/shared/copyright.py`.

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

**Why.** A single, predictable home for front-end assets — independent of which blueprint
serves them — keeps the layout discoverable and matches the parent engagement's structure.

```
src/static/js/    *.js          # one file per UI module
src/static/css/   app.css
src/templates/    index.html
```

**Verified by.** Reviewed by hand (the directory layout); a misplaced asset shows up as a
404 in the e2e smoke suite, which loads every script.

---

## Change log

- 2026-06-25 — Added R7 (front-end assets under `src/static` / `src/templates`).
- 2026-06-22 — Created for MKM-ModelRisk, adapting R1–R6 from the parent engagement.
  R6 reframed around the `src/database/` event store. Mechanical audits (R1/R2/R4/R5/R6
  gates) to be ported in Phase 0.
