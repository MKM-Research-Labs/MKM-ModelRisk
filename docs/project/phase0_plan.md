# Phase 0 — Contract & Collector Foundation (detailed plan)

Part of the ModelRisk / PhysicalRisk consolidation (see
`ModelRisk_PhysicalRisk_Migration.md`). Phase 0 stands up the **generic ingest
spine** in ModelRisk and proves it end-to-end on one artifact, so every later
phase just replicates a proven pattern.

## Goal & exit criterion

**Goal:** a working, generic ingest pipeline — envelope → schema validation →
provenance capture → event append → projection → receipt — demonstrated on one
reference artifact.

**Exit criterion (the demo that means Phase 0 is done):** PhysicalRisk, using the
new `modelrisk-scan` library, POSTs a **data-lineage** manifest to a dev
ModelRisk instance →

- it is schema-validated, provenance-stamped, appended to the event store, and
  visible via `GET /api/ingest/status/data-lineage`;
- re-posting identical content is an **idempotent no-op** (no new event);
- a malformed payload returns `422` with structured errors and appends
  **nothing**.

**Guardrail — no production data moves.** Phase 0 uses **sample** payloads only.
Real onboarding of PhysicalRisk's current state is Phase 4.

## Decisions (accepted defaults)

| Decision | Choice | Rationale |
|---|---|---|
| Reference vertical | **data-lineage** | Net-new (no reconcile with an existing domain), has a real runtime producer, simple to store |
| Contract format | **JSON Schema docs**, validated server-side with `jsonschema` | Single source of truth; language-agnostic for future Moody's producers; no spec/validator drift |
| `modelrisk-scan` home | **`packages/modelrisk-scan/`** in the ModelRisk repo, own `pyproject.toml` | Single ownership, independently `pip install -e`-able, publishable to a private index later |
| Producer auth | **Shared-token header stub** for Phase 0 | Unblocks the pipe; real API-key/mTLS is a later hardening item |

---

## Architecture fit (ModelRisk conventions this follows)

ModelRisk is CQRS + event sourcing: the append-only `events` log is the source of
truth; Postgres read-model **views** are derived and fully rebuildable. A new
capability is a **write-domain** = `_state.py` (pure fold) + `_rules.py` (pure
`decide_*`) + `commands.py` (`load → decide → record` via `append_event`) +
`projection.py` (`rebuild_*_view` via `replace_view`) + a numbered migration +
an HTTP blueprint. Events append with `append_event(*, aggregate_type,
aggregate_id, event_type, payload, actor, reason, expected_version)`; the `actor`
string is the recorded attribution. Coding rules: **R1** params only in
`config/`, **R6** all DB access through `src/database`, **R7** front-end under
`src/static`/`src/templates`; every module carries the MKM licence header;
coverage gate **99%**; source files **< 300** lines, test files **< 400**.

---

## Workstream A — Freeze the contract

Pure files, **no DB** — doable fully offline.

| File (new) | Contents |
|---|---|
| `contracts/ingest/v1/envelope.schema.json` | `provenance` (`source_repo, commit, producer, producer_version, generated_at`) + `payload` |
| `contracts/ingest/v1/model_inventory.schema.json` | `metadata, models[], model_chain, tiering_matrix` |
| `contracts/ingest/v1/data_lineage.schema.json` | `runs, steps` |
| `contracts/ingest/v1/field_lineage.schema.json` | `version, reports → sections → fields` |
| `contracts/ingest/v1/document.schema.json` | PDF upload metadata (`model_id, doc_type, title, …`) |
| `contracts/README.md` | Envelope, versioning policy (additive-only within v1; breaking ⇒ v2), provenance semantics |

**Acceptance:** a round-trip test validates the *actual* current PhysicalRisk
JSON (`data_lineage.json`, `model_inventory.json`, `field_lineage_registry.json`)
against these schemas — proving the frozen contract matches what the producer
already emits.

## Workstream B — Ingest spine (server): `src/ingest/` + reference domain

Two aggregates — a generic **receipt** and the reference **manifest**.

| File (new) | Role |
|---|---|
| `src/ingest/_envelope.py` | Parse/validate envelope, extract `provenance` + `payload`, compute `content_hash` (sha256 of canonical payload) |
| `src/ingest/_validate.py` | Load `contracts/` schemas, validate payload (→ `SchemaValidationError`); registry of per-artifact **cross-ref** validators. Phase 0 implements the data-lineage internal-consistency check (every `runs[*]` step exists in `steps`); chain/field validators are registered stubs, filled in Phase 2/3 |
| `src/governance/data_lineage/{_state,_rules,commands,projection,__init__}.py` | Reference write-domain: `AGGREGATE_TYPE="DataLineageManifest"`, event `DataLineageIngested`, `aggregate_id = source_repo`; projection `data_lineage_view` (repo → latest manifest) |
| `src/ingest/receipt/{_state,_rules,commands,projection,__init__}.py` | `AGGREGATE_TYPE="IngestReceipt"`, events `PayloadIngested`/`PayloadRejected`, `aggregate_id = f"{artifact}:{source_repo}"`; projection `ingest_receipts_view` |
| `config/ingest.py` | Accepted artifacts, max payload size, contract dir (path via `config/paths.py`), dev token (**R1**) |
| `src/identity/` (extend) | `SOURCE_INGEST="ingest"` + `ingest_principal(provenance) → Principal(actor=f"ingest:{repo}", source="ingest")` |
| `src/database/migrations/0006_ingest_views.sql` | `ingest_receipts_view` + `data_lineage_view`, standard `TEXT PK + JSONB data + GRANT … TO mkm_app` |

