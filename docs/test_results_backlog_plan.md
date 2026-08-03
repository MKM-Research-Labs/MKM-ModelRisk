# Test Results Documentation Backlog — Project Plan

**Author:** governance remediation stream · **Date:** 2026-08-01
**Goal:** clear the Test Results documentation gap on the 17 models that reached
ModelRisk without it, honestly and with minimal effort.

---

## 1. The key finding

17 models have no Test Results document in ModelRisk (confirmed against the live
inventory; matches the audit). **All 17 already have a rendered `test_results.pdf`
(and its `.tex` source) on disk** under PhysicalRisk `docs/models/<folder>/`.

So this is a **filing exercise, not a generation exercise** — the same shape as
the GH-001 completion, not the EF-001 one. No test suites need to be re-run and no
PDFs need rendering. The bulk `migrate_phys` document sweep simply ran before
these test PDFs existed (they and the migration History docs are both dated
2026-07-29), so they were never picked up. Nothing was lost.

## 2. The findings-per-model multiplier — the honest version

Filing one `test_results.pdf` legitimately clears, per model:

* the **Test Results** document finding (the ~5–6pt rating lift), and
* the **Unit Test** document finding — the same PDF is unit-test evidence, filed
  under the Unit Test category (as done for EF/GH/PF/ST/TC), and
* the **unit_tests = Yes** declaration.

What the *same upload* does **not** honestly clear:

* **Integration Test** document — that is an interoperability *handover*
  (`model_handoff` aggregate), not the test PDF. 15 of the 17 already carry
  handovers, so `integration_tests = Yes` is genuinely backed for those; the two
  without any (FIRE-001, SEIS-001) get `integration_tests = No`.
* **Benchmark Test** document / `benchmark_tests` — no benchmarking has been done
  for these models, so `benchmark_tests = No` and the finding **stays open**
  (correctly Red). We do not file a benchmark doc we do not have.

Net honest clearance per model ≈ 3 findings (Test Results doc, Unit Test doc,
unit-test declaration) plus the integration declaration where handovers exist.

## 3. Per-model mapping (all 17)

| Model | Folder (`docs/models/`) | `test_results.pdf` | Intg handovers | → integration_tests |
|---|---|---|---|---|
| MKM-BRI-001  | bri_resilience     | yes | 2 | Yes |
| MKM-DD-001   | flood_risk         | yes | 2 | Yes |
| MKM-DE-001   | delta_engine       | yes | 4 | Yes |
| MKM-FC-001   | flood_classifier   | yes | 6 | Yes |
| MKM-FIRE-001 | fire_resilience    | yes | 0 | **No** |
| MKM-FPO-001  | flood_poly         | yes | 1 | Yes |
| MKM-GHD-001  | gaugehd_synthetic  | yes | 1 | Yes |
| MKM-IP-001   | insurance_premium  | yes | 1 | Yes |
| MKM-MP-001   | mortgage_pricer    | yes | 3 | Yes |
| MKM-PR-001   | prs_pricing        | yes | 4 | Yes |
| MKM-PV-001   | property_valuation | yes | 1 | Yes |
| MKM-RA-001   | risk_assessment    | yes | 4 | Yes |
| MKM-SEIS-001 | seismic_resilience | yes | 0 | **No** |
| MKM-SG-001   | storm_gauge        | yes | 6 | Yes |
| MKM-SI-001   | storm_intensity    | yes | 4 | Yes |
| MKM-SP-001   | spatial_model      | yes | 1 | Yes |
| MKM-SS-001   | storm_multi        | yes | 3 | Yes |

All 17 currently have `validation_date` blank and validation questions at 2/0/7
(PR-001 at 3/0/6).

## 4. Phase 1 — mechanical filing (do first)

One parameterised, idempotent script (mirroring `attach_sensitivity_docs` /
`complete_pf_st_governance`) over all 17:

1. file `docs/models/<folder>/test_results.pdf` → **Test Results** category;
2. file the same PDF → **Unit Test** category (`unit_tests_MKM-<ID>.pdf`);
3. set `unit_tests = Yes` (all 17);
4. set `integration_tests` = Yes (15) / No (FIRE-001, SEIS-001) per the table;
5. set `benchmark_tests = No` (all 17);
6. add a test, apply live, commit explicit paths.

**Prerequisite:** spot-check 3–4 of the on-disk `test_results.pdf` are genuine and
current (not stale stubs) before the bulk file. Read-only from PhysicalRisk; no
writes to `data/`.

**Effort:** one script, one session. Clears 17 Test Results + 17 Unit Test doc
findings + the unit/integration declarations.

## 5. Phase 2 — full governance completion (larger, judgement)

Model-by-model, honest, exactly as done for PF/ST/TC-001:

* `validation_date` + `recertification_date` (anchored to each model's build date);
* all 9 validation questions recorded honestly — VQ-005 (data quality), VQ-008
  (benchmarking), VQ-009 (independent validation) stay Not Addressed;
* `version_history` / `change_history` where blank.

This is where the remaining rating lift beyond the document findings comes from.
It is **not** fully templatable — each model needs reading to write honest VQ
rationales — so run it in tranches of ~5 models per session.

## 6. Sequencing

| Phase | Scope | Effort | Order |
|---|---|---|---|
| 1 | File Test Results + Unit Test, set 3 declarations, all 17 | 1 script / 1 session | first — biggest lift per effort |
| 2 | Dates + 9 VQs + history, per model | 3–4 tranches of ~5 | after Phase 1 |

## 7. Standing constraints

* **Honesty:** no inflated VQ or benchmark statuses; real evidence only; open
  items stay open with a rationale.
* **Commits:** explicit paths only (the copyright self-heal mutates files during
  test runs — never `git add -A`).
* **Pushes:** the user pushes; commit to `main` and wait for the go-ahead.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
