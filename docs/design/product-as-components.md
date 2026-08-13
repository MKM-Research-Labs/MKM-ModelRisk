# Design decision: a Product is typed components + a calculating agent

**Status:** Implemented — accepted 2026-07-29; one clean-up outstanding (see below)
**Area:** Products / Model chain

## Decision

A Product is defined as an **open list of component models, each carrying a model
type, plus a single Calculating Agent** — "a combination of several models, like a
candy store." It is *not* a fixed Analytics-model + Market-Data-model + Agent
triple.

How the component models **connect** to each other is not a Product concept: it is
already captured by **model dependencies** (each model's upstream/downstream) and
the **Model Chain**. A Product references a set of models; the existing dependency
graph explains how those models feed each other.

## Why

The original Product model bound exactly three components and used
`model_type.binding_role` (`Analytics` / `Market Data` / `Neither`) as the gate
deciding which of the two fixed *model* slots a given model was eligible for. Once a
Product is an open list of components, there is no fixed slot to gate, so
`binding_role` has no consumer — it becomes dead weight.

## Current state (already partly here)

- `PRODUCT_BINDINGS == ('calculating_agent',)` — the fixed model slots are already
  gone; only the agent is a singular binding.
- Products already have a `components` collection: `component_type` (→ `model_type`
  reference), `model_id` (→ `model_inventory` reference), `role` (free text).
- The Product overview already *displays* components read-only.

So the data model is already the candy-store shape. What was missing is the UI to
**define** components, and the removal of the now-vestigial `binding_role`.

## Consequences / follow-ups

1. **Done.** The **Components** tab to the Product detail so components
   can be added/edited (generic collection editor; `component_type` and `model_id`
   render as dropdowns from their reference lists). This is the first increment.
2. **Still outstanding (2026-08-11).** Remove `binding_role` from the `model_type` reference (field + admin column +
   `_component_set`/registration references) when Product functionality is reviewed.
   Left in place for now so nothing breaks mid-review.
3. The model **type name** (Statistical, Curve, Fitter, …) is what a component
   carries; that vocabulary is admin-managed under Admin → Model Type.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
