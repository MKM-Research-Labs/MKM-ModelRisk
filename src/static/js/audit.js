// Copyright (c) 2022-2026 MKM Research Labs.
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

// snake_case / list-key → Title Case for display ("due_date" → "Due Date").
function auditHumanize(key) {
  if (!key) return "";
  return String(key).replace(/_/g, " ").replace(/\b\w/g, (m) => m.toUpperCase());
}

// Render a before/after value; empty / null shows a muted em-dash.
function auditValue(v) {
  if (v === null || v === undefined || v === "") return "<span class='muted'>—</span>";
  return esc(String(v));
}

const Audit = {
  _ref: {},                       // reference data (mrc / division / department)
  _committees: [],
  _events: [],
  _modelMap: {},                  // model_id   -> model data (for MRC scoping)
  _productMap: {},                // product_id -> product data

  // The division/department of the entity an event touched, for MRC scoping.
  // Model and Product events map to their record; every other event (MRC
  // meetings, reference, settings) is unscoped and appears only under "All".
  _scopeData(e) {
    if (e.aggregate_type === "ModelInventoryEntry") return this._modelMap[e.aggregate_id] || {};
    if (e.aggregate_type === "Product") return this._productMap[e.aggregate_id] || {};
    return {};
  },

  // Which record a change touched: the reference/collection item where known,
  // otherwise the raw aggregate (for events that aren't collection changes).
  _record(e) {
    if (e.target) {
      return esc(auditHumanize(e.target.collection)) +
        (e.target.item_id ? " <span class='pill'>" + esc(e.target.item_id) + "</span>" : "");
    }
    return esc(e.aggregate_type) + " <span class='pill'>" + esc(e.aggregate_id) + "</span>";
  },

  // One line per changed field, so Field / Old / New stay aligned within a row.
  _cells(e) {
    if (e.changes && e.changes.length) {
      return {
        field: e.changes.map((c) => esc(auditHumanize(c.field))).join("<br>"),
        old: e.changes.map((c) => auditValue(c.from)).join("<br>"),
        neu: e.changes.map((c) => auditValue(c.to)).join("<br>"),
      };
    }
    // Non-collection events (model registered, meeting held, sign-off, …): no
    // field-level diff — surface the event name instead.
    return { field: "<span class='muted'>" + esc(e.event_type) + "</span>", old: "—", neu: "—" };
  },

  async render() {
    const [nav, models, products, events] = await Promise.all([
      MrcNav.load(), App.get("/api/models"),
      App.get("/api/products"), App.get("/api/audit"),
    ]);
    this._ref = nav.ref;
    this._committees = nav.committees;
    this._events = events;
    this._modelMap = {};
    models.forEach((m) => { this._modelMap[m.model_id] = m.data || {}; });
    this._productMap = {};
    products.forEach((p) => { this._productMap[p.product_id] = p.data || {}; });
    this._draw();
  },

  // Render the log filtered to the shared MRC region; re-drawn (no re-fetch) as
  // the region selection changes.
  _draw() {
    const el = document.getElementById("tab-audit");
    MrcNav.normalize(this._committees, this._ref);
    const self = this;
    const events = this._events
      // Drop the SR 26-2 validation questions seeded automatically at
      // registration — the user made no change, so they'd be misleading noise
      // here. They remain in the immutable event log; this only hides them
      // from the audit view.
      .filter((e) => e.reason !== "Seed SR 26-2 validation questions")
      .filter((e) => MrcNav.inScope(this._committees, this._ref, self._scopeData(e)));
    let rows = "";
    events.forEach(function (e) {
      const when = e.recorded_at.replace("T", " ").slice(0, 19);
      const c = self._cells(e);
      rows +=
        "<tr><td>" + esc(e.global_seq) + "</td><td>" + esc(when) + "</td>" +
        "<td>" + esc(e.actor) + "</td>" +
        "<td>" + self._record(e) + "</td>" +
        "<td>" + c.field + "</td>" +
        "<td>" + c.old + "</td>" +
        "<td>" + c.neu + "</td>" +
        "<td>" + esc(e.reason || "—") + "</td></tr>";
    });
    const body = events.length
      ? "<table><thead><tr><th>#</th><th>When (UTC)</th><th>Who</th><th>Record</th>" +
        "<th>Field</th><th>Old</th><th>New</th><th>Reason</th></tr></thead><tbody>" +
        rows + "</tbody></table>"
      : '<div class="empty">' + (MrcNav.state.div
        ? "No model or product events for this MRC scope."
        : "No events yet. Every change you make appears here, in order, immutably.") + "</div>";
    el.innerHTML =
      '<div class="card"><h3>Audit trail — the immutable event log</h3>' +
      '<p class="muted">Every recorded change, newest first. This is the source of truth; ' +
      "the inventory and meeting views above are projections of it.</p>" + body + "</div>";
  },
};
