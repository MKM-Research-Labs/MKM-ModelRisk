# ModelRisk / PhysicalRisk Consolidation — Migration Approach

## Objective

Make **ModelRisk** the single system of record for model/product governance,
and reduce **PhysicalRisk** to a *producer* that feeds it. After migration:

- All regulatory state — model inventory, model chain, BCBS 239, RACI, MRC,
  audit trail, documents, bibliography, data lineage, field lineage — lives in
  the ModelRisk database and is worked on in the ModelRisk console.
- PhysicalRisk **generates artifacts** (model-documentation PDFs, lineage
  scans) and **pushes** them into ModelRisk. It no longer hosts any regulatory
  UI, CRUD, or `.json` persistence.
- The same contract lets *any* repo feed ModelRisk — including, later, a
  Moody's repo where the scans are produced by running Claude over their code.

This supersedes the earlier "generalise the four components and re-import them
as a pinned library" framing. Investigation of both codebases showed that model
is the wrong shape (see *Why not a shared library* below).

---

## Two seams, deliberately different

The integration between the two repos is **not** one boundary but two, chosen to
match what actually crosses them:

1. **A service seam (REST).** The stateful regulatory engine is a running
   ModelRisk instance. Producers talk to it over HTTP. This is the boundary for
   all *data and artifacts* (inventory records, lineage JSON, PDFs). It is
   language-agnostic, survives the producer being a separate process / repo /
   machine, and is the only thing that generalises to "run Claude in a Moody's
   repo and POST the result."

2. **A utility-library seam (pip).** The *stateless, generic* scanner helpers
   (today: the data-lineage manifest/hashing engine) are published by ModelRisk
   as a small installable package. Producing repos install it and run it locally
   with their own repo-specific config. This is how "keep a copy of the scanner
   utilities inside ModelRisk" is honoured **without** duplicating code into two
   repos that then drift: ModelRisk *owns* the generic version; PhysicalRisk
   *installs* it.

```
  PRODUCERS (PhysicalRisk today; a Moody's repo tomorrow)     MODELRISK (system of record)
  ┌───────────────────────────────────────────────┐          ┌──────────────────────────────────┐
  │ model-doc generator ──► PDFs ─────────────────┼── REST ──►│ POST /ingest/documents (blob)    │
  │ data-lineage engine  ──► data_lineage.json ───┼── REST ──►│ POST /ingest/data-lineage        │
  │ field/model scans    ──► *.json ──────────────┼── REST ──►│ POST /ingest/{...}               │
  │                                               │          │   ├ validate (generic)            │
  │ uses:  modelrisk-scan  (installed utility) ◄──┼── pip ───┤ publishes modelrisk-scan lib      │
  │ keeps: repo-specific topology / field maps    │          │   ├ append events (+ provenance)  │
  │                                               │          │   └ project → console views       │
  │ NO regulatory UI / CRUD / json (deleted)      │          │ MRC · BCBS · RACI · lineage views │
  └───────────────────────────────────────────────┘          │ semi-automatic gov workflow      │
                                                              └──────────────────────────────────┘
```

**Rule:** ModelRisk never imports from PhysicalRisk. Data flows up over REST;
the only thing flowing *down* is the `modelrisk-scan` utility package.

---

## Tab-by-tab migration matrix

The PhysicalRisk "Regulatory Compliance" console has eleven tabs. Their targets:

| Tab | Source in PhysicalRisk | ModelRisk today | Work required |
|---|---|---|---|
| **Inventory** | `model_inventory.json` (24 models) | exists (static table) | Reconcile data **+ build** sort, per-column filters, and Tier/Overdue/Due-Soon/Assessed stat tiles |
| **Model Chain** | `model_inventory.json` → `model_chain.links` ("string of pearls") | **none** | Net-new: schema + dependency-graph view |
| **BCBS 239** | `bcbs239_assessment.json` | **none** | Net-new domain + view |
| **RACI** | `raci_matrix.json` | fields only, no domain | Net-new domain + view |
| **MRC** | `mrc_meetings.json` etc. | **canonical** (event-sourced) | Reconcile data into existing MRC; **ModelRisk wins** |
| **Audit Trail** | `model_audit_log.json` (~3.5 MB) | event store is the audit spine | Fold legacy log in as imported events |
| **Documents** | `governance_documents.json` + `governance_docs/`, `mrc_uploads/` blobs | exists (+ `src/files/store.py`) | Migrate records + blobs |
| **Bibliography** | `bibliography.json` | exists | Migrate data |
| **Audit Reports** | PDF audit generators (`docs/models/full_audit/`) | `src/governance/mrc/pack.py` renders PDF | Generalise/port report builders |
| **Data Lineage** | `data_lineage.json` (runtime scanner) | **none** | Net-new sink + ingestion; producer stays in PhysicalRisk |
| **Field Lineage** | `field_lineage_registry.json` (hand-authored) | **none** | Net-new sink + ingestion; producer stays in PhysicalRisk |