**Provenance & idempotency:** the envelope's `provenance` block is written into
every event payload (full detail) *and* summarised on the receipt; `actor =
ingest:<repo>` gives quick attribution. Idempotency key =
`(artifact, source_repo, content_hash)`: before appending, load the
`IngestReceipt` stream — if the last `content_hash` matches, return the existing
receipt with **no new events**. Ingest commands are deliberately **not** in
`config/commands.py` confirm-lists (machine-to-machine; no confirm-to-amend).

## Workstream C — HTTP endpoints: `src/web/api_ingest/`

Multi-file blueprint, exactly like `api_mrc/`.

- `_bp.py` → `Blueprint("ingest", __name__, url_prefix="/api/ingest")`;
  `__init__.py` side-effect-imports the route modules.
- `data_lineage.py` → `POST /data-lineage`: `json_body()` → envelope parse →
  validate → `dispatch("ingest_data_lineage", …)` → `rebuild_data_lineage_view()`
  + receipt → `201` (or `200` idempotent).
- `status.py` → `GET /status/<artifact>` reads `ingest_receipts_view`.
- `documents.py` (multipart PDF upload) is **deferred to Phase 5** with the
  model-doc workflow. The receipt aggregate keys on `(artifact, source_repo)`,
  which fits per-repo lineage cleanly but not per-document uploads (each doc is
  distinct); documents get their own aggregate when that workflow is built, so a
  throwaway minimal endpoint now would be rework. The data-lineage round-trip is
  the Phase 0 exit criterion and does not need it.
- `src/web/app.py` → register `ingest_bp`; add
  `@app.errorhandler(SchemaValidationError) → ({"error":…, "details":[…]}, 422)`.

## Workstream D — `modelrisk-scan` client package: `packages/modelrisk-scan/`

Runs in the **producer**, so it never touches ModelRisk's DB (HTTP only). Owns
its own `pyproject.toml`.

| Module | Role |
|---|---|
| `modelrisk_scan/manifest/` | Generalised engine lifted from PhysicalRisk `src/lineage/manifest/_core.py` — hashing, `record_step`, `save/repair` — with **topology injected** (constructor takes `DEPENDENCY_GRAPH`/`STEP_IO`) |
| `modelrisk_scan/client.py` | `IngestClient(base_url, token).push(artifact, payload, provenance)` — builds envelope, computes content-hash, POSTs, handles `200`/`201`/`422` |
| `modelrisk_scan/provenance.py` | Build provenance (repo, `git rev-parse HEAD`, producer, version, timestamp) |

**Wiring into PhysicalRisk:** `pip install -e ../ModelRisk/packages/modelrisk-scan`;
PhysicalRisk keeps its `_topology.py` and passes it in. **No producer is rewired
to actually push yet** — that is Phase 3. Phase 0 only proves the library +
round-trip with a sample.

## Workstream E — End-to-end smoke test (the exit criterion)

Integration test (`tests/e2e/` marker): boot/target a dev ModelRisk instance →
`modelrisk-scan` pushes a sample data-lineage manifest → assert `201` + receipt →
`GET /status/data-lineage` returns it → re-push identical → `200`, `read_stream`
length unchanged → push malformed → `422`, zero events appended.

---

## Sequencing

1. **A (contract)** first — pure files, everything pins to it.
2. **B (spine)** and **D (client)** in parallel once A is frozen.
3. **C (endpoints)** after B.
4. **E (smoke test)** after C + D — the go/no-go for Phase 0.

**Offline vs online:** A and most of D need no database. B/C/E need the DB up
(migrations + app run) — so those wait until the ModelRisk Postgres cluster on
"David SSD" is mounted and started via `bash scripts/pg.sh start`.

## Explicitly OUT of Phase 0

Rich console views (Model Chain / BCBS / RACI / lineage UI), the Inventory
sort/filter/stat-tiles, real producer rewiring in PhysicalRisk, real producer
auth, and any production data onboarding. Phase 0 is the *pipe + one proof*, not
the domains.

## Risks / notes

- **`jsonschema` dependency.** Adds ModelRisk's third runtime dep (currently
  `psycopg` + `flask`). Accepted, to keep the contract as a single source of
  truth. Alternative was pure-Python validators (more code, no dep).
- **Producer authentication.** Shared-token stub in Phase 0; real API-key/mTLS
  is a later hardening item and a prerequisite before any external (Moody's)
  producer.
- **Projection scaling.** Projections currently **full-rebuild from `read_all()`
  on every write**. Fine at current volumes; at lineage scale, switch to the
  already-provisioned-but-unused `projection_checkpoints` for incremental
  projection. Not a Phase 0 change — flagged for the record.

## Compliance checklist (per new module)

- MKM licence header on every new source file.
- **R1:** all parameters/paths in `config/` (`config/ingest.py`, `config/paths.py`).
- **R6:** DB access only via `src/database` (`append_event`, `read_stream`,
  `read_all`, `replace_view`, `read_view`) — no raw SQL in ingest code.
- **R7:** no front-end assets added in Phase 0 (API only).
- **R2:** keep source files < 300 lines, tests < 400 (split blueprints/domains
  as `api_mrc/` and the governance domains already do).
- **R3:** tests for every new module to hold the 99% coverage gate; the E2E
  smoke test carries the `e2e` marker.
