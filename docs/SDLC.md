# MKM-ModelRisk — Software Development Lifecycle Protocol

**Document owner:** MKM Research Labs
**Applies to:** All changes to MKM-ModelRisk (`src/`, `config/`, `tests/`, `docs/`)

Adapted from the MKM engagement SDLC for this repo: a generic, model-agnostic
model-risk-governance platform, event-sourced on PostgreSQL. The controls below
support BCBS 239 Principles 3 (accuracy), 5 (timeliness) and 6 (adaptability) as
they apply to the governance platform's own software.

---

## 1. Development workflow

### 1.1 Branches

| Branch | Purpose | Merge target |
|--------|---------|-------------|
| `main` | Production-ready code. | — |
| `feature/<topic>` | New capabilities | `main` |
| `fix/<topic>` | Bug fixes | `main` |
| `refactor/<topic>` | Structural change, no behaviour change | `main` |

### 1.2 Commit discipline

- Atomic commits — one logical change each.
- Conventional messages: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`.
- Never commit secrets, `.env`, or credentials.

---

## 2. Quality gates

All gates are mandatory before merge to `main`.

### Gate 1 — Tests & coverage

```bash
source .venv/bin/activate
python -m pytest --cov --cov-report=term-missing
```

- **All tests pass.**
- **Coverage ≥ 99%** (`fail_under = 99`; `core = "ctrace"` — see coding rule R3).
- New code ships with tests in the same stage. Tests are deterministic — no network,
  no reliance on wall-clock time, no inter-test ordering dependencies. The event log is
  reset between tests by the `conftest` fixture.

### Gate 2 — Coding-rule audits (Phase 0, once ported)

The self-healing/structural audits enforce R1–R6 mechanically: canonical copyright header,
≤300-line files, no logic in `__init__.py`, parameters only in `config/`, and data access
only via `src/database/`. Until ported, these are reviewed by hand against
`docs/rules/coding_rules.md`.

### Gate 3 — Live verification (when the change is observable)

For changes to the web layer, run the console and confirm the behaviour:

```bash
docker compose up -d            # PostgreSQL on :5433
python -m src.web               # console on :5070
```

Confirm the confirm-to-amend flow, actor attribution, and that the audit trail records the
change.

---

## 3. Architecture invariants

These are not negotiable; a change that breaks one is a bug.

- **The event log is the source of truth.** All state is derived by replaying events;
  read models (projections) are rebuildable and never authoritative.
- **Immutability is enforced by the database.** The runtime role may append and read
  events but cannot `UPDATE`/`DELETE`/`TRUNCATE` them; each event chains to the prior
  event's hash so tampering is detectable (`verify_chain`).
- **Every mutation is attributed and confirmed.** Commands run through `dispatch`, which
  refuses to act without confirmation and records the SSO-resolved actor and reason.
- **All persistence is behind `src/database/`** (coding rule R6).

---

## 4. Adding a governance aggregate

1. `_state.py` — a pure fold (`apply`) over the aggregate's events.
2. `_rules.py` — pure `decide_*` functions returning `(event_type, payload)` or raising
   `DomainError`; no I/O.
3. `commands.py` — handlers that load the stream, rebuild state, validate, and append with
   optimistic concurrency, recording actor + reason.
4. `projection.py` — a read model rebuilt from the log, plus query functions.
5. A numbered SQL migration for the projection table + grants.
6. Tests for each layer to ≥99% coverage (pure rules unit-tested with no I/O).

---

## 5. Pre-merge checklist

```
[ ] python -m pytest --cov                 — all pass, coverage ≥ 99%
[ ] New parameters in config/, not inline  — R1
[ ] No file exceeds 300 lines              — R2
[ ] No logic in __init__.py                — R4
[ ] Canonical copyright header on new files — R5
[ ] No data access outside src/database/   — R6
[ ] Conventional commit messages
[ ] No secrets or .env committed
```