Net-new builds in ModelRisk: **Model Chain, BCBS 239, RACI, Data Lineage,
Field Lineage.** Everything else already has a home and is a *data reconcile*.

---

## Producer responsibilities (what stays in PhysicalRisk)

PhysicalRisk keeps exactly the code that *generates* governance artifacts,
because that code is coupled to the PhysicalRisk pipeline and cannot be made
generic:

- **Model-documentation generation.** On model creation/change, build the model
  PDFs as today, then **upload them to ModelRisk** (`POST /ingest/documents`)
  instead of writing to a local folder. ModelRisk then runs the semi-automatic
  governance workflow (MRC scheduling, sign-off, RAG routing) on top.
- **Data-lineage scanning.** The manifest engine (`src/lineage/manifest/_core.py`
  — SHA-256 hashing of pipeline inputs/outputs at run time, driven by
  `app/commands/port/`) keeps running as a pipeline side-effect, but now **pushes**
  its manifest to `POST /ingest/data-lineage`. Its domain map
  (`src/lineage/manifest/_topology.py` — storm/flood/gauge step names) stays
  local.
- **Field-lineage / inventory data.** Hand-authored today. They are *pushed* to
  ModelRisk on change. If/when automated, the scanner is a producer-side job
  (this is the Claude-in-repo extraction path) that emits the same schema.

**Important reality check:** of the three "scanners", only data lineage is a real
runtime producer. `model_inventory.json` and `field_lineage_registry.json` are
hand-maintained JSON with *validators/readers* around them, not generators.
"Keeping the scanner in PhysicalRisk" therefore literally applies to data
lineage; for the other two, what PhysicalRisk keeps is the *authored source of
truth* (plus an optional future scanner) that it pushes upstream.

---

## The ingestion contract (REST)

Transport is **documented REST over HTTPS**, JSON bodies (multipart for blobs).
ModelRisk ships a thin optional Python client wrapping these calls; the contract
is the spec, so any stack can implement a producer.

### Common envelope — provenance on every payload

Every ingest request carries provenance, which becomes the BCBS 239 audit trail
and gives a reproducible link from a governed artifact back to the exact scan
that produced it:

```jsonc
{
  "provenance": {
    "source_repo": "PhysicalRisk",
    "commit": "d097faea…",
    "producer": "modelrisk-scan/data-lineage",
    "producer_version": "1.2.0",
    "generated_at": "2026-07-15T15:48:22Z"
  },
  "payload": { … artifact-specific schema below … }
}
```

Ingestion is idempotent per `(source_repo, artifact, content-hash)`; re-posting
identical content is a no-op. Each accepted payload appends an event and updates
the projection (ModelRisk is event-sourced, so imports are events, not row
writes — see *Persistence*).

### Endpoints

| Endpoint | Body | Purpose |
|---|---|---|
| `POST /ingest/model-inventory` | JSON | Full inventory snapshot (models + chain) |
| `POST /ingest/model-chain` | JSON | Chain links only (if pushed separately) |
| `POST /ingest/data-lineage` | JSON | Pipeline run manifest |
| `POST /ingest/field-lineage` | JSON | Report → section → field registry |
| `POST /ingest/documents` | multipart | Model-doc PDF + metadata → blob store |
| `GET  /ingest/status/{artifact}` | — | Last accepted provenance + validation result |

### Payload schemas (the emitted contracts to freeze)

These mirror what PhysicalRisk emits today, so producers change transport, not
format. Freeze them as versioned schemas in ModelRisk.

**model-inventory** — top-level `metadata`, `models[]`, `model_chain`,
`tiering_matrix`, `audit_trail`:

```jsonc
{
  "metadata": { "framework", "version", "last_updated", "handbook_reference" },
  "models": [ {
     "model_id": "MKM-SI-001", "name", "short_name", "tier", "materiality",
     "status", "version", "owner", "rag_rating", "validation_status",
     "source_module": "src/models/intensity/distribution.py",
     "upstream_models": [...], "downstream_models": [...]      // adjacency
  } ],
  "model_chain": {
     "links": [ { "from": "MKM-BRI-001", "to": "MKM-BRF-001",
                  "data_handoff": "…", "granularity": "Per-property",
                  "fields": [ { "name": "BRIFloodScore", "type": "float" } ] } ]
  },
  "tiering_matrix": { "description", "matrix" }
}
```

