# `legacy/` — staged source from PhysicalRisk

This folder holds the **governance/regulatory code extracted from the
PhysicalRisk repo** as a staging area. It is **not** the production layout and is
not expected to run as-is. Over time, the relevant pieces will be refactored and
moved into `src/` (and `docs/`, `tests/`) per the build plan in
[`../docs/mkm_modelrisk_extraction_plan.md`](../docs/mkm_modelrisk_extraction_plan.md).

> Source of truth for the design: the extraction plan. This `legacy/` tree is
> raw reference material to port *from*, not the target architecture. In
> particular, MKM-ModelRisk is **model-agnostic** — anything flood/PRS-specific
> in here (notably `tools/cdm_property_editor` pricing) is reference only and
> will be dropped or generalised, not carried forward verbatim.

## What was brought across

| Path | Origin (PhysicalRisk) | Disposition (see plan §3) |
|------|-----------------------|---------------------------|
| `src/routes/governance/` | model-risk governance API (inventory, MRC, BCBS239, RACI, audit, documents, bibliography, lineage) | REBUILD on event-sourced/CQRS core |
| `src/lineage/` | manifest / validation / field-usage (RED-AMBER-GREEN) | GENERALIZE — drop the flood pipeline DAG |
| `src/cdm_edit/` | schema-driven edit/validation engine | GENERALIZE |
| `src/static/js/governance/` + `modelgovernance-panel.js` | governance UI panels (26 modules) | MOVE → add confirm-to-amend |
| `docs/models/{bcbs239,mrc_tor,parameter_inventory,test_results/generator}` | regulatory doc generators (LaTeX→PDF) | GENERALIZE |
| `docs/models/full_audit/` | 9-section consolidated audit (incl. self-healing copyright, path, data-access gates) | MOVE — repo self-governance |
| `docs/models/{init_audit,hardcoding,embedded_js,data_lineage,duplication}` | standalone code-quality / lineage audits | MOVE / GENERALIZE |
| `docs/models/governance_data/` | seed JSON (inventory, audit log, MRC, BCBS239, RACI, bibliography) | reference for schema shapes; replaced at build |
| `docs/rules/coding_rules.md` | coding rules R1–R6 | MOVE — governs the new repo |
| `docs/shared/` | canonical copyright header + shared helpers | MOVE |
| `config/path/` | path registry (single source of truth for path audit) | GENERALIZE |
| `tools/cdm_property_editor/` | standalone CDM asset-review tool | DROP / REBUILD-lite (reference for the generic model-record editor) |
| `tests/routes/governance/`, `tests/routes/lineage/`, `tests/lineage/`, `tests/cdm_edit/`, `tests/e2e/test_governance.py`, `tests/commands/test_{copyright_headers,path_definitions,data_access}_report.py` | governance + audit-gate tests | MOVE → extend to ≥99% on the new core |

## What was deliberately excluded

- All analytical model code (`src/models/`, `src/port/rand`, `src/loaders/`,
  `src/reports/`, analytics routes) — stays in PhysicalRisk for the other engagement.
- LaTeX build artifacts (`*.pdf`/`*.aux`/`*.log`/`*.tex` output), the 38M
  `test_history.json`, `__pycache__`, and `.bak` files — generators kept, output dropped.

_Copied 2026-06-22 from `MKM-Research-Labs/PhysicalRisk`._
