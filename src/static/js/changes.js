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

// The change register, as it appears on a record's detail screen.
//
// One renderer for all three record types, on the same reasoning as ModelDocs: the
// register is identical everywhere and only the subject differs. What a tier COSTS
// differs by workflow, and that difference is resolved on the server and served
// through /api/changes/vocabulary -- no tier name, depth or wording is written here.
const Changes = {
  _subjectType: null, _subjectId: null, _host: null, _retired: false,
  _rows: [], _vocab: null, _refresh: null,

  // The vocabulary is fetched once per page. It is configuration, not record data:
  // an institution that renames a tier renames it in one place and every screen
  // follows, which is the point of serving it rather than compiling it in here.
  async _vocabulary() {
    if (!this._vocab) this._vocab = await App.get("/api/changes/vocabulary");
    return this._vocab;
  },

  async render(subjectType, subjectId, host, retired, refresh) {
    this._subjectType = subjectType;
    this._subjectId = subjectId;
    this._host = host;
    this._retired = !!retired;
    this._refresh = refresh || null;
    const box = document.getElementById(host);
    if (!box) return;
    box.innerHTML = '<div class="empty">Loading&hellip;</div>';
    try {
      await this._vocabulary();
      this._rows = await App.get(
        "/api/changes?subject_type=" + encodeURIComponent(subjectType) +
        "&subject_id=" + encodeURIComponent(subjectId));
    } catch (e) {
      box.innerHTML = '<div class="empty">' + esc(e.message) + "</div>";
      return;
    }
    box.innerHTML = this._html();
    this._bind();
  },

  _workflow() {
    return (this._vocab.subject_workflows || {})[this._subjectType] || "";
  },

  // What this record's workflow does about a tier. Read from the served matrix, so an
  // AI System says "re-baseline" where an ML Application says "refresh the validation
  // pack" without either word appearing in this file.
  _depthNote(changeClass, depth) {
    const depths = this._vocab.revalidation_depths || {};
    const resolved = depth ||
      ((this._vocab.depth_matrix || {})[changeClass] || {})[this._workflow()];
    return depths[resolved] || resolved || "";
  },

  // The same badge a tier or a meeting status is drawn as, coloured from the theme --
  // never a literal here (R10). An unclassified proposal is a muted word rather than a
  // badge: a badge asserts a classification, and nobody has made one yet.
  _tierPill(changeClass) {
    if (!changeClass) return '<span class="muted">unclassified</span>';
    const colour = Theme.colour("change_class", changeClass);
    if (!colour) return '<span class="muted">' + esc(changeClass) + "</span>";
    return '<span class="badge" style="background:' + colour + '">' +
      esc(changeClass) + "</span>";
  },

  // Governance fields hold prose — a model's methodology runs to a paragraph — and the
  // movement is read as "what moved", not as the text itself. The full value stays
  // reachable on hover rather than being dropped.
  _short(value) {
    const text = String(value == null ? "—" : value);
    if (text.length <= 90) return esc(text);
    return '<span title="' + esc(text) + '">' + esc(text.slice(0, 90)) +
      "&hellip;</span>";
  },

  _movement(data) {
    const after = data.after || {};
    const before = data.before || {};
    const self = this;
    const parts = Object.keys(after).sort().map(function (key) {
      return '<div><code>' + esc(key) + "</code> " + self._short(before[key]) +
        " &rarr; " + self._short(after[key]) + "</div>";
    });
    (data.affected_artifacts || []).forEach(function (name) {
      parts.push("<div><em>artifact</em> <code>" + esc(name) + "</code></div>");
    });
    return parts.join("") || '<div class="muted">—</div>';
  },

  _row(row) {
    const d = row.data || {};
    const actions = [];
    if (!this._retired && !d.superseded && !d.change_class) {
      actions.push('<button class="btn small" data-classify="' + esc(row.change_id) +
                   '">Classify</button>');
    }
    if (!this._retired && !d.superseded) {
      actions.push('<button class="btn small ghost" data-supersede="' +
                   esc(row.change_id) + '">Supersede</button>');
    }
    return "<tr" + (d.superseded ? ' class="muted"' : "") + "><td><code>" +
      esc(row.change_id) + "</code></td><td>" + this._tierPill(d.change_class) +
      (d.superseded ? ' <span class="pill">superseded</span>' : "") + "</td><td>" +
      this._movement(d) + "</td><td>" + esc(d.rationale || "") + "</td><td>" +
      esc(d.change_class ? this._depthNote(d.change_class, d.revalidation_depth) : "") +
      "</td><td>" + actions.join(" ") + "</td></tr>";
  },

  _proposeForm() {
    if (this._retired) return "";
    return '<div class="section-header" style="margin-top:var(--space-8)">' +
      "Propose a change</div>" +
      '<p class="muted" style="font-size:var(--size-sm);margin:0 0 var(--space-4)">' +
      "Name the field and the value you want it to take. What it holds today is read " +
      "from the record, so the tier is derived from the real movement rather than " +
      "from how the proposal describes it.</p>" +
      '<div class="row" style="gap:var(--space-4);flex-wrap:wrap">' +
      '<input id="chg-field" placeholder="field, e.g. foundation_model" />' +
      '<input id="chg-value" placeholder="proposed value" />' +
      '<input id="chg-artifacts" placeholder="artifacts (comma separated, optional)" />' +
      '<input id="chg-rationale" placeholder="why" style="flex:1;min-width:16rem" />' +
      '<button class="btn" id="chg-propose">Propose</button></div>';
  },

  _html() {
    const rows = this._rows.map((r) => this._row(r)).join("");
    const table = rows
      ? '<table class="table"><thead><tr><th>Change</th><th>Tier</th>' +
        "<th>Movement</th><th>Why</th><th>What it calls for</th><th></th></tr></thead>" +
        "<tbody>" + rows + "</tbody></table>"
      : '<div class="empty">No changes proposed against this record.</div>';
    return '<div class="section-header">Proposed changes</div>' +
      '<p class="muted" style="font-size:var(--size-sm);margin:0 0 var(--space-4)">' +
      "Every proposed change is classified into one of four tiers, and the tier sets " +
      "how much revalidation it calls for. The classification is recorded once, as a " +
      "decision taken on a date &mdash; it is not recomputed each time this is " +
      "opened.</p>" + table + this._proposeForm();
  },

  _reload() {
    if (this._refresh) this._refresh();
    this.render(this._subjectType, this._subjectId, this._host, this._retired,
                this._refresh);
  },

  _bind() {
    const self = this;
    document.querySelectorAll("[data-classify]").forEach(function (btn) {
      btn.onclick = function () {
        const id = btn.getAttribute("data-classify");
        App.amend("Classify change " + id + ".", "POST",
                  "/api/changes/" + id + "/classify", {}, () => self._reload());
      };
    });
    document.querySelectorAll("[data-supersede]").forEach(function (btn) {
      btn.onclick = function () {
        const id = btn.getAttribute("data-supersede");
        App.amend("Supersede change " + id + ".", "POST",
                  "/api/changes/" + id + "/supersede", {}, () => self._reload());
      };
    });
    const propose = document.getElementById("chg-propose");
    if (propose) propose.onclick = function () { self._propose(); };
  },

  _propose() {
    const field = val("chg-field");
    const value = val("chg-value");
    const artifacts = val("chg-artifacts").split(",")
      .map((s) => s.trim()).filter(Boolean);
    const rationale = val("chg-rationale");
    if (!field && !artifacts.length) {
      App.toast("Name a field or an artifact.", "error"); return;
    }
    if (!rationale) { App.toast("A change needs a reason.", "error"); return; }
    const after = {};
    if (field) after[field] = value;
    const self = this;
    App.amend("Propose a change to " + this._subjectId + ".", "POST", "/api/changes", {
      subject_type: this._subjectType, subject_id: this._subjectId,
      rationale: rationale, after: after, affected_artifacts: artifacts,
    }, () => self._reload());
  },
};
