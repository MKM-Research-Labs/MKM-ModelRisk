# ModelRisk — Remediation Project

**Status:** draft for review
**Owner:** MKM Research Labs
**Date:** 2026-07-18
**Origin:** Sister analysis to a day spent fixing the same class of issues in
PhysicalRisk. ModelRisk was seeded by replicating much of PhysicalRisk, so this
plan checks ModelRisk for every failure mode found there and adds the
*preventive* controls PhysicalRisk lacked.

---

## 1. Headline

**ModelRisk is in far better shape than PhysicalRisk was** — it was born MIT,
the git history is tiny and clean, and the worst PhysicalRisk bugs (restrictive
headers, the header-audit prune bug, tracked test artifacts, the exit-code bug)
either don't exist here or can't, because the architecture differs.

The real risk is different and more subtle: **migration is still live** (HEAD is
`feat(migration): migrate the model chain from PhysicalRisk`). Every file copied
from PhysicalRisk is a chance to import a bug that was fixed in PhysicalRisk only
*today*. And ModelRisk has **almost no automated guard-rails** (no CI, no header
enforcement, no preventive gitignore), so an imported problem would land silently
and stay.

So this is less "clean up a mess" and more "install the guard-rails before the
next migration commit brings the mess in."

---

## 2. What's already right (verified 2026-07-18)

| Area | State |
|---|---|
| Licence headers | MIT canonical, **0 trailing whitespace**, **0 restrictive headers** in tree |
| Coverage tracer | `core = "ctrace"` set — the sys.monitoring deflation bug is already avoided |
| Coverage gate | `fail_under = 99` set in pyproject |
| DB single-seam rule | **0** files with direct SQL/SQLAlchemy outside `src/database/` |
| Tracked generated artifacts | **none** — no `test_history.json`, `test_results.*`, `test_report.*`, LaTeX intermediates, or tracked `.pdf` |
| `data/` in git | never committed (0 commits touch it) |
| `.git` size | 5.7 MB / 200 commits |
| Entrypoint | `app.py` is a 34-line Flask launcher — no CLI test-orchestrator, so PhysicalRisk's exit-code and test-command bugs are structurally absent |
| Audit-PDF generators | not replicated — so PhysicalRisk's evidence-integrity issues (stale-e2e cover figure, lineage PASS/ISSUES contradiction) don't apply |

Do not "fix" any of these. They're the baseline to protect.

---

## 3. Findings — by severity

### 🔴 P1 — No CI. Nothing is enforced.

There is **no `.github/` directory at all**. `fail_under = 99`, header
correctness, the DB-single-seam rule, and "do the tests even pass" are enforced
only when a human remembers to run `pytest --cov` locally. PhysicalRisk had a
`ci.yml` with a file-backend lane *and* a Postgres-parity lane.

This is the root finding: without CI, every other control in this document is a
suggestion, and every latent issue below drifts in unnoticed. **Fix this first —
it's the thing that keeps the rest fixed.**

### 🟠 P2 — Preventive `.gitignore` is missing.

`.gitignore` covers **neither test artifacts nor `data/`**. Nothing generates
those *today*, which is exactly why it looks fine — but the doc/test generators
are among the things being migrated from PhysicalRisk, and the moment they arrive
they will write `test_history.json` (38 MB/run in PhysicalRisk), `test_results.*`,
LaTeX intermediates, and logs straight into a tree that tracks them. In
PhysicalRisk this silently added ~1 GB of *uncompressed* history (≈15.6 MB packed)
across 44 versions before anyone noticed.

Add the rules **now**, before the generators land. Cost: minutes. See §4.

### 🟠 P2 — No header-enforcement machinery, during active migration.

