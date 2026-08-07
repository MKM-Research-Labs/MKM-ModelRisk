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

const InventoryList = {
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
    { key: "model_id", label: "ID", sortVal: (m) => m.model_id.toLowerCase(),
      cell: (m) => '<span class="modelid">' + esc(m.model_id) + "</span>" },
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
      cell: (m) => m.retired ? '<span class="pill">retired</span>' : fieldDisplay(m.d.lifecycle_stage || m.d.status) },
  ],

  mount(models, onRow) {
    this._models = models.map((m) => ({ model_id: m.model_id, retired: m.retired, d: m.data || {} }));
    this._onRow = onRow;
    // Filters survive a re-mount. Choosing "Hibernated" re-fetches, and clearing
    // the filters here would drop the very filter that asked for the reload —
    // the list would come back showing everything, hibernated models included.
    this._filters = this._filters || { q: "", tier: "", rag: "", owner: "", review: "", lifecycle: "" };
    // Default to the soonest next-review first, so the models needing attention
    // are at the top on load; unscheduled ("9999" sort key) fall to the bottom.
    // Any header click still re-sorts and toggles.
    this._sort = { key: "next", dir: 1 };
    document.getElementById("m-summary").innerHTML = this._tiles() +
      policyDraftNotice(this._models.map((m) => m.d.division));
    this._wireTiles();
    document.getElementById("m-list").innerHTML =
      '<div id="m-filters" class="filters"></div><div id="m-table"></div>';
    this._renderFilters();
    this._renderTable();
  },

  // The Mission-Criticality bands the tiles and the filter speak in, so the list uses the
  // same vocabulary as the Risk tab and the Criticality column instead of a fixed
  // Tier 1/2/3. Scoped to a division, that division's bands; under "All", the union across
  // the divisions on the list (keyed by score — the value a model actually stores), because
  // one division's policy cannot describe another's models. Each division's own ordering is
  // kept: the admin sets it deliberately with the move up/down controls.
  _mcBands() {
    const scoped = (typeof MrcNav !== "undefined" && MrcNav.state) ? MrcNav.state.div : null;
    const seed = () => Policy.dimensionBands("mission_criticality", null) ||
      [1, 2, 3].map((t) => ({ name: "Tier " + t, score: t, colour: TIER_COLORS[t] }));
    if (scoped) return Policy.dimensionBands("mission_criticality", scoped) || seed();
    const byScore = new Map();
    [...new Set(this._models.map((m) => m.d.division).filter(Boolean))].forEach((division) =>
      (Policy.dimensionBands("mission_criticality", division) || []).forEach((b) => {
        if (!byScore.has(b.score)) byScore.set(b.score, b);
      }));
    return byScore.size ? [...byScore.values()] : seed();
  },

  // The risk ratings the tiles and the filter offer, resolved exactly like the bands above:
  // the scoped division's, or the union across the divisions on the list under "All".
  _ratings() {
    const scoped = (typeof MrcNav !== "undefined" && MrcNav.state) ? MrcNav.state.div : null;
    const of = (division) => Policy.ratings(division) || [];
    if (scoped) return of(scoped).length ? of(scoped) : of(null);
    const byName = new Map();
    [...new Set(this._models.map((m) => m.d.division).filter(Boolean))].forEach((division) =>
      of(division).forEach((r) => { if (!byName.has(r.name)) byName.set(r.name, r); }));
    return byName.size ? [...byName.values()] : of(null);
  },

  // --- tiles ---
  // Counted over the live estate only. A hibernated model is out of the estate, so
  // it is out of every figure — including while the Hibernated filter is showing
  // it, when it is on screen precisely because it is *not* part of the picture.
  _live() { return this._models.filter((m) => !m.retired); },

  _tiles() {
    const live = this._live();
    const byTier = (t) => live.filter((m) => m.d.tier === t).length;
    const byRag = (r) => live.filter((m) => m.d.rag_rating === r).length;
    // The ratings tile counted a fixed Red / Amber / Green, so a division that has added a
    // rating (this estate's "Stop") had models it simply did not show. It lists whatever
    // the policy defines, in policy order, each count in its own colour.
    const ratings = this._ratings();
    // Approved = models whose CURRENT MRC state is an approval, the same rule the status
    // column and the Risk tab use: a model awaiting a decision, or approved under a
    // categorisation the division has since replaced, is not covered by a sign-off. Counting
    // the last historical outcome instead read 25/25 while the column beside it said Pending.
    const approved = live.filter((m) => mrcState(m.d) === "Approved").length;
    const ragCount = (r) => '<span style="color:' + (r.colour || RAG_COLORS[r.name] ||
      "#9e9e9e") + '">' + byRag(r.name) + "</span>";
    const ragVal = ratings.map(ragCount).join(" / ");
    const ragLabel = ratings.map((r) => r.name.charAt(0)).join(" / ");
    const tile = (lbl, val, color, filter) =>
      '<div class="scard" style="border-left-color:' + color + '"' +
      (filter ? ' data-tile="' + filter + '"' : "") + '><div class="lbl">' + lbl +
      '</div><div class="val">' + val + "</div></div>";
    return '<div class="summary">' +
      tile("Total Models", live.length, "#1976d2", "") +
      this._mcBands().map((b) => tile(esc(b.name), byTier(b.score),
        b.colour || TIER_COLORS[b.score] || "#9e9e9e", "tier=" + b.score)).join("") +
      tile(esc(ragLabel), ragVal, "#388e3c", "") +
      tile("Approved", approved + " / " + live.length, "#388e3c", "") +
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
    // The criticality filter offers band NAMES but still filters on the stored score, so
    // the option's value and its label differ — hence its own builder.
    const mcLabel = Policy.dimensionLabel("mission_criticality",
      (typeof MrcNav !== "undefined" && MrcNav.state) ? MrcNav.state.div : null);
    const tierSel = '<select id="mf-tier"><option value="">All ' +
      esc(mcLabel || "tiers") + "</option>" +
      this._mcBands().map((b) => '<option value="' + esc(b.score) + '"' +
        (String(b.score) === String(f.tier) ? " selected" : "") + ">" + esc(b.name) +
        "</option>").join("") + "</select>";
    document.getElementById("m-filters").innerHTML =
      '<input id="mf-q" placeholder="Search id or name…" value="' + esc(f.q) + '">' +
      tierSel +
      // Policy order, so a division's own ratings (and only those) are offered.
      sel("mf-rag", f.rag, ["All ratings", ...this._ratings().map((r) => r.name)]) +
      sel("mf-owner", f.owner, ["All owners", ...owners]) +
      sel("mf-review", f.review, ["All reviews", "Overdue", "Due Soon", "On Track", "Not Scheduled"]) +
      sel("mf-lifecycle", f.lifecycle, ["All lifecycle", ...LIFECYCLE_STAGES, HIBERNATED_FILTER]) +
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
    document.getElementById("mf-lifecycle").onchange = function () {
      const el = document.getElementById("mf-lifecycle");
      const was = self._filters.lifecycle === HIBERNATED_FILTER;
      self._filters.lifecycle = el.value;
      // Hibernated models are not in the list this page was drawn from, so
      // switching into (or out of) that filter has to go back for the data.
      if (was !== (el.value === HIBERNATED_FILTER)) { Inventory.loadList(); return; }
      self._renderTable();
    };
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
