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
// The inventory list's tiles and filters -- how the register is narrowed.
//
// The summary tiles across the top and the filter row beneath them are one subject:
// each tile is a filter that has already been counted, and clicking one applies it.
// Keeping them together is what stops the count and the filter drifting apart, which
// is the bug this arrangement prevents -- a tile reading 17 that filters to 15.
//
// Assigns onto Inventory; loads after list.js.

Object.assign(InventoryList, {

  // The Mission-Criticality bands the tiles and the filter speak in, so the list uses the
  // same vocabulary as the Risk tab and the Criticality column instead of a fixed
  // Tier 1/2/3. Scoped to a division, that division's bands; under "All", the union across
  // the divisions on the list (keyed by score — the value a model actually stores), because
  // one division's policy cannot describe another's models. Each division's own ordering is
  // kept: the admin sets it deliberately with the move up/down controls.
  _mcBands() {
    const scoped = (typeof MrcNav !== "undefined" && MrcNav.state) ? MrcNav.state.div : null;
    const seed = () => Policy.dimensionBands("mission_criticality", null) ||
      [1, 2, 3].map((t) => ({ name: "Tier " + t, score: t,
                              colour: Theme.hex("mission_criticality", t) }));
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
    const ragCount = (r) => '<span style="color:' + (r.colour ||
      Theme.hex("rag", r.name) || Theme.value("grey")) + '">' + byRag(r.name) + "</span>";
    const ragVal = ratings.map(ragCount).join(" / ");
    const ragLabel = ratings.map((r) => r.name.charAt(0)).join(" / ");
    const tile = (lbl, val, color, filter) =>
      '<div class="scard" style="border-left-color:' + color + '"' +
      (filter ? ' data-tile="' + filter + '"' : "") + '><div class="lbl">' + lbl +
      '</div><div class="val">' + val + "</div></div>";
    return '<div class="summary">' +
      tile("Total " + this._cfg.noun, live.length, Theme.value("accent"), "") +
      this._mcBands().map((b) => tile(esc(b.name), byTier(b.score),
        b.colour || Theme.hex("mission_criticality", b.score) || Theme.value("grey"),
        "tier=" + b.score)).join("") +
      tile(esc(ragLabel), ragVal, Theme.value("green"), "") +
      tile("Approved", approved + " / " + live.length, Theme.value("green"), "") +
      // A register may declare tiles of its own: the ML Apps list adds the estate's
      // mandatory-item gap, which means nothing on a model. Declared by the caller
      // rather than branched on here, so this builder never learns which register it
      // is drawing.
      (this._cfg.extraTiles ? this._cfg.extraTiles(live, tile).join("") : "") +
      "</div>";
  },

  _wireTiles() {
    const self = this;
    document.querySelectorAll("#" + this._cfg.summaryId + " [data-tile]").forEach(function (el) {
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
  // The stages the estate actually uses, from the division's vocabulary, falling
  // back to the shipped words before it has been seeded.
  _lifecycleValues() {
    const spec = this._cfg.spec("lifecycle_stage");
    return (spec && spec.options && spec.options.length) ? spec.options : LIFECYCLE_STAGES;
  },

  // What each stage is shown as, where the institution has renamed one.
  _lifecycleLabels() {
    const spec = this._cfg.spec("lifecycle_stage");
    return (spec && spec.option_labels) || {};
  },

  _renderFilters() {
    const owners = [...new Set(this._models.map((m) => m.d.owner).filter(Boolean))].sort();
    const f = this._filters;
    // ``shown`` maps a stored value to what it is displayed as, for the filters
    // whose vocabulary the institution has renamed. Without it the lifecycle filter
    // would offer the word on record rather than the word on every other screen.
    const sel = (id, cur, opts, shown) =>
      '<select id="' + id + '"><option value="">' + opts[0] + "</option>" +
      opts.slice(1).map((o) => '<option value="' + esc(o) + '"' + (o === cur ? " selected" : "") +
        ">" + esc((shown && shown[o]) || o) + "</option>").join("") +
      "</select>";
    // The criticality filter offers band NAMES but still filters on the stored score, so
    // the option's value and its label differ — hence its own builder.
    const mcLabel = Policy.dimensionLabel("mission_criticality",
      (typeof MrcNav !== "undefined" && MrcNav.state) ? MrcNav.state.div : null);
    const tierSel = '<select id="' + this._cfg.p + 'tier"><option value="">All ' +
      esc(mcLabel || "tiers") + "</option>" +
      this._mcBands().map((b) => '<option value="' + esc(b.score) + '"' +
        (String(b.score) === String(f.tier) ? " selected" : "") + ">" + esc(b.name) +
        "</option>").join("") + "</select>";
    document.getElementById(this._cfg.filtersId).innerHTML =
      '<input id="' + this._cfg.p + 'q" placeholder="Search id or name…" value="' + esc(f.q) + '">' +
      tierSel +
      // Policy order, so a division's own ratings (and only those) are offered.
      sel(this._cfg.p + "rag", f.rag, ["All ratings", ...this._ratings().map((r) => r.name)]) +
      sel(this._cfg.p + "owner", f.owner, ["All owners", ...owners]) +
      sel(this._cfg.p + "review", f.review, ["All reviews", "Overdue", "Due Soon", "On Track", "Not Scheduled"]) +
      sel(this._cfg.p + "lifecycle", f.lifecycle, ["All lifecycle", ...this._lifecycleValues(), HIBERNATED_FILTER],
          this._lifecycleLabels()) +
      '<button class="btn small" id="' + this._cfg.p + 'clear">Clear</button>' +
      '<span class="fcount" id="' + this._cfg.p + 'count"></span>';
    this._wireFilters();
  },

  _wireFilters() {
    const self = this;
    const bind = (id, key, ev) => {
      const el = document.getElementById(id);
      el[ev] = function () { self._filters[key] = el.value; self._renderTable(); };
    };
    bind(this._cfg.p + "q", "q", "oninput");
    bind(this._cfg.p + "tier", "tier", "onchange");
    bind(this._cfg.p + "rag", "rag", "onchange");
    bind(this._cfg.p + "owner", "owner", "onchange");
    bind(this._cfg.p + "review", "review", "onchange");
    // ``self``, not ``this``: inside the handler ``this`` is the <select>, which has
    // no _cfg — so reading the id off it threw, and the Lifecycle filter did nothing
    // at all on any of the three screens. It surfaced when hibernated records became
    // reachable-by-filter only: this is the sole route back to one.
    document.getElementById(this._cfg.p + "lifecycle").onchange = function () {
      const el = document.getElementById(self._cfg.p + "lifecycle");
      const was = self._filters.lifecycle === HIBERNATED_FILTER;
      self._filters.lifecycle = el.value;
      // Hibernated models are not in the list this page was drawn from, so
      // switching into (or out of) that filter has to go back for the data.
      if (was !== (el.value === HIBERNATED_FILTER)) { self._cfg.reload(); return; }
      self._renderTable();
    };
    document.getElementById(this._cfg.p + "clear").onclick = function () {
      self._filters = { q: "", tier: "", rag: "", owner: "", review: "", lifecycle: "" };
      self._renderFilters();
      self._renderTable();
    };
  },
});