Headers are all clean MIT *right now*, but nothing keeps them that way — there is
no self-heal/audit (PhysicalRisk's `copyright_headers` audit is not ported). This
matters specifically because **files are being copied from PhysicalRisk, which
carried the restrictive non-commercial header until today**. A migration commit
could drag a restrictive or malformed header in and nothing would catch it — the
exact contradiction (MIT `LICENSE`, non-MIT file headers) we spent today undoing.

Port the header check (the *fixed* version — see the prune-bug note in §6) as a
CI test, or a lightweight standalone check. It does not need the full self-heal;
a read-only "every header matches canonical" gate is enough.

### 🟡 P3 — No e2e timeout.

15 e2e tests, `pytest-timeout` not declared, no timeout config. In PhysicalRisk a
single Playwright driver hang wedged the whole suite for 89 minutes and destroyed
the run's evidence. Add `pytest-timeout` and a per-test timeout so a hang fails
one test, not the run.

### 🟡 P3 — No live-service preflight.

`src/database/` seam exists but there is no `postgres_reachable`-style preflight.
If integration/e2e tests need Postgres and it's down, they skip and coverage
silently drops below the gate — read as a test gap, not a missing service (cost
PhysicalRisk a 17-minute misdiagnosis). Lower severity here because `app.py` is
not the test orchestrator, so the blast radius is smaller — but the same
skip-then-miss dynamic applies to whatever runs the DB-backed tests.

### 🟢 P4 — Orphaned 3.3 MB blob in history.

`legacy/docs/models/governance_data/model_audit_log.json` (3.3 MB) was committed
(`e501550` "stage governance code into legacy/") then stripped (`3d98d46`). It's
orphaned in history — ~58% of the (tiny) `.git`, but only 3.3 MB absolute.
Notably the *same pattern* as PhysicalRisk's bloat: a large JSON committed then
removed. Not worth a history rewrite on its own; fold it into any future rewrite,
or leave it. (The `legacy/` reference in `risk.py:79` is only a comment — no live
dependency.)

---

## 4. The preventive `.gitignore` (ready to apply)

```gitignore
# Generated test/audit artifacts — regenerated every run, never versioned
docs/models/*/test_results.*
docs/models/test_results/test_report.*
**/test_history.json
*.aux
*.toc
*.out
logs/*.log

# Local data / outputs
data/
```

Tune paths to ModelRisk's actual layout as the generators are migrated — the
point is to have the rules in place *before* the first artifact is written.

---

## 5. Phased plan

| Phase | Work | Why this order |
|---|---|---|
| **0. CI skeleton** | `.github/workflows/ci.yml`: lint (ruff) + `pytest --cov` with the 99% gate, on push/PR. Add a Postgres service lane if DB-backed tests exist. | Nothing else stays fixed without this. One file, biggest leverage. |
| **1. Preventive gitignore** | Apply §4. | Cheap; must precede the generator migration. |
| **2. Header gate** | Port PhysicalRisk's header check (prune-bug-free) as a CI test asserting every `.py`/`.js` matches the MIT canonical. | Protects the clean header state during ongoing migration. |
| **3. Test-robustness** | Add `pytest-timeout` + config; add a DB preflight or explicit skip-with-reason for DB-backed tests. | Prevents hangs and silent coverage misses. |
| **4. Migration checklist** | A standing checklist (below) applied to every PhysicalRisk→ModelRisk port. | Turns today's lessons into a repeatable filter. |
| **5. History (optional)** | Purge the orphaned 3.3 MB blob if/when any rewrite happens. | Low value; defer. |

---

## 6. Migration hygiene checklist (the highest-leverage item)

Migration from PhysicalRisk is active. Before merging any ported code, verify it
does **not** carry these PhysicalRisk defects — several were only fixed on
2026-07-18, so anything copied earlier likely still has them:

- [ ] **Headers** — MIT, not the old non-commercial block; no trailing whitespace
      (PhysicalRisk's canonical had 3 trailing spaces that propagated to 2,500 files).
- [ ] **Header-audit walker** — if the audit is ported, confirm the fix: prune
      `data` **only at repo root**, not any directory named `data` at any depth
      (the old code hid `tests/data/`'s 50 files from the sweep).
- [ ] **No generated artifacts staged** — no `test_history.json`, `test_results.*`,
      `test_report.*`, `.aux/.log/.out/.toc`, or run logs added to git.
- [ ] **Entrypoint exit codes** — if any CLI orchestrator is ported, confirm it
      returns non-zero on failure and the caller propagates it (PhysicalRisk's
      `app.py` discarded the return code, so `test` exited 0 on failures).
- [ ] **Coverage tracer** — `core = "ctrace"` preserved (already correct here).
- [ ] **Audit reports** — if PhysicalRisk's report generators are ported, verify
      cover-page metrics read the *same* source as the detail sections and
      fail-closed on missing data (PhysicalRisk's cover read one check while the
      body read another, and defaulted a missing file to green PASS).
- [ ] **DB access** — all through the `src/database` seam; no direct SQL
      (currently clean — keep it that way).

---

## 7. Open decisions

1. **CI scope** — minimal (lint + coverage) now, or the fuller PhysicalRisk shape
   (file + Postgres-parity lanes) from the start? Recommend: start minimal, add
   the Postgres lane when DB-backed tests exist.
2. **Header enforcement** — port the full self-heal, or a read-only CI gate only?
   Recommend read-only gate — ModelRisk's headers are already clean, so it only
   needs to *stay* clean, not be repaired.
3. **DB preflight** — build one, or rely on clear skip-reason messages + the CI
   Postgres lane guaranteeing the service is up in the gated run? Recommend the
   latter; it's simpler and CI is where the gate actually bites.
4. **The 3.3 MB blob** — clean now (needs a small history rewrite + force-push) or
   defer to a future rewrite? Recommend defer.

---

## 8. Notes

- All findings are read-only observations; nothing in ModelRisk was modified to
  produce this plan.
- Severity reflects *likelihood × cost given active migration*, not present-day
  breakage — most of these are latent, which is the point: fix them while they're
  still cheap.
- Sanity-check every number before acting. In the PhysicalRisk exercise a
  "1 GB" figure turned out to be 15.6 MB packed; measure the real cost before
  spending effort on it.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
