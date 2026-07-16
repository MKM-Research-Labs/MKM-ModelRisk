# ModelRisk ingest contract

The JSON Schemas under `ingest/v1/` are the **contract** every producer codes to.
ModelRisk is the collector/system-of-record; producers (PhysicalRisk today, other
repos later — e.g. a Moody's repo running Claude over its own code) generate
artifacts and POST them to `/api/ingest/*`. These schemas are the frozen,
language-agnostic definition of what a valid payload looks like, so a producer in
any stack can conform.

## Layout

```
ingest/v1/
  envelope.schema.json          common wrapper (provenance + payload)
  model_inventory.schema.json   inventory + "string of pearls" model chain
  data_lineage.schema.json      pipeline run manifest
  field_lineage.schema.json     report -> section -> field registry
  document.schema.json          model-doc PDF upload metadata (multipart)
  examples/                     one validated example per schema (sliced from real data)
```

## The envelope

Every request is an **envelope**: a `provenance` block plus the artifact
`payload`. Provenance is stamped onto every stored event and is the BCBS 239
audit trail — a reproducible link from a governed artifact back to the exact scan
that produced it.

```jsonc
{
  "schema_version": "v1",              // optional; absent means v1
  "artifact": "data-lineage",          // optional; the endpoint path is authoritative
  "provenance": {
    "source_repo": "PhysicalRisk",
    "commit": "d097faea…",
    "producer": "modelrisk-scan/data-lineage",
    "producer_version": "0.1.0",
    "generated_at": "2026-07-15T15:48:22Z"
  },
  "payload": { /* validated against the matching artifact schema */ }
}
```

The envelope is **strict** (`additionalProperties: false`) — unknown top-level
keys are rejected to catch producer mistakes. Artifact **payloads** are
**permissive** (`additionalProperties: true`) — only structural and identifying
keys are required, so producer-added descriptive fields never break ingestion.

## What the schemas do *not* enforce

Cross-reference integrity is validated **server-side** at ingest time, not by
these schemas, because it spans records (or spans artifacts):

- model chain: links resolve to known `model_id`s; up/downstream adjacency is
  consistent; the graph is acyclic;
- field lineage: every field's `pipeline_step` resolves to a known step in the
  latest data-lineage manifest;
- data lineage: every step named in `runs` exists in `steps`.

## Versioning

`v1` is stable. Changes within `v1` are **additive only** (new optional fields).
A breaking change (removing/renaming a required field, tightening a type) means a
new `v2/` directory and a new endpoint version — never an in-place edit that
could silently invalidate an existing producer. The `examples/` are validated
against their schemas by `tests/ingest/test_contracts_v1.py`, which fails if a
schema and its example drift apart.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
