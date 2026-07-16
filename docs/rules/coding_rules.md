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

**How to comply.** Don't hand-retype it — run `python -m audit --fix-headers`, which rewrites
any non-compliant header in place from `docs/shared/copyright.py` (preserving a shebang, and
leaving a leading comment that isn't a licence header alone).

**Verified by.** The self-healing header audit (`audit/headers.py`): `header_findings()` gates
`python -m audit` and `tests/audit/test_audit_headers.py`; `apply_headers()` backs
`--fix-headers`. Scope is repo-wide — root-level files plus `HEADER_SCAN_DIRS` in
`config/audit.py` (`tests/` and `docs/` included), so the entry point and the test suite
cannot carry a stale licence while R5 passes.

The one-line notices are checked by `audit/notices.py` (`notice_findings()`), **reported
rather than gating** — the wording is prose and the comment syntax varies, so it is surfaced
for review instead of failing the build. `tests/audit/test_audit_headers.py` also asserts the
canonical block matches `LICENSE` verbatim, so the per-file header and the licence file
cannot drift apart.

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

## Change log

- 2026-07-16 — Relicensed to MIT (`LICENSE` at the repo root). R5 extended: the header is
  now propagated by `python -m audit --fix-headers`, its scope is repo-wide (root files,
  `tests/`, `docs/`), and every non-`.py`/`.js` file carries a one-line notice — checked,
  reported, by `audit/notices.py`.
- 2026-06-25 — Added R8 (avoid duplication / extract utilities; zero-tolerance across
  models). Extended R7 to forbid embedding JS/CSS in `.py` files.
- 2026-06-25 — Added R7 (front-end assets under `src/static` / `src/templates`).
- 2026-06-22 — Created for MKM-ModelRisk, adapting R1–R6 from the parent engagement.
  R6 reframed around the `src/database/` event store. Mechanical audits (R1/R2/R4/R5/R6
  gates) to be ported in Phase 0.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
