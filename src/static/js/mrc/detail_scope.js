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

// MeetingDetail — the scope picker: choosing which models / products a meeting
// takes. Split from the analysis review it sits above because the two jobs pull
// in opposite directions: picking wants to be compact and searchable, reviewing
// wants room. The picker is collapsed by default and disappears once the agenda
// is locked, so a live meeting shows only the work.
Object.assign(MeetingDetail, {
  // Rows visible before the list scrolls. Deep enough to browse, shallow enough
  // that the picker never pushes the review work off the page.
  _SCOPE_ROWS: 8,

  _scopeOpen(kind) { return this["_scopeOpen_" + kind] === true; },

  // The picker, behind a disclosure. Once the agenda is locked for distribution
  // the scope is settled, so it is not offered at all.
  _scopeTable(cfg) {
    if (this._agendaLocked()) {
      return '<div class="muted" style="font-size:var(--size-sm);margin-bottom:var(--space-4)">Agenda ' +
        "locked for distribution — scope is settled. " + cfg.inScope.length + " " +
        (cfg.inScope.length === 1 ? cfg.label : cfg.plural) + " in scope.</div>";
    }
    const open = this._scopeOpen(cfg.kind);
    const toggle = '<button class="btn small" data-scope-toggle="' + cfg.kind + '">' +
      (open ? "&minus; Hide" : "+ Add") + " " + cfg.plural +
      " to scope</button> " +
      '<span class="muted" style="font-size:var(--size-sm)">' + cfg.inScope.length + " in scope.</span>";
    if (!open) return '<div style="margin-bottom:var(--space-5)">' + toggle + "</div>";
    return '<div style="margin-bottom:var(--space-5)">' + toggle + "</div>" + this._scopePanel(cfg);
  },

  _scopePanel(cfg) {
    const inScope = new Set(cfg.inScope.map((m) => m[cfg.idKey]));
    const filter = this._scopeFilter();
    const candidates = this._candidates(cfg);
    const mrc = (this._meeting.data || {}).mrc;
    const mrcNote = mrc ? " for MRC <b>" + esc(mrc) + "</b>" : "";
    // Singular and plural both come from the served scope table. They used to be
    // built by lowercasing the label and adding an "s", which reads correctly for
    // models and products and gives "ai systems" for an AI System.
    const many = cfg.plural, one = cfg.label;
    const banner = filter
      ? '<div class="muted" style="margin-bottom:var(--space-3)">Showing ' + many + " the MRC oversees" +
        mrcNote + " — " + esc(filter.key) + " <b>" + esc(filter.value) + "</b>. " +
        '<label style="margin-left:var(--space-4)"><input type="checkbox" data-show-all="' + cfg.kind + '"' +
        (this[cfg.showAllKey] ? " checked" : "") + "> Show all</label></div>"
      : '<div class="muted" style="margin-bottom:var(--space-3)">Company-wide MRC' + mrcNote +
        " — every " + one + " is a candidate.</div>";
    const docBy = {}, presBy = {};
    cfg.inScope.forEach((r) => {
      if (r.analysis_item_id) docBy[r[cfg.idKey]] = r.analysis_item_id;
      if (r.presenter) presBy[r[cfg.idKey]] = r.presenter;
    });
    const rows = candidates.length ? candidates.map((m) => {
      const d = m.data || {};
      const id = m[cfg.idKey];
      const inS = inScope.has(id);
      return '<tr><td><input type="checkbox" data-scope="' + esc(id) + '"' + (inS ? " checked" : "") +
        '></td><td class="modelid">' + esc(id) + "</td><td>" + fieldDisplay(d[cfg.nameKey]) +
        "</td><td>" + tierBadge(d.tier, d.division) + "</td><td>" + ragBadge(d.rag_rating, d.division) +
        "</td><td>" + this._presenterCell(id, inS, presBy) +
        "</td><td>" + this._analysisCell(cfg, id, inS, docBy) + "</td></tr>";
    }).join("") : '<tr><td colspan="7" class="empty">No ' + many + " match this scope.</td></tr>";
    // Search + a capped scroll box: with a few hundred models on the inventory a
    // flat list is unusable, and typing beats scanning rows by eye.
    const rowPx = 34, headPx = 38;
    return banner +
      '<input id="scope-search-' + cfg.kind + '" placeholder="Search ' + esc(many) +
      ' by id or name&hellip;" style="width:100%;margin-bottom:var(--space-3)">' +
      '<div class="scope-scroll" style="max-height:' + (this._SCOPE_ROWS * rowPx + headPx) +
      'px;overflow:auto;border:1px solid var(--line);border-radius:var(--radius-md)">' +
      "<table><thead><tr><th></th><th>" + cfg.label + " ID</th><th>Name</th><th>Tier</th><th>RAG</th>" +
      "<th>Presenter</th><th>Analysis</th></tr></thead><tbody>" + rows + "</tbody></table></div>" +
      '<div class="row" style="margin-top:var(--space-5)">' +
      '<button class="btn small primary" data-save-scope="' + cfg.kind + '">Save selection&hellip;</button>' +
      '<span class="muted" style="margin-left:var(--space-4)">' + inScope.size + " in scope.</span></div>";
  },

  // Presenter per in-scope item: a dropdown of people from the register.
  _presenterCell(id, inScope, byId) {
    if (!inScope) return '<span class="muted">—</span>';
    const cur = byId[id] || "";
    const opts = ['<option value=""></option>'].concat((this._people || []).map((p) =>
      "<option" + (p.name === cur ? " selected" : "") + ">" + esc(p.name) + "</option>")).join("");
    return '<select data-presenter="' + esc(id) + '">' + opts + "</select>";
  },

  // The paper tabled against an in-scope item. The MRC references a document the
  // model already holds rather than taking its own copy: a committee should be
  // reviewing what the model actually has on file, and two copies drift apart.
  // Uploading a new one is done on the model's Docs tab, where it belongs.
  _analysisCell(cfg, id, inScope, byId) {
    if (!inScope) return '<span class="muted" style="font-size:var(--size-xs)">add to scope first</span>';
    const docs = (this._reviewableDocs || {})[id];
    if (docs === undefined) return '<span class="muted" style="font-size:var(--size-xs)">&hellip;</span>';
    if (!docs.length) {
      return '<span class="muted" style="font-size:var(--size-xs)">no analysis on the ' +
        esc(cfg.label) + "</span>";
    }
    const chosen = byId[id] || "";
    const opts = ['<option value="">&mdash; none tabled &mdash;</option>'].concat(
      docs.map((d) => '<option value="' + esc(d.item_id) + '"' +
        (d.item_id === chosen ? " selected" : "") + ">" + esc(d.category) + ": " +
        esc(d.original_name) + "</option>")).join("");
    const link = chosen
      ? ' <a href="/api/models/' + esc(id) + "/documents/" + esc(chosen) +
        '/download?inline=1" target="_blank" rel="noopener">view</a>'
      : "";
    return '<select data-analysis-ref="' + esc(id) + '">' + opts + "</select>" + link;
  },
});
