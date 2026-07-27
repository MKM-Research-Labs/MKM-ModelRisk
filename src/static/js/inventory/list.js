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

// Inventory list view: summary stat tiles, per-column filters, and a sortable
// table. Given the full in-scope model set it renders everything client-side;
// filtering and sorting never re-fetch. The tiles summarise the whole set;
// clicking a Tier / Overdue / Due Soon tile toggles the matching filter.

const LIFECYCLE_STAGES = ["Development", "Validation", "Production", "Retired"];
// A model counts as "assessed" once the MRC validation has reached a decision.
const ASSESSED_STATUSES = ["Validated", "Conditionally Approved", "Rejected"];

const InventoryList = {
  _models: [],
  _onRow: null,
  _filters: null,
  _sort: null,

  // Column set: key drives sorting; sortVal extracts a comparable value; cell
  // renders the <td> body from a model's data document.
  _columns: [
    { key: "model_id", label: "ID", sortVal: (m) => m.model_id.toLowerCase(),
      cell: (m) => '<span class="modelid">' + esc(m.model_id) + "</span>" },
    { key: "name", label: "Name", sortVal: (m) => (m.d.name || "").toLowerCase(),
      cell: (m) => fieldDisplay(m.d.name) },
    { key: "tier", label: "Tier", sortVal: (m) => m.d.tier || 99,
      cell: (m) => tierBadge(m.d.tier) },
    { key: "rag", label: "RAG", sortVal: (m) => RAG_ORDER[m.d.rag_rating] ?? 9,
      cell: (m) => ragBadge(m.d.rag_rating) },
    { key: "owner", label: "Owner", sortVal: (m) => (m.d.owner || "").toLowerCase(),
      cell: (m) => fieldDisplay(m.d.owner) },
    { key: "next", label: "Next Review", sortVal: (m) => m.d.next_review_date || "9999",
      cell: (m) => fieldDisplay(m.d.next_review_date) },
    // The derived review status (On Track / Overdue) is no longer a column — it
    // only re-stated the Next Review date beside it. The Overdue / Due Soon tiles
    // and the review filter still surface it as a portfolio-health signal.
    { key: "mrc", label: "MRC Status", sortVal: (m) => mrcOutcome(m.d),
      cell: (m) => mrcStatusBadge(m.d) },
    { key: "lifecycle", label: "Lifecycle", sortVal: (m) => m.retired ? "zz" : (m.d.lifecycle_stage || m.d.status || "").toLowerCase(),
      cell: (m) => m.retired ? '<span class="pill">retired</span>' : fieldDisplay(m.d.lifecycle_stage || m.d.status) },
  ],

  mount(models, onRow) {
    this._models = models.map((m) => ({ model_id: m.model_id, retired: m.retired, d: m.data || {} }));
    this._onRow = onRow;
    this._filters = { q: "", tier: "", rag: "", owner: "", review: "", lifecycle: "" };
    // Default to the soonest next-review first, so the models needing attention
    // are at the top on load; unscheduled ("9999" sort key) fall to the bottom.
    // Any header click still re-sorts and toggles.
    this._sort = { key: "next", dir: 1 };
    document.getElementById("m-summary").innerHTML = this._tiles();
    this._wireTiles();
    document.getElementById("m-list").innerHTML =
      '<div id="m-filters" class="filters"></div><div id="m-table"></div>';
    this._renderFilters();
    this._renderTable();
  },

  // --- tiles ---
  _tiles() {
    const byTier = (t) => this._models.filter((m) => m.d.tier === t).length;
    const byReview = (s) => this._models.filter((m) => reviewStatus(m.d.next_review_date) === s).length;
    const assessed = this._models.filter((m) => ASSESSED_STATUSES.indexOf(m.d.validation_status) >= 0).length;
    const tile = (lbl, val, color, filter) =>
      '<div class="scard" style="border-left-color:' + color + '"' +
      (filter ? ' data-tile="' + filter + '"' : "") + '><div class="lbl">' + lbl +
      '</div><div class="val">' + val + "</div></div>";
    return '<div class="summary">' +
      tile("Total Models", this._models.length, "#1976d2", "") +
      tile("Tier 1", byTier(1), "#d32f2f", "tier=1") +
      tile("Tier 2", byTier(2), "#f57c00", "tier=2") +
      tile("Tier 3", byTier(3), "#1976d2", "tier=3") +
      tile("Overdue", byReview("Overdue"), "#d32f2f", "review=Overdue") +
      tile("Due Soon", byReview("Due Soon"), "#f57c00", "review=Due Soon") +
      tile("Assessed", assessed + " / " + this._models.length, "#388e3c", "") +
      "</div>";
  },

  _wireTiles() {
    const self = this;
    document.querySelectorAll("#m-summary [data-tile]").forEach(function (el) {
      el.classList.add("clickable-tile");
      el.onclick = function () {
        const [key, val] = el.getAttribute("data-tile").split("=");
        self._filters[key] = self._filters[key] === val ? "" : val;
        self._renderFilters();
        self._renderTable();
      };
    });
  },

  // --- filters ---
  _renderFilters() {
    const owners = [...new Set(this._models.map((m) => m.d.owner).filter(Boolean))].sort();
    const f = this._filters;
    const sel = (id, cur, opts) =>
      '<select id="' + id + '"><option value="">' + opts[0] + "</option>" +
      opts.slice(1).map((o) => '<option' + (o === cur ? " selected" : "") + ">" + esc(o) + "</option>").join("") +
      "</select>";
    document.getElementById("m-filters").innerHTML =
      '<input id="mf-q" placeholder="Search id or name…" value="' + esc(f.q) + '">' +
      sel("mf-tier", f.tier, ["All tiers", "1", "2", "3"]) +
      sel("mf-rag", f.rag, ["All RAG", "Green", "Amber", "Red"]) +
      sel("mf-owner", f.owner, ["All owners", ...owners]) +
      sel("mf-review", f.review, ["All reviews", "Overdue", "Due Soon", "On Track", "Not Scheduled"]) +
      sel("mf-lifecycle", f.lifecycle, ["All lifecycle", ...LIFECYCLE_STAGES]) +
      '<button class="btn small" id="mf-clear">Clear</button>' +
      '<span class="fcount" id="mf-count"></span>';
    this._wireFilters();
  },

  _wireFilters() {
    const self = this;
    const bind = (id, key, ev) => {
      const el = document.getElementById(id);
      el[ev] = function () { self._filters[key] = el.value; self._renderTable(); };
    };
    bind("mf-q", "q", "oninput");
    bind("mf-tier", "tier", "onchange");
    bind("mf-rag", "rag", "onchange");
    bind("mf-owner", "owner", "onchange");
    bind("mf-review", "review", "onchange");
    bind("mf-lifecycle", "lifecycle", "onchange");
    document.getElementById("mf-clear").onclick = function () {
      self._filters = { q: "", tier: "", rag: "", owner: "", review: "", lifecycle: "" };
      self._renderFilters();
      self._renderTable();
    };
  },

  // --- table ---
  _visible() {
    const f = this._filters;
    const q = f.q.trim().toLowerCase();
    let rows = this._models.filter((m) => {
      if (q && (m.model_id + " " + (m.d.name || "")).toLowerCase().indexOf(q) < 0) return false;
      if (f.tier && String(m.d.tier) !== f.tier) return false;
      if (f.rag && m.d.rag_rating !== f.rag) return false;
      if (f.owner && m.d.owner !== f.owner) return false;
      if (f.review && reviewStatus(m.d.next_review_date) !== f.review) return false;
      if (f.lifecycle && (m.d.lifecycle_stage || m.d.status) !== f.lifecycle) return false;
      return true;
    });
    const col = this._columns.find((c) => c.key === this._sort.key);
    const dir = this._sort.dir;
    rows.sort((a, b) => {
      const va = col.sortVal(a), vb = col.sortVal(b);
      return va < vb ? -dir : va > vb ? dir : 0;
    });
    return rows;
  },

  _renderTable() {
    const rows = this._visible();
    const count = document.getElementById("mf-count");
    if (count) count.textContent = rows.length + " of " + this._models.length;
    const box = document.getElementById("m-table");
    if (!rows.length) {
      box.innerHTML = '<div class="empty">No models match these filters.</div>';
      return;
    }
    const arrow = (k) => this._sort.key === k ? (this._sort.dir > 0 ? " ▲" : " ▼") : "";
    const head = this._columns.map((c) =>
      '<th class="sortable" data-sort="' + c.key + '">' + c.label + arrow(c.key) + "</th>").join("");
    const body = rows.map((m) =>
      '<tr class="clickable" data-id="' + esc(m.model_id) + '">' +
      this._columns.map((c) => "<td>" + c.cell(m) + "</td>").join("") + "</tr>").join("");
    box.innerHTML = "<table><thead><tr>" + head + "</tr></thead><tbody>" + body + "</tbody></table>";
    this._wireTable();
  },

  _wireTable() {
    const self = this;
    document.querySelectorAll("#m-table th.sortable").forEach(function (th) {
      th.onclick = function () {
        const key = th.getAttribute("data-sort");
        if (self._sort.key === key) self._sort.dir = -self._sort.dir;
        else self._sort = { key: key, dir: 1 };
        self._renderTable();
      };
    });
    document.querySelectorAll("#m-table tr.clickable").forEach(function (tr) {
      tr.onclick = function () { self._onRow(tr.getAttribute("data-id")); };
    });
  },
};