**data-lineage** — top-level `runs`, `steps`:

```jsonc
{
  "runs":  { "run-20260714-154822": ["gauges", "properties", "…"] },  // run → ordered steps
  "steps": {
     "gaugehd": {
        "run_id", "timestamp", "user", "hostname",
        "generator": "port.src.gauge.gaugehd", "status": "success",
        "parameters": { "history_years": 1 },
        "inputs":  { "gauge.json": { "hash": "<sha256|null>", "type": "file", "file_count": N } },
        "outputs": { "gaugehd/":   { "hash": "…", "type": "directory", "file_count": N } }
     }
  }
}
```

**field-lineage** — top-level `version`, `reports` → `sections` → `fields`:

```jsonc
{
  "version": "1.0.0", "last_updated": "…",
  "reports": {
     "eod_report": {
        "label": "…", "generator": "…",
        "sections": {
           "executive_summary": {
              "fields": {
                 "eod_date": {
                    "label": "EOD Date",
                    "source_file": "data/output/trading/eod/<date>.json",
                    "source_field": "eod_date",
                    "pipeline_step": "blotter",   // ties to a data-lineage step
                    "cdm_path": null,
                    "computation": "snapshot timestamp"
                 } } } } }
  }
}
```

### Generic validation on ingest

The *generic* half of today's PhysicalRisk validators moves server-side and runs
as ingest-acceptance criteria:

- **Model chain referential integrity** (from `scan_model_chain`): chain links
  resolve to known `model_id`s; `upstream`/`downstream` adjacency is consistent;
  the graph is acyclic.
- **Lineage cross-refs**: every `field.pipeline_step` names a step present in the
  latest data-lineage manifest.

The *domain-specific* checks stay producer-side: `source_module` path existence,
CDM field classification (`src/lineage/field_usage/` RED/AMBER/GREEN tiering).

---

## The `modelrisk-scan` utility library

A small, installable package **owned by ModelRisk**, installed by producers.
Scope is deliberately narrow — stateless scan helpers only, no regulatory state:

- **Generalised manifest engine** — `record_step`, `pre_hash_inputs`,
  `save_manifest`, `repair_manifest`, file/dir hashing — lifted from
  `src/lineage/manifest/_core.py` with the domain topology factored out.
