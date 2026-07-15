# modelrisk-scan

Producer-side client for feeding a **ModelRisk** collector. Install it into any
repo that produces governance scans — PhysicalRisk today, a Moody's repo running
Claude over its own code tomorrow — and push artifacts over the ingest contract.

Deliberately **dependency-free** (standard library only), so it never drags a
dependency tree into a producer repo.

## Install (development)

```
pip install -e packages/modelrisk-scan       # from the ModelRisk repo
```

## Use

```python
from modelrisk_scan import IngestClient, build_provenance

client = IngestClient("https://modelrisk.internal", token=INGEST_TOKEN)

prov = build_provenance(
    source_repo="PhysicalRisk",
    producer="modelrisk-scan/data-lineage",
    producer_version="0.1.0",
)  # commit defaults to the repo's current git HEAD

result = client.push("data-lineage", manifest, prov)
print("stored" if result.created else "unchanged")
print(result.receipt)   # the collector's ingest receipt
```

`push` returns an `IngestResult` (`created=True` on HTTP 201 stored, `False` on
200 idempotent) or raises `IngestError` on any non-2xx response. The transport is
injectable (`IngestClient(..., transport=...)`) for testing without a live server.

## Scope

Phase 0 ships the **push client** and **provenance** builder. The generalised
data-lineage manifest *engine* (lifted and de-domained from PhysicalRisk's
`src/lineage/manifest`) lands in **Phase 3**, when PhysicalRisk actually adopts
this library in place of its local copy.
