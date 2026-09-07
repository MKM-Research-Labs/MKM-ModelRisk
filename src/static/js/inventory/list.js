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
// clicking a Tier / RAG tile toggles the matching filter.

const LIFECYCLE_STAGES = ["Development", "Validation", "Production", "Retired"];
// Not a lifecycle stage but the natural place to ask for one: a hibernated model is
// out of the estate and out of every count, so the only way to see one — to reactivate
// it, say — is to ask. Picking it re-fetches with the retired models included.
const HIBERNATED_FILTER = "Hibernated";

// The list is the same furniture for every register: tiles over filters over a
// sortable table. What differs is the id key, which columns it draws and which
// elements it draws into -- so those are configuration and the rest is written once.
// ``createRecordList`` below makes an instance; ML Applications make a second.
const InventoryList = {
  _cfg: {
    idKey: "model_id", summaryId: "m-summary", listId: "m-list",
    filtersId: "m-filters", tableId: "m-table", p: "mf-", noun: "models",
    // Lead with the functional groups rather than one long list — the whole point of
    // the field. Unset on a register with no groups and it draws exactly as before.
    groupBy: "functional_group",
    spec: (key) => (typeof Inventory !== "undefined" && Inventory.specByKey
      ? Inventory.specByKey(key) : null),
    reload: () => Inventory.loadList(),
  },

  // Whether the list is currently asking for hibernated models. Read by the fetch
  // in inventory.js, because choosing this filter changes what has to be fetched,
  // not just what is shown.
  wantsHibernated() { return this._filters && this._filters.lifecycle === HIBERNATED_FILTER; },

  _models: [],
  _onRow: null,
  _filters: null,
  _sort: null,

  // Column set: key drives sorting; sortVal extracts a comparable value; cell
  // renders the <td> body from a model's data document.
  _columns: [
    { key: "id", label: "ID", sortVal: (m) => m.id.toLowerCase(),
      cell: (m) => '<span class="modelid">' + esc(m.id) + "</span>" },
    { key: "name", label: "Name", sortVal: (m) => (m.d.name || "").toLowerCase(),
      cell: (m) => fieldDisplay(m.d.name) },
    { key: "tier", label: "Criticality", sortVal: (m) => m.d.tier || 99,
      cell: (m) => tierBadge(m.d.tier, m.d.division) },
    // "RAG" named the old fixed Red/Amber/Green scale; a division defines its own ratings
    // now (this estate has added "Stop"), so the column is named for what it holds.
    { key: "rag", label: "Risk Rating", sortVal: (m) => ragOrder(m.d.rag_rating, m.d.division),
      cell: (m) => ragBadge(m.d.rag_rating, m.d.division) },
    { key: "owner", label: "Owner", sortVal: (m) => (m.d.owner || "").toLowerCase(),
      cell: (m) => fieldDisplay(m.d.owner) },
    { key: "next", label: "Next Review", sortVal: (m) => m.d.next_review_date || "9999",
      cell: (m) => fieldDisplay(m.d.next_review_date) },
    // The derived review status (On Track / Overdue) is no longer a column — it
    // only re-stated the Next Review date beside it. The Overdue / Due Soon tiles
    // and the review filter still surface it as a portfolio-health signal.
    { key: "mrc", label: "MRC Status", sortVal: (m) => mrcState(m.d),
      cell: (m) => mrcStatusBadge(m.d) },
    { key: "lifecycle", label: "Lifecycle", sortVal: (m) => m.retired ? "zz" : (m.d.lifecycle_stage || m.d.status || "").toLowerCase(),
      cell: function (m) { return m.retired ? '<span class="pill">retired</span>'
        : optionLabel(InventoryList._cfg.spec("lifecycle_stage"), m.d.lifecycle_stage || m.d.status); } },
  ],

  mount(models, onRow) {
    // ``r`` is the row as the API sent it. The shared shape names only what every
    // register has; a register's own tiles (see ``extraTiles``) read the rest from
    // here rather than this builder growing a field per register.
    this._models = models.map((m) => ({ id: m[this._cfg.idKey], retired: m.retired,
                                        d: m.data || {}, r: m }));
    this._onRow = onRow;
    // Filters survive a re-mount. Choosing "Hibernated" re-fetches, and clearing
    // the filters here would drop the very filter that asked for the reload —
    // the list would come back showing everything, hibernated models included.
    this._filters = this._filters || { q: "", tier: "", rag: "", owner: "", review: "", lifecycle: "" };
    // Default to the soonest next-review first, so the models needing attention
    // are at the top on load; unscheduled ("9999" sort key) fall to the bottom.
    // Any header click still re-sorts and toggles.
    this._sort = { key: "next", dir: 1 };
    document.getElementById(this._cfg.summaryId).innerHTML = this._tiles() +
      policyDraftNotice(this._models.map((m) => m.d.division));
    this._wireTiles();
    document.getElementById(this._cfg.listId).innerHTML =
      '<div id="' + this._cfg.filtersId + '" class="filters"></div>' +
      '<div id="' + this._cfg.tableId + '"></div>';
    this._renderFilters();
    this._renderTable();
  },

  // --- table ---
  _visible() {
    const f = this._filters;
    const q = f.q.trim().toLowerCase();
    let rows = this._models.filter((m) => {
      if (q && (m.id + " " + (m.d.name || "")).toLowerCase().indexOf(q) < 0) return false;
      if (f.tier && String(m.d.tier) !== f.tier) return false;
      if (f.rag && m.d.rag_rating !== f.rag) return false;
      if (f.owner && m.d.owner !== f.owner) return false;
      if (f.review && reviewStatus(m.d.next_review_date) !== f.review) return false;
      if (f.lifecycle === HIBERNATED_FILTER) {
        if (!m.retired) return false;
      } else if (f.lifecycle && (m.d.lifecycle_stage || m.d.status) !== f.lifecycle) return false;
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
    const count = document.getElementById(this._cfg.p + "count");
    if (count) count.textContent = rows.length + " of " + this._models.length;
    const box = document.getElementById(this._cfg.tableId);
    if (!rows.length) {
      box.innerHTML = '<div class="empty">No ' + this._cfg.noun + ' match these filters.</div>';
      return;
    }
    const arrow = (k) => this._sort.key === k ? (this._sort.dir > 0 ? " ▲" : " ▼") : "";
    const head = this._columns.map((c) =>
      '<th class="sortable" data-sort="' + c.key + '">' + c.label + arrow(c.key) + "</th>").join("");
    // A register that carries functional groups leads with them (list_groups.js); one
    // that does not, or a reader who is filtering for something specific, gets the flat
    // table exactly as before.
    if (this._grouped && this._grouped()) {
      this._openGroups = this._openGroups || {};
      this._renderGrouped(rows, head);
      return;
    }
    box.innerHTML = this._tableMarkup(rows, head);
    this._wireTable();
  },

  // The flat table. Its own method because the grouped view falls back to it whenever
  // there is nothing to group by, and two copies of a table builder is how the two come
  // to draw a record differently.
  _tableMarkup(rows, head) {
    const body = rows.map((m) =>
      '<tr class="clickable" data-id="' + esc(m.id) + '">' +
      this._columns.map((c) => "<td>" + c.cell(m) + "</td>").join("") + "</tr>").join("");
    return "<table><thead><tr>" + head + "</tr></thead><tbody>" + body + "</tbody></table>";
  },

  _wireTable() {
    const self = this;
    document.querySelectorAll("#" + this._cfg.tableId + " th.sortable").forEach(function (th) {
      th.onclick = function () {
        const key = th.getAttribute("data-sort");
        if (self._sort.key === key) self._sort.dir = -self._sort.dir;
        else self._sort = { key: key, dir: 1 };
        self._renderTable();
      };
    });
    document.querySelectorAll("#" + this._cfg.tableId + " tr.clickable").forEach(function (tr) {
      tr.onclick = function () { self._onRow(tr.getAttribute("data-id")); };
    });
  },
};

// A second register's list: same furniture, its own columns, ids and id key.
function createRecordList(cfg, columns) {
  const list = Object.create(InventoryList);
  list._cfg = Object.assign({}, InventoryList._cfg, cfg);
  if (columns) list._columns = columns;
  list._models = [];
  list._onRow = null;
  list._filters = null;
  list._sort = null;
  list._openGroups = null;
  return list;
}
