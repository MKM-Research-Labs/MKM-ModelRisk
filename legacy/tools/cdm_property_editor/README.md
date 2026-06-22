# CDM Property Editor (side tool)

A standalone, schema-driven browser for the residential property CDM. It shows
a **menu of all properties** and a set of **tabs — one per top-level CDM
section** (`PropertyHeader`, `ProtectionMeasures`, `EnergyPerformance`,
`HistoryAndIncidents`, `TransactionHistory`). Each tab's fields are generated
straight from `port.cdm.asset.residential.schema.PROPERTY_SCHEMA`, so labels,
widget types and menu options always match the canonical CDM.

It follows the **Model Governance / regulatory workflow** UI as a template:
left-hand property list, a right-hand **review icon** on each row, and a
centered detail **modal** (gradient header card + section tabs + schema-driven
field grids), light-themed to match (`#1976d2` blue, pill badges).

This is deliberately isolated from the production scene:

- It reads/writes **only** a sandbox copy at `data/property_sandbox.json`.
- On first run the sandbox is seeded from the existing simulated thames
  portfolio `data/input/thames/property.json` (falls back to the golden
  fixture `tests/port/cdm/golden/property.json` if the data SSD is unmounted).
- The real `data/` tree and the test fixture are never modified. To re-seed
  (e.g. after switching catchment), delete `data/property_sandbox.json`.

## Run

```bash
source .venv/bin/activate
python tools/cdm_property_editor/app.py
# open http://127.0.0.1:5057
```

## Status

Done: read-only review — left list + per-row review icon + governance-style
detail modal with the 5 CDM section tabs, schema-driven from `PROPERTY_SCHEMA`.
Seeded from the simulated thames portfolio (100 properties).

Next (planned): **update** field values, **add** a property, **remove** a
property — all writing back to the sandbox file only. Follow the governance
edit pattern: small inline Edit buttons in the field grid → a field-type-aware
modal (text / date / `<select>` from `options`) → `PUT/POST/DELETE` endpoints.
The renderer already exposes each field's `type`/`options`, so editing is just
swapping the displayed value for the matching input widget.
