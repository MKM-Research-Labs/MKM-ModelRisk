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

  // --- context: the shape of the estate, and which way it is moving -------
  _estate(d) {
    const e = d.estate || {};
    const o = d.operational || {};
    const kinds = Object.keys(e.by_kind || {}).map((k) =>
      this._line(k, e.by_kind[k])).join("");
    const tiers = Object.keys(e.by_tier || {}).map((t) =>
      this._line(t === "untiered" ? "Untiered" : "Tier " + t, e.by_tier[t])).join("");
    return '<div class="card"><h3>The estate</h3>' + kinds + tiers +
      this._line("Operational failures, " + (o.window_days || 0) + " days",
                 o.failures_in_window, o.failures_in_window ? this._colour("act") : null) +
      "</div>";
  },

  _direction(d) {
    const dir = d.direction || {};
    const share = dir.share_meeting_standard == null
      ? "—" : Math.round(dir.share_meeting_standard * 100) + "%";
    const trend = this._trend(dir.trend);
    return '<div class="card"><h3>Meeting the standard</h3>' +
      '<div style="font-size:var(--size-xl);font-weight:700">' + esc(share) + "</div>" +
      this._line("Records audited", dir.records_audited) +
      this._line("Meeting the standard", dir.records_meeting_standard,
                 this._colour("clear")) +
      this._line("Below the standard", dir.records_below_standard,
                 dir.records_below_standard ? this._colour("act") : null) +
      trend + "</div>";
  },

  // The one chart on the page. "Is this getting better?" is the second question
  // every executive asks, and a figure for today cannot answer it. Drawn from the
  // observed series only — with no history it says so, because a flat line and an
  // empty history look identical and only one of them is true.
  _trend(series) {
    if (series == null || !series.length) {
      return '<div class="muted" style="margin-top:var(--space-4)">No history yet — ' +
        "the observation runs daily, and the trend appears once it has looked more " +
        "than once.</div>";
    }
    const points = series
      .map((row) => (row.share_meeting_standard == null ? null : row.share_meeting_standard))
      .filter((v) => v !== null);
    if (points.length < 2) {
      return '<div class="muted" style="margin-top:var(--space-4)">Observed once so ' +
        "far — a trend needs a second look.</div>";
    }
    const colour = this._colour("clear");
    const W = 240, H = 44;
    // Scale to the observed range, never to 0–100: a governed estate lives in the
    // top few percent, and a full-height axis would draw every real movement flat.
    const lo = Math.min.apply(null, points), hi = Math.max.apply(null, points);
    const span = (hi - lo) || 1;
    const x = (i) => (i * W) / (points.length - 1);
    const y = (v) => H - ((v - lo) / span) * (H - 8) - 4;
    const path = points.map((v, i) => (i ? "L" : "M") + x(i).toFixed(1) + "," + y(v).toFixed(1)).join(" ");
    const first = Math.round(points[0] * 100), last = Math.round(points[points.length - 1] * 100);
    const delta = last - first;
    // preserveAspectRatio="none" so the chart fills the panel's width instead of
    // being scaled to its height and centred; the strokes are marked non-scaling so
    // stretching the box does not stretch the line with it.
    return '<svg viewBox="0 0 ' + W + " " + H + '" width="100%" height="44" ' +
      'preserveAspectRatio="none" ' +
      'style="display:block;margin:var(--space-5) 0" role="img" aria-label="' +
      esc("Records meeting the standard, " + first + " to " + last + " per cent over " +
          points.length + " observations") + '">' +
      '<path d="' + path + " L" + W + "," + H + " L0," + H + ' Z" fill="' + colour +
      '" opacity="0.12"></path>' +
      '<path d="' + path + '" fill="none" stroke="' + colour +
      '" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke"></path>' +
      '<path d="M' + W + "," + y(points[points.length - 1]).toFixed(1) + " L" + W +
      "," + y(points[points.length - 1]).toFixed(1) + '" stroke="' + colour +
      '" stroke-width="7" stroke-linecap="round" vector-effect="non-scaling-stroke">' +
      "</path></svg>" +
      '<div class="muted" style="font-size:var(--size-xs)">' +
      esc(first + "% → " + last + "% over " + points.length + " observations") +
      (delta === 0 ? "" : esc(" · " + (delta > 0 ? "+" : "") + delta + " points")) +
      "</div>";
  },

  _line(label, value, colour) {
    return '<div class="inforow"><span class="k">' + esc(label) + "</span>" +
      '<span class="v"' + (colour ? ' style="color:' + colour + '"' : "") + ">" +
      esc(value == null ? "—" : value) + "</span></div>";
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
