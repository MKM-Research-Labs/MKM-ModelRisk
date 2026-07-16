# MKM-ModelRisk — Extraction & Build Project Plan

**Status:** Draft v1 — 2026-06-22
**Owner:** risk@kerrshearer.co.uk
**Goal:** Stand up a new standalone repository, **MKM-ModelRisk**, containing a
**generic, model-agnostic model-risk-governance workflow** that can be cloned
into a client's repo. It captures model documentation, risk-assessment status,
MRC meetings, BCBS 239 self-assessment, RACI, audit trail, document control and
data lineage — backed by an **immutable, event-sourced (CQRS) store on
PostgreSQL**. Identity is provided by the **client's own SSO** (out of our
scope); every authenticated user may amend, but **all mutations require an
explicit confirmation dialog** and are attributed to the SSO-provided actor in
the immutable audit line.

> The analytical "model stuff" (hazard / flood / wind / fire / seismic / PRS /
> trading / valuation) is **explicitly out of scope** — it stays in PhysicalRisk
> for the other engagement. MKM-ModelRisk knows *nothing* about any specific
> model; it is the governance scaffolding *around* whatever models a client owns.

---

## 1. Locked decisions

| # | Decision | Choice |
|---|----------|--------|
| D1 | Product shape | Generic model-governance platform; **no flood/PRS pricing**. The CDM asset-review tool's pricing recompute is dropped; a generic "model record / artifact editor" replaces it. |
| D2 | Immutability | **Event-sourced (full CQRS)** — all state derived by replaying an append-only event log. The existing JSON "audit log" *becomes* the event stream. |
| D3 | Permissions | **No RBAC, no auth build.** Identity comes from the **client's SSO** (perimeter; out of scope). All authenticated users may amend; **every mutation requires a confirmation dialog**, and the SSO actor is recorded on the event. |
| D4 | Data store | **PostgreSQL-first**, all access through a single `src/database/` utility (coding rule R6). No direct SQL/JSON I/O anywhere else. |

---

## 2. Architecture overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser UI  (governance panels: Inventory · MRC · BCBS239 ·     │
│               RACI · Audit · Documents · Bibliography · Lineage)  │
└───────────────┬─────────────────────────────────────────────────┘
                │  requests (identity injected by client SSO at perimeter)
┌───────────────▼─────────────────────────────────────────────────┐
│  Flask API  (governance_bp)                                      │
│    └─ Actor resolver  → read SSO principal (header/session) →    │
│                         attach actor to every command            │
│       (UI: confirmation dialog gates every mutating action)      │
└───────────────┬─────────────────────────────────────────────────┘
                │  COMMANDS (CreateMeeting, UpdateModelField, …)
┌───────────────▼─────────────────────────────────────────────────┐
│  Command handlers  → validate → emit EVENTS                      │
└───────────────┬─────────────────────────────────────────────────┘
                │  append-only
┌───────────────▼──────────────────────┐   ┌──────────────────────┐
│  EVENT STORE  (Postgres, append-only) │──▶│  Projections /        │
│  events(id, aggregate, type, payload, │   │  read models          │
│         actor, ts, seq, prev_hash)    │   │  (current-state views)│
└───────────────────────────────────────┘   └──────────────────────┘
                ▲                                       │
                └────────── replay / rebuild ───────────┘
         (the event log IS the audit trail — one source of truth)