- **Topology is injected**, not built in. Each repo provides its own
  `DEPENDENCY_GRAPH` / `STEP_IO` (PhysicalRisk keeps its
  `src/lineage/manifest/_topology.py`; a Moody's repo supplies its own).
- **A push client** wrapping the REST endpoints above (provenance stamping,
  ret/idempotency, multipart upload).

This is the single source for the generic scanner; there is no second copy to
drift. Field-lineage and model-inventory have little reusable scanner today, so
their "generic version" in ModelRisk is the schema + validation (server-side),
not utility code — the library grows to cover them if/when automated scanners
are built.

---

## Persistence: `.json` → event-sourced DB

ModelRisk is **event-sourced CQRS on Postgres** (psycopg 3, append-only `events`
table with a per-stream tamper-evident hash chain; read models are Postgres
views built by projections). It is **not** an ORM with mutable rows. Migration
implications:

- Importing legacy `.json` means **synthesising events** — a genesis
  `…Imported` event per aggregate that folds into the existing projection — not
  inserting rows.
- The one-off loader is written as a **documented, re-runnable script** under
  `scripts/`; it is audit evidence of the data move. It reads the legacy JSON,
  wraps each record in the ingest envelope (with provenance pointing at the
  legacy file + its checksum), and calls the same ingest path producers use —
  so the import exercises the real contract.
- Validate with row counts, checksums, and field-by-field reconciliation between
  source JSON and destination projection.
- **Canonical source — resolved.** The regulatory JSON appears in two places,
  and the split follows how the app resolves paths:
  - `docs/models/governance_data/` (repo-versioned, `get_governance_data_dir()`)
    is authoritative for the **governance files** — `model_inventory.json`,
    `model_audit_log.json`, `bcbs239_assessment.json`, `raci_matrix.json`,
    `mrc_meetings.json`, `bibliography.json`, `governance_documents.json` — plus
    the `governance_docs/` and `mrc_uploads/` blob dirs. This is the copy the
    live app reads.
  - The SSD `data/` dir (`/Volumes/David SSD/Docs/PhysicalRisk/data`, via the
    `data →` symlink, `get_data_dir()`) is authoritative **only** for
    `data_lineage.json` and `field_lineage_registry.json` (pipeline output).
  - The SSD dir also contains **stale** copies of `model_inventory.json`
    (227 KB vs the canonical 264 KB) and `model_audit_log.json` (397 KB vs
    3.5 MB), sitting beside `*.bak` files. The loader **must ignore** these and
    read governance files from `governance_data/` only.
  The remaining shared files (bcbs239, raci, mrc_meetings, bibliography,
  governance_documents) are byte-identical across both locations, so the choice
  is moot for them — but standardise on `governance_data/` for consistency.

---

## Sequencing

Phases are ordered by dependency. Each is merged, tested, and green before the
next begins.

**Phase 0 — Contract + foundations.**
Freeze the four payload schemas and the ingest envelope. Stand up the ingest
endpoints, provenance storage, generic validation, and event/projection plumbing
in ModelRisk. Scaffold the `modelrisk-scan` package (engine + push client) and
`pip install -e` it into PhysicalRisk. No data moves yet.

**Phase 1 — Inventory UX upgrade.**
Build sort, per-column filters, and the Tier/Overdue/Due-Soon/Assessed stat
tiles on ModelRisk's existing inventory (data already present there). Anchor
tab, immediate visible win. Note the status concepts (Overdue/Due-Soon/On-Track)
already exist as badge logic in `helpers.js` — surface them as tiles/columns/
filters. Stack: plain Jinja + vanilla JS (`fetch` + `innerHTML`), matching both
apps — port the *patterns*, not a framework.

**Phase 2 — Net-new read domains.**
Model Chain, BCBS 239, RACI: schema, projection, and console view for each.
Reconcile their data in via the loader.

**Phase 3 — Lineage.**
Data-lineage and field-lineage sinks + ingestion endpoints and console views.
Point PhysicalRisk's manifest engine (now on `modelrisk-scan`) at
`POST /ingest/data-lineage`. Wire field-lineage/inventory push.

**Phase 4 — Data-move for existing domains.**
Reconcile Documents (+ blobs), Bibliography, Audit Trail (`model_audit_log`),
and MRC data into ModelRisk (ModelRisk MRC is canonical; PhysicalRisk data folds
in as history). Retain original JSON read-only as provenance until sign-off.

**Phase 5 — PhysicalRisk cutover.**
Switch model-doc generation to upload PDFs to ModelRisk. Delete PhysicalRisk's
regulatory blueprints, UI panels, CRUD, and `.json` reads; remove the mount
points in `src/routes/registry.py` and `src/visual/interactivity/manager.py`.
PhysicalRisk now only produces and pushes.

---

## Watch-outs

- **Back-coupling — checked, clean.** PhysicalRisk's governance code has **zero**
  imports into pricing/hedging/sim. The only cross-boundary item is the static
  `lineage.manifest` topology (data, not calls), handled by injecting topology
  into `modelrisk-scan`. No dependency inversion needed.
- **Two MRC implementations.** ModelRisk already has an event-sourced MRC and
  PhysicalRisk has a parallel JSON one. ModelRisk is canonical; the import folds
  PhysicalRisk meetings in as history. Do not overwrite ModelRisk's event stream.
- **Utility drift.** Never *copy* scanner code into both repos. ModelRisk owns
  `modelrisk-scan`; PhysicalRisk installs it. A copied-and-edited scanner
  re-creates the duplication this migration exists to remove.
- **Scope discipline.** Phase 0's contract must be frozen and green before the
  net-new domains build against it.
- **Circular dependency.** ModelRisk must never import PhysicalRisk. Data flows
  up over REST; only `modelrisk-scan` flows down.

---

## Why not a shared library (the earlier plan)

The prior approach — generalise BCBS/RACI/lineage into ModelRisk and have
PhysicalRisk re-import them as a version-pinned wheel — was dropped because:

- The regulatory engine is **stateful and database-backed**. A pinned library
  can't be the single source of truth for data that must live in one DB; a
  *service* can.
- ModelRisk exposes **no importable Python API** and ships flat `src.` / `config.`
  namespaces. The library model forces a full repackage + public-API design
  *before* anything else. The service model needs none of that.
- The library model keeps regulatory UI running *inside* PhysicalRisk. The goal
  is the opposite: strip it out entirely.
- A network contract is the only thing that extends to **other repos** (Moody's)
  producing scans. A Python wheel does not.

The narrow, healthy remainder of the library idea survives as `modelrisk-scan` —
stateless scan utilities only, never the regulatory core.
