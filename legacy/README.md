# `legacy/` — generic starting point

This folder is a **clean, model-agnostic starting point** for MKM-ModelRisk. It
holds **no PhysicalRisk-specific code or data** — the governance workflow will be
built fresh against the design in
[`../docs/mkm_modelrisk_extraction_plan.md`](../docs/mkm_modelrisk_extraction_plan.md),
then promoted into `src/` over time.

## Contents

| Path | Purpose |
|------|---------|
| `example/model_inventory.example.json` | A single **generic placeholder** model-inventory record (`EXAMPLE-001`). Demonstrates the inventory schema with neutral content. Replace with real, client-owned models. |

## Principle

Nothing engagement-specific (flood / PRS / wind / fire / seismic / any
PhysicalRisk model, pipeline, or seed data) belongs here. The platform is
generic: it governs *whatever* models a client owns. Reference implementations
from PhysicalRisk are consulted in that repo, not copied in.