```

**Key properties**

- **Immutable by construction.** Events are append-only; `UPDATE`/`DELETE` are
  revoked on the event table at the DB-role level. Each event carries
  `prev_hash` (hash of prior event in the aggregate stream) → tamper-evident chain.
- **Audit trail = event log.** Today's `model_audit_log.json` is redundant; the
  event stream already records *who changed what, when, and why* for every
  aggregate. The "Audit" UI tab becomes a view over the event store.
- **Documents are content-addressed.** Every uploaded governance document is
  hashed (SHA-256) and stored immutably; new versions append, nothing is
  overwritten; every upload/access is an event.
- **All persistence via `src/database/`.** Event store, projections and the
  outbox all sit behind intent-named functions. Enforced by the ported
  data-access audit (R6, zero-tolerance gate).

### 2.1 Aggregates (event-sourced domains)

| Aggregate | Replaces today's | Example commands / events |
|-----------|------------------|---------------------------|
| `ModelInventoryEntry` | `model_inventory.json` per-model record | `RegisterModel`, `UpdateField`, `SetValidationStatus`, `OverrideRiskRating` |
| `ValidationAssessment` | validation_questions + overall_risk_rating | `AnswerValidationQuestion`, `RecalculateRiskRating`, `MRCOverride` |
| `MRCMeeting` | `mrc_meetings.json` | `ScheduleMeeting`, `AddAgendaItem`, `RecordMinute`, `LogDecision`, `RaiseAction`, `AttachDocument` |
| `BCBS239Assessment` | `bcbs239_assessment.json` | `ScorePrinciple`, `RecordGap`, `SetRemediation` |
| `RACIMatrix` | `raci_matrix.json` | `AssignRole`, `UpdateActivity`, `SetEscalationTrigger` |
| `GovernanceDocument` | `governance_documents.json` + files | `UploadDocument`, `SupersedeDocument`, `RetireDocument` |
| `BibliographyReference` | `bibliography.json` | `AddReference`, `UpdateReference`, `RemoveReference` |

### 2.2 Access model (no RBAC build)

- **Identity** is supplied by the **client's SSO** at the perimeter (reverse
  proxy / IdP). We do **not** build login, sessions, OIDC, or a user store.
- The API reads the SSO-provided principal (e.g. a trusted header or session
  attribute) via a thin **actor resolver** and attaches `actor` to every command.
- **Every authenticated user may amend** any governance record — there is no
  role enforcement in our code.
- **Every mutating action is gated by a confirmation dialog** in the UI
  ("You are about to change X from A to B. Confirm?"), and the confirmed change
  becomes an event stamped with the actor (and an optional reason).
- If the client later wants role restrictions, the command-dispatch seam is the
  single place to add an authorization hook — designed in, but not built now.

---

## 3. Component disposition (what moves, what changes, what's dropped)

Legend: **MOVE** = port largely as-is · **GENERALIZE** = port but strip
flood/model specifics · **REBUILD** = port the intent, new implementation
(event-sourced / RBAC) · **DROP** = leave in PhysicalRisk · **NEW** = net-new.

| Area | Source (PhysicalRisk) | Disposition | Notes |
|------|----------------------|-------------|-------|
| Governance routes | `src/routes/governance/` (25 modules, 50+ endpoints) | **REBUILD** | Same API surface, but handlers become command dispatchers; mutations require authenticated actor + RBAC. |
| Audit trail | `audit.py`, `model_audit_log.json` | **REBUILD** | Becomes a read view over the event store; no separate log. |
| Model inventory | `models.py`, `model_inventory.json` | **GENERALIZE** | Schema kept (generic model record); seed data emptied / replaced with a worked example, not flood models. |
| Validation / risk rating | `audit_validation.py`, `_helpers_risk.py` | **MOVE→REBUILD** | Risk-scoring logic ports; persistence becomes event-sourced. |
| MRC committee | `mrc.py` + `mrc_crud_*.py` + `mrc_pdf.py` | **REBUILD** | Full CRUD + PDF pack generation (reportlab) retained. |
| BCBS 239 / RACI | `compliance.py` | **MOVE→REBUILD** | Generic; no model-specific content. |
| Documents | `documents.py` | **REBUILD** | Content-addressed, immutable, versioned. |
| Bibliography | `bibliography.py` | **MOVE** | Generic reference manager. |
| Lineage framework | `src/lineage/` (manifest, validation, field_usage) | **GENERALIZE** | Keep the framework + RED/AMBER/GREEN field-impact concept; **drop** the hard-coded flood pipeline DAG/topology — becomes client-defined config. |
| Lineage routes | `src/routes/governance/lineage/` | **GENERALIZE** | Generic data/field lineage trace API. |
| CDM edit/validation | `src/cdm_edit/` | **GENERALIZE** | Keep schema-driven validation engine; decouple from flood CDM schemas. |
| CDM asset-review tool | `tools/cdm_property_editor/` | **DROP / REBUILD-lite** | The flood-PRS pricing recompute is dropped. Optionally rebuild a generic "model record editor" later (Phase 7). |
| Doc generators | `docs/models/{bcbs239,mrc_tor,test_results,parameter_inventory}` | **GENERALIZE** | BCBS239 + MRC ToR move ~as-is. Test-results generator generalised to run a *configurable* test command. Parameter-inventory generalised to read client config. |
| Full audit (9 sections) | `docs/models/full_audit/` | **GENERALIZE** | Test/coverage/modularisation/init/copyright/path/data-access sections move as-is; flood "data lineage" & "E2E" sections become generic. |
| Self-healing audits | copyright headers, path definitions, data access, hardcoding, embedded-JS, duplication | **MOVE** | Pure dev-infra; port as-is. These enforce the coding rules in the new repo. |
| Coding rules | `docs/rules/coding_rules.md` (R1–R6) | **MOVE** | Becomes the new repo's governance-of-itself. |
| Copyright header | `docs/shared/copyright.py` | **MOVE** | Canonical 19-line header + self-heal. |
| Config | `config/path/registry.py`, server, format | **GENERALIZE** | Keep path registry + audit hooks; drop flood/peril model config. |
| Frontend | `src/static/js/governance/` (26 modules) + `modelgovernance-panel.js` | **MOVE→REBUILD** | Port panels; add login/role-aware UI; wire to new auth. |
| Tests | `tests/routes/governance/`, `tests/e2e/test_governance.py`, audit gate tests | **MOVE→REBUILD** | Port + extend to ≥99% coverage (R3) incl. event-store, RBAC, projections. |
| Actor resolver + confirm dialog | — | **NEW** | Read SSO principal into `actor`; confirmation popup on every mutation. No login/RBAC build. |
| Event store / CQRS | — | **NEW** | Event table, append-only constraints, projection framework, replay. |
| Database utility | `src/database/` (concept) | **REBUILD** | Postgres-backed; single access point. |
| Migrations | — | **NEW** | Alembic (or equiv.) schema + role grants. |
| Packaging | — | **NEW** | Clone-ready: docker-compose (Postgres), `.env.example`, seed/bootstrap, README. |

**Explicitly NOT moving:** `src/models/`, `src/port/rand` generators, `src/loaders/`,
`src/reports/`, analytics routes (properties, commercial, propertyts, propertyhc,
prs, trading, gauges, counterparty, perils, visualization), and all flood/wind/
fire/seismic/typhoon config and data.

---

## 4. Phased plan & work breakdown

Each phase ends with: passing tests at **≥99% coverage** (R3), all coding-rule
audit gates green (R1–R6), and a short demo. Phases are sequential but 4–7 can
overlap once the spine (1–3) is in.

### Phase 0 — Repo scaffold & guardrails *(foundation)*
- Create `MKM-ModelRisk` repo; Python project skeleton, `app.py` CLI seam (`server`, `test`, `audit`, `db`).
- Port coding rules (R1–R6), `copyright.py`, and **all self-healing audits + their gate tests** *first* — the new repo polices itself from commit one.
- CI: pytest + coverage gate (`fail_under=99`, `core=ctrace` for the Py3.13 sys.monitoring bug), audit gates, copyright self-heal.
- `config/` package with path registry; `.env.example`; pre-commit.
- **Deliverable:** empty-but-governed repo; `app.py audit` green on itself.

### Phase 1 — Persistence & event-store spine *(D2 + D4)*
- `src/database/` utility: Postgres connection mgmt, all access behind intent-named functions.
- Event store schema: `events` table (append-only), `prev_hash` chain, per-aggregate sequence; **revoke UPDATE/DELETE** at DB-role level.
- Projection framework: register projector, rebuild-from-zero, incremental catch-up, outbox.
- Migration tooling (Alembic) + role grants (app role vs read role).
- **Deliverable:** can append events, replay them, rebuild a trivial projection; data-access gate green.

### Phase 2 — Actor resolution & confirm-to-amend *(D3, lightweight)*
- **Actor resolver:** read the SSO-provided principal from a trusted request
  source (configurable header / session attribute) into `actor`; sensible local
  fallback for dev. **No** login, sessions, OIDC, or user store built here.
- Command dispatch stamps every event with `actor` (+ optional `reason`) —
  replaces the old arbitrary `user` body field.
- **Confirmation gate:** a reusable confirm-dialog seam — no mutating endpoint is
  reachable from the UI without an explicit confirm; backend treats the confirmed
  request as the command. Spelled-out before/after summary in the dialog.
- Leave a single empty **authorization hook** at dispatch (future role rules) — designed in, not implemented.
- **Deliverable:** any field change shows a confirm popup; on confirm an event is
  written with the SSO actor; cancel writes nothing.

### Phase 3 — Governance domains (event-sourced) *(core value)*
Port each aggregate as commands → events → projection → API → tests. Suggested order:
1. **Audit/event-log view** (read side first — proves the spine).
2. **Model inventory** (`RegisterModel`/`UpdateField`/validation status).
3. **Validation & risk rating** (scoring logic + MRC override).
4. **MRC meetings** (full CRUD + agenda/minutes/decisions/actions/participants + PDF pack).
5. **BCBS 239** + **RACI**.
6. **Documents** (content-addressed, versioned, immutable).
7. **Bibliography**.
- **Deliverable:** full governance API on the event store, each domain demoable.

### Phase 4 — Lineage framework (generalized)
- Port manifest/validation/field-usage; replace flood DAG with a **client-defined topology config**.
- Generic data-lineage + field-lineage trace APIs.
- **Deliverable:** lineage works against a sample client topology; BCBS 239 lineage section renders.

### Phase 5 — Document generators & audit PDFs (generalized)
- BCBS 239 self-assessment PDF; MRC Terms-of-Reference PDF.
- Test-results generator → runs a **configurable** test command (the client's model test suite, not flood pytest).
- Full audit (9 sections) generalised; parameter-inventory reads client config.
- **Deliverable:** `app.py audit` produces the consolidated governance PDF set.

### Phase 6 — Frontend (confirm-to-amend)
- Port the 26 governance JS modules + panel; wire every mutating action through
  the shared **confirmation dialog** (before/after summary + optional reason).
- Wire to the new APIs; surface the event-log audit view. No login UI (SSO sits
  in front of the app).
- **Deliverable:** working browser UI; no amend without a confirm; e2e (Playwright) green.

### Phase 7 — Generic model-record editor *(optional, replaces CDM tool)*
- A schema-driven editor for model records/artifacts (the *generic* descendant of the CDM tool), **no pricing recompute** — RED/AMBER/GREEN field-impact tagging retained as a governance signal only.
- **Deliverable:** add/edit a model record with field-impact classification + full audit.

### Phase 8 — Hardening & client-handover packaging
- ≥99% coverage across event store, projections, RBAC, replay, tamper-detection tests.
- `docker-compose` (app + Postgres), bootstrap/seed (admin user, empty inventory, example model), backup/restore, README + ops guide.
- Tamper-evidence test: mutate an event row → chain verification fails → alarm.
- **Deliverable:** `git clone` → `docker compose up` → working governance platform.

---

## 5. Cross-cutting concerns

- **Coupling to the parallel JSON→Postgres migration.** That project is migrating
  PhysicalRisk's *operational* data; MKM-ModelRisk is Postgres-first from day one,
  so it does **not** inherit the file-backend seam. Shared learning: the
  `src/database/`-only access discipline (R6) and the data-access audit gate are
  common to both — reuse the gate code.
- **Immutability vs. corrections.** Event-sourcing never deletes; corrections are
  *compensating events* (`CorrectField`, `RetractDecision`) that preserve the
  original. The UI must make "supersede/correct" explicit — never "edit in place".
- **PII / access logging.** Reads of sensitive governance docs are themselves
  events (who viewed what) for the "perfect audit line".
- **Time.** Event timestamps are server-authoritative; never trust client clocks.
- **Backups / retention.** Append-only store + WAL archiving; define retention
  (regulatory minimums) before go-live.

---

## 6. Open questions for next session

1. **SSO actor handoff** — how does the client's SSO pass identity to the app
   (trusted header name? session attribute?) so the actor resolver knows where to read it.
2. **Postgres version & deployment** — managed (RDS/Cloud SQL) or self-hosted container?
3. **Does the generic model-record editor (Phase 7) ship in v1**, or is the governance API + panels enough for first delivery?
4. **Repo bootstrapping mechanics** — fresh `git init` (clean history) vs. `git filter-repo` to carry the relevant history of the ported files?

> Resolved: SSO is the client's; we build no auth/RBAC (D3). All users may amend,
> gated by a confirmation dialog.

---

## 7. Immediate next steps (once plan is approved)

1. Confirm Section 6 open questions (esp. SSO actor handoff + Phase 7 scope).
2. Scaffold the repo (Phase 0) — I can generate the skeleton, port the coding-rule audits + copyright self-heal, and stand up CI.
3. Phase 1 spike: event table + append/replay + one projection, to de-risk the CQRS core early.
```

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
