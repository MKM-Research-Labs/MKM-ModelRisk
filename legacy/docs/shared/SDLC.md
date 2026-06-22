# MKM Research Labs — Software Development Lifecycle Protocol

**Document owner:** MKM Research Labs
**Effective:** 29 March 2026
**Applies to:** All changes to the PhysicalRisk codebase (src/, config/, tests/, docs/)

---

## 1. Purpose

This protocol defines the mandatory quality gates that every code change must
pass before reaching the `main` branch. The PhysicalRisk platform underpins
pricing, risk assessment, and regulatory reporting for physical-risk securities.
It is operated as a production system with corresponding SDLC rigour.

The controls below implement BCBS 239 Principles 3 (accuracy), 5 (timeliness),
and 6 (adaptability) as they apply to model and data-pipeline software.

---

## 2. Development Workflow

### 2.1 Branch Strategy

| Branch | Purpose | Merge target |
|--------|---------|-------------|
| `main` | Production-ready code. Protected — no direct pushes. | — |
| `feature/<ticket>` | New capabilities | `main` via PR |
| `fix/<ticket>` | Bug fixes | `main` via PR |
| `refactor/<ticket>` | Structural improvements (no behaviour change) | `main` via PR |

Every branch must originate from the latest `main`.

### 2.2 Commit Discipline

