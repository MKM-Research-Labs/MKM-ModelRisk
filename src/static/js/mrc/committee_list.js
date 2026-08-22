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

// The MRC committees list on the Admin > MRC tab (the Committees package). This
// core module owns the list itself: the clickable table, the add form and its
// level-driven scope picker. The committee detail (membership, quorum, ToR)
// augments Committees from committee_detail.js, loaded after.
const Committees = {
  _spec: null,
  _items: [],
  _ref: {},             // reference data (divisions/lines of business) for scope pickers
  _openId: null,        // survives a re-render so the open detail re-opens

  _visible() {
    return this._spec.fields.filter((f) => !f.hidden);
  },

  // Committees are archived, never deleted; ``archived`` is stored as the string
  // "true" via the standard update endpoint.
  _isArchived(item) { return item.archived === "true"; },

  // The Division/Line of Business scope depends on the committee's level: a
  // Company-level MRC has no scope; a Division-level one picks a Division; a
  // Line of Business-level one picks a Line of Business.
  _scopeOptions(level) {
    if (level === "Division") return (this._ref.division || []).map((d) => d.value);
    if (level === "Line of Business") return (this._ref.line_of_business || []).map((d) => d.value);
    return null;  // Company-level, or no level chosen yet
  },

  _scopeControl(id, level, current) {
    const opts = this._scopeOptions(level);
    if (opts === null) {
      const hint = level === "Company" ? "n/a for a Company-level MRC" : "choose a Level first";
      return '<input id="' + id + '" disabled placeholder="' + hint + '">';
    }
    const choices = ['<option value=""></option>'].concat(opts.map((o) =>
      "<option" + (o === current ? " selected" : "") + ">" + esc(o) + "</option>")).join("");
    return '<select id="' + id + '">' + choices + "</select>";
  },

  _addControl(f) {
    if (f.key === "scope_value") {
      return '<span id="cadd-scope-wrap">' + this._scopeControl("cadd-scope_value", "", "") + "</span>";
    }
    return inputControl("cadd-" + f.key, f);
  },

  render(container, spec, items, refData) {
    this._spec = spec;
    this._items = items;
    this._ref = refData || {};
    const cols = this._visible();
    const head = cols.map((f) => "<th>" + esc(f.label) + "</th>").join("");
    const body = items.length
      ? items.map((it) =>
          '<tr class="clickable' + (this._isArchived(it) ? " muted" : "") + '" data-cid="' + esc(it.item_id) + '">' +
          cols.map((f, i) => "<td>" + fieldDisplay(it[f.key]) +
            (i === 0 && this._isArchived(it) ? ' <span class="badge" style="background:var(--muted)">Archived</span>' : "") +
            "</td>").join("") + "</tr>").join("")
      : '<tr><td colspan="' + cols.length + '" class="empty">No committees yet.</td></tr>';
    const addInputs = cols.map((f) =>
      '<div class="field"><label>' + esc(f.label) + (f.required ? " *" : "") + "</label>" +
      this._addControl(f) + "</div>").join("");
    container.innerHTML =
      '<div class="section-header">MRC committees</div>' +
      '<p class="muted">Each committee is anchored to an org tier and carries its chair, cadence ' +
      "and Terms of Reference. Click a row to open its detail.</p>" +
      "<table><thead><tr>" + head + "</tr></thead><tbody>" + body + "</tbody></table>" +
      '<div class="row" style="margin-top:var(--space-4)">' + addInputs +
      '<button class="btn small" id="cadd">Add committee&hellip;</button></div>' +
      '<div id="committee-detail"></div>';
    container.querySelectorAll("tr.clickable").forEach((tr) => {
      tr.onclick = () => this._showDetail(tr.getAttribute("data-cid"));
    });
    // The scope picker follows the chosen Level.
    const levelSel = document.getElementById("cadd-level");
    if (levelSel) {
      levelSel.onchange = () => {
        document.getElementById("cadd-scope-wrap").innerHTML =
          this._scopeControl("cadd-scope_value", levelSel.value, "");
      };
    }
    document.getElementById("cadd").onclick = () => this._add();
    if (this._openId && items.some((i) => i.item_id === this._openId)) {
      this._showDetail(this._openId);
    } else {
      this._openId = null;
    }
  },

  _add() {
    const fields = {};
    this._visible().forEach((f) => {
      const v = val("cadd-" + f.key);
      if (v !== "") fields[f.key] = v;
    });
    App.amend("Add an MRC committee.", "POST", "/api/reference/collections/mrc",
      { fields: fields }, () => Reference.render());
  },
};
