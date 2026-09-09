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

// The landing tab: does any of this need a response?
//
// Everything it draws comes from /api/dashboard in one read, including the words.
// No state name, card heading or instruction is written here — they live in
// config/governance/_attention.py so an adopter renames them like every other
// vocabulary, and the colours resolve through Theme from config/theme.py (rule R10).
//
// The page never writes. There is no acknowledge and no dismiss: an executive
// clearing an item from a screen would be an ungoverned decision with no minute
// against it. Every row instead opens the record or the meeting where the response
// is recorded and can be challenged.

// Where a row goes when it is opened, by the kind of thing it is about. A kind with
// no entry simply renders without a link rather than opening the wrong screen.
const DASH_OPEN = {
  "Model": { tab: "inventory", show: (id) => Detail.show(id) },
  "Product": { tab: "product", show: (id) => ProductDetail.show(id) },
  "ML Application": { tab: "mlapps", show: (id) => MLAppDetail.show(id) },
  "Committee action": { tab: "mrc", show: (id, parent) => MeetingDetail.show(parent || id) },
  "Division": { tab: "reference", show: () => {} },
};

const Dashboard = {
  _data: null,
  _expanded: {},          // which collapsed rows the reader has opened

  async render() {
    this._data = await App.get("/api/dashboard");
    this._draw();
  },

  _state(name) {
    return (this._data.states || []).find((s) => s.state === name) || {};
  },

  // The colour a state is drawn in, via the theme. Never a literal.
  _colour(name) {
    return Theme.colour("attention", name) || "var(--muted)";
  },

  _draw() {
    const d = this._data;
    document.getElementById("tab-dashboard").innerHTML =
      this._verdict(d) + this._cards(d) + this._queue(d) +
      '<div class="grid2">' + this._estate(d) + this._direction(d) + "</div>";
    this._wire();
  },

  // --- the verdict: one sentence, never a score ---------------------------
  _verdict(d) {
    const v = d.verdict || {};
    const colour = this._colour(v.state);
    return '<div class="dash-verdict" style="border-color:' + colour + '">' +
      '<span class="dash-dot" style="background:' + colour + '"></span>' +
      '<div class="dash-said"><div class="dash-headline">' +
      esc(v.response_required ? "Yes — " + v.headline : v.headline) +
      '</div><div class="dash-detail">' + esc(v.detail || "") + "</div></div>" +
      '<div class="dash-asof">as at ' + esc(d.as_of || "") + "</div></div>";
  },

  // --- one card per state, in the order the payload presents them ---------
  _cards(d) {
    const counts = (d.verdict || {}).counts || {};
    return '<div class="summary dash-cards">' + (d.states || []).map((s) =>
      '<div class="scard dash-card" style="border-left-color:' + this._colour(s.state) + '">' +
      '<div class="lbl">' + esc(s.card) + "</div>" +
      '<div class="val" style="color:' + this._colour(s.state) + '">' +
      esc(counts[s.state] == null ? "—" : counts[s.state]) + "</div>" +
      '<div class="dash-card-note">' + esc(s.response) + "</div></div>").join("") +
      "</div>";
  },

  // --- the queue: only what needs a response ------------------------------
  _queue(d) {
    const needs = (d.states || []).filter((s) => s.needs_response)
      .map((s) => s.state);
    const rows = ((d.queue || {}).rows || [])
      .filter((r) => needs.indexOf(r.state) >= 0);
    if (!rows.length) {
      return '<div class="card"><h3>What needs your response</h3>' +
        '<div class="empty">Nothing. Every open item is with a named owner and ' +
        "inside its date.</div></div>";
    }
    const q = (d.queue || {});
    const note = q.truncated
      ? '<div class="muted" style="margin-top:var(--space-4)">Showing ' +
        esc(q.returned) + " of " + esc(q.total_rows) + " rows.</div>"
      : "";
    return '<div class="card"><h3>What needs your response</h3>' +
      '<table class="dash-q"><thead><tr><th>Record</th><th>What is owed</th>' +
      "<th>Owner</th><th>Due</th><th>Over</th><th></th></tr></thead><tbody>" +
      rows.map((r) => this._row(r, d)).join("") + "</tbody></table>" + note + "</div>";
  },

  _row(r, d) {
    const colour = this._colour(r.state);
    const grouped = r.grouped;
    const entity = r.entity || {};
    // A collapsed row names what it spans; an ordinary row names the record.
    const meta = grouped
      ? "across " + esc(r.records) + (r.records === 1 ? " record" : " records")
      : [entity.kind, entity.tier ? "Tier " + entity.tier : "", entity.rating]
          .filter(Boolean).map(esc).join(" · ");
    const name = grouped ? "" : (entity.id || entity.name || "");
    const open = grouped
      ? '<span class="edit-btn" data-dash-expand="' + esc(r.id) + '">' +
        (this._expanded[r.id] ? "Hide" : "List") + "</span>"
      : (DASH_OPEN[entity.kind]
          ? '<span class="edit-btn" data-dash-open="' + esc(r.id) + '">Open</span>' : "");
    let html = "<tr><td>" +
      (name ? "<b>" + esc(name) + "</b><br>" : "") +
      '<span class="muted">' + meta + "</span></td>" +
      '<td><span class="badge" style="background:' + colour + '">' +
      esc(this._state(r.state).label) + "</span><br>" + esc(r.reason_label) +
      (r.detail && !grouped ? '<br><span class="muted">' + esc(r.detail) + "</span>" : "") +
      "</td><td>" + esc(r.owner || "—") + "</td>" +
      "<td>" + esc(r.due || "—") + "</td>" +
      '<td style="color:' + (r.days_over > 0 ? colour : "inherit") + '">' +
      (r.days_over > 0 ? esc(r.days_over) + " d" : "—") + "</td>" +
      "<td>" + open + "</td></tr>";
    if (grouped && this._expanded[r.id]) html += this._members(r, d);
    return html;
  },

  // A collapsed row opened: its records, worst first, each openable. The count is
  // what the executive needs; the list is what the owner of the problem needs.
  _members(r, d) {
    const byId = {};
    (d.items || []).forEach((i) => { byId[i.id] = i; });
    return (r.members || []).map((id) => byId[id]).filter(Boolean)
      .map((i) => {
        const e = i.entity || {};
        return '<tr class="dash-member"><td></td><td colspan="4">' +
          "<b>" + esc(e.id || "") + "</b> " +
          '<span class="muted">' + esc(e.name || "") +
          (e.tier ? " · Tier " + esc(e.tier) : "") + "</span>" +
          (i.action ? '<br><span class="muted">' + esc(i.action) + "</span>" : "") +
          "</td><td>" + (DASH_OPEN[e.kind]
            ? '<span class="edit-btn" data-dash-open="' + esc(i.id) + '">Open</span>' : "") +
          "</td></tr>";
      }).join("");
  },

  // --- wiring -------------------------------------------------------------
  _wire() {
    const self = this;
    const byId = {};
    (this._data.items || []).forEach((i) => { byId[i.id] = i; });
    ((this._data.queue || {}).rows || []).forEach((r) => { byId[r.id] = r; });
    document.querySelectorAll("[data-dash-expand]").forEach(function (el) {
      const id = el.getAttribute("data-dash-expand");
      el.onclick = function () {
        self._expanded[id] = !self._expanded[id];
        self._draw();
      };
    });
    document.querySelectorAll("[data-dash-open]").forEach(function (el) {
      const item = byId[el.getAttribute("data-dash-open")];
      if (!item) return;
      el.onclick = function () { self._open(item.entity || {}); };
    });
  },

  // Open the record, or the meeting, where the response is actually recorded.
  async _open(entity) {
    const to = DASH_OPEN[entity.kind];
    if (!to) return;
    await showTab(to.tab);
    to.show(entity.id, entity.parent_id);
  },
};