- **Atomic commits**: one logical change per commit.
- **Conventional messages**: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`.
- Never commit secrets, credentials, `.env` files, or data artefacts (`data/`).
- Never commit with `--no-verify`; fix hook failures at source.

---

## 3. Quality Gates

All gates are mandatory. A failing gate blocks merge to `main`.

### Gate 1 — Lint

```bash
ruff check src/ tests/
```

- Zero errors, zero warnings.
- Line length ≤ 120 characters.
- Import ordering enforced (isort-compatible).
- Runs automatically in CI (`lint` job) and should be run locally before push.

### Gate 2 — Unit & Model Tests

```bash
python app.py test --unit
```

- **All tests must pass** (currently ~6,500+ tests across 16 model groups).
- **Coverage ≥ 90%** (`fail_under = 90` enforced in `pyproject.toml`).
- New code must include tests. Target: every public function tested, every
  branch exercised.
- Tests must be deterministic — no network calls, no reliance on wall-clock
  time, no inter-test ordering dependencies.

**Test file conventions:**

| Rule | Rationale |
|------|-----------|
| Max 300 lines per test file | Maintainability; split into `_part1.py`, `_part2.py` |
| One `Test*` class per logical unit | Clear failure attribution |
| Fixtures in `conftest.py` | Shared setup, isolated state |
| Mock external I/O | Tests run without data/ or network |

### Gate 3 — Data Lineage Validation

```bash
python app.py test --lineage
```

- Every pipeline step recorded in `data_lineage.json`.
- No stale inputs (producer hash must match consumer's recorded input hash).
- Structural integrity: every `STEP_IO` input traceable to a producer within
  the step's transitive `DEPENDENCY_GRAPH` dependencies.

**When adding a new pipeline step:**

1. Add entry to `DEPENDENCY_GRAPH` in `src/lineage/manifest.py`.
2. Add entry to `STEP_IO` with correct inputs and outputs.
3. Ensure `_find_producer()` resolves the correct upstream writer for every
   input (especially for shared artefacts like `gaugets/` or `gauge.json`).
4. Wire `pre_hash_inputs()` / `record_step()` calls in `app/commands/port.py`.
5. Run `test_every_input_has_producer_in_transitive_deps` — it must pass.

### Gate 4 — E2E Browser Tests

```bash
python app.py test --e2e
```

- Playwright tests validate the full request cycle: Flask routes → JSON API →
  rendered HTML/JS panels.
- Required for any change touching routes, visual panels, or JS generation.
- Skipped in CI if Playwright browsers are not installed (but mandatory for
  release certification).

### Gate 5 — Full Audit Package

```bash
python app.py test --audit --pdf
```

Generates the complete audit artefact set:

| Artefact | Location | Contents |
|----------|----------|----------|
| `junit.xml` | `data/output/audit/` | Machine-readable test results |
| `coverage.xml` | `data/output/audit/` | Line-level coverage data |
| Coverage HTML | `data/output/audit/coverage/` | Browsable coverage report |
| Data Lineage Report | `data/output/audit/data_lineage_report.pdf` | BCBS 239 P3 compliance |
| Code Modularisation | `data/output/audit/large_file_report.pdf` | Files exceeding 300 lines |
| Code Duplication | `data/output/audit/code_duplication_report.pdf` | Copy-paste detection |
| Hard-Coding Audit | `data/output/audit/hardcoding_report.pdf` | Inline literals not in config/ |
| Full Audit Report | `data/output/audit/full_audit_report.pdf` | Combined governance summary |
| Per-model LaTeX | `docs/models/<model>/test_results.tex` | Model-level test evidence |

The audit must show:

- **0 test failures** (excluding xfail).
- **0 stale lineage steps**.
- **0 large files** exceeding 300 lines (or documented exemptions).
- **0 hard-coded parameters** outside `config/` (or precision-ok exemptions).

---

## 4. Model Documentation Requirements

Every analytical model in `src/models/` must have a corresponding documentation
package in `docs/models/<model_id>/`.

### Required Artefacts

| File | Purpose |
|------|---------|
| `model_spec.tex` | Mathematical specification, assumptions, limitations |
| `test_results.tex` | Auto-generated from `app.py test --audit` |
| `Makefile` | `make pdf` compiles the full model document |

### Model Inventory Registration

New models must be registered in the governance model inventory accessible via
`/api/v1/governance/models`. Each registration includes:

- Model ID (e.g. `MKM-DD-001`)
- Version, owner, review date
- Risk rating (auto-calculated, manually overridable)
- Validation questions and evidence
- Audit trail of all changes

---

## 5. Configuration Management

### 5.1 Parameter Governance

All tuneable parameters must reside in `config/*.py`:

| Config file | Scope |
|-------------|-------|
| `config/port.py` | Portfolio generation parameters |
| `config/models.py` | Model hyperparameters and thresholds |
| `config/visual.py` | Visualisation settings |
| `config/format.py` | Display formatting |
| `config/server.py` | Flask / server configuration |
| `config/path.py` | Directory paths |

**Never inline numeric constants in source files.** The hard-coding audit
(`hardcoding_report.pdf`) catches violations. Use `ALL_CAPS` names in config
and import explicitly:

```python
from config.port import SYNTH_DEDUP_DISTANCE_M
```

### 5.2 Pipeline Topology

The data pipeline topology is defined in two structures in
`src/lineage/manifest.py`:

- `DEPENDENCY_GRAPH` — step execution ordering (DAG).
- `STEP_IO` — declared inputs and outputs per step.

Any change to pipeline steps requires updating both structures and running the
structural integrity test (`test_every_input_has_producer_in_transitive_deps`).

---

## 6. Code Standards

### 6.1 Source File Size

Maximum **300 lines** per source file. When a module grows beyond this:

1. Identify logical sub-units (e.g. I/O, computation, rendering).
2. Create a package directory with `__init__.py` re-exporting the public API.
3. Split into focused sub-modules (each ≤ 300 lines).
4. Verify all imports and tests still pass.
5. The `large_file_report.pdf` audit must show zero violations.

### 6.2 Test File Size

Maximum **300 lines** per test file. Split with `_part1.py`, `_part2.py`
suffixes.

### 6.3 JavaScript Generation

All JS is generated server-side via Python f-strings. Mandatory rules:

- Escape all literal braces: `{{` and `}}` in f-strings.
- Never use single quotes inside JS strings generated by Python.
- Every panel's `get_js()` must pass `node --check` syntax validation.
- Contract D tests (`test_cross_iife_syntax.py`) enforce this automatically.

---

## 7. Pre-Merge Checklist

Before raising a Pull Request, the developer must verify:

```
[ ] ruff check src/ tests/                         — zero issues
[ ] python app.py test --unit                       — all pass, coverage ≥ 90%
[ ] python app.py test --lineage                    — no stale steps
[ ] python app.py test --e2e                        — all pass (if routes/visual changed)
[ ] python app.py test --audit --pdf                — clean audit package
[ ] New parameters in config/*.py, not inline       — hardcoding audit clean
[ ] New pipeline steps wired in DEPENDENCY_GRAPH    — structural test passes
[ ] New models registered in governance inventory   — model doc package created
[ ] No file exceeds 300 lines                       — modularisation audit clean
[ ] Commit messages follow conventional format      — clear change history
[ ] No secrets, data files, or .env committed       — git diff reviewed
```

---

## 8. CI Pipeline

GitHub Actions (`.github/workflows/ci.yml`) enforces Gates 1–2 on every push
and pull request to `main`:

```
push/PR → lint (ruff) → test (pytest + coverage) → upload artefacts
```

Gates 3–5 (lineage, E2E, full audit) are run locally before merge and during
release certification. The full audit PDF is archived with each release.

---

## 9. Release Certification

A release to production requires:

1. All 5 gates green on `main`.
2. Full audit PDF generated and archived.
3. Data lineage report showing all 15 pipeline steps consistent.
4. Model documentation current for any models changed in the release.
5. Governance model inventory updated with new version numbers.
6. Portfolio generation (`python app.py port --all`) completes with zero
   stale steps and zero data lineage warnings.

---

## 10. Incident Response

If a test failure is discovered after merge to `main`:

1. **Triage**: classify as data-state (stale portfolio), code regression, or
   environment issue.
2. **Hotfix branch**: `fix/<description>` from `main`.
3. **Root cause**: add a test that reproduces the failure before fixing.
4. **Fix forward**: never revert tests to make them pass — fix the underlying
   code.
5. **Audit**: run full audit after fix to confirm no collateral damage.
6. **Post-mortem**: update this protocol if the failure class was not covered.
