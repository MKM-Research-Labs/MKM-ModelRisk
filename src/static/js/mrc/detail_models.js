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

// MeetingDetail — the Signoff tab: Approvals (risk-rating sign-offs) plus an
// Analysis section with Models and Products sub-tabs. The scope table + per-item
// analysis review are written once and driven by a per-kind config, so models
// and products behave identically.
Object.assign(MeetingDetail, {
  // Org-scope filter shared by both kinds: the most specific level set on the
  // meeting (derived from its bound MRC) — line of business > division > all.
  _scopeFilter() {
    const md = this._meeting.data || {};
    if (md.line_of_business) return { key: "line_of_business", value: md.line_of_business };
    if (md.division) return { key: "division", value: md.division };
    return null;
  },

  // Everything that differs between a model scope pane and a product one.
  _scopeCfg(kind) {
    if (kind === "product") {
      return { kind: "product", idKey: "product_id", collection: "products_in_scope",
        inventory: this._products || [], inScope: this._meetingProducts || [],
        base: "products", label: "Product", nameKey: "product", showAllKey: "_showAllProducts",
        setKey: "product_ids" };
    }
    return { kind: "model", idKey: "model_id", collection: "models_in_scope",
      inventory: this._inventory || [], inScope: this._models || [],
      base: "models", label: "Model", nameKey: "name", showAllKey: "_showAll",
      setKey: "model_ids" };
  },

  _candidates(cfg) {
    const filter = this._scopeFilter();
    const inv = cfg.inventory.slice();
    if (this[cfg.showAllKey] || !filter) return inv;
    return inv.filter((m) => (m.data || {})[filter.key] === filter.value);
  },

  _modelsTab() {
    const cfg = this._scopeCfg(this._analysisKind === "product" ? "product" : "model");
    return this._approvalsSection() +
      '<div class="section-header" style="margin-top:18px">Analysis</div>' +
      this._analysisSubtabs(cfg.kind) +
      '<p class="muted" style="font-size:12px">Choose the ' + cfg.label.toLowerCase() +
      "s in scope, then record the confirmation to proceed and any follow-on actions.</p>" +
      this._scopeTable(cfg) + this._analysisReview(cfg);
  },

  _analysisSubtabs(kind) {
    const btn = (k, label) => '<button class="dtab' + (k === kind ? " active" : "") +
      '" data-atab="' + k + '">' + label + "</button>";
    return '<div class="dtabs" style="margin-bottom:8px">' +
      btn("model", "Models") + btn("product", "Products") + "</div>";
  },

  // One review block per in-scope item: the MRC's confirmation to proceed with a
  // note, plus follow-on remediation (owned by the model/product).
  _analysisReview(cfg) {
    const inScope = cfg.inScope;
    if (!inScope.length) {
      return '<div class="muted" style="font-size:12px;margin-top:8px">Add ' + cfg.label.toLowerCase() +
        "s to scope above to record their analysis outcome and remediation.</div>";
    }
    const byId = {};
    cfg.inventory.forEach((m) => { byId[m[cfg.idKey]] = (m.data || {}).remediation_steps || []; });
    const opts = (cur) => ["Pending", "Reviewed — agreed to proceed"].map((s) =>
      "<option" + (s === (cur || "Pending") ? " selected" : "") + ">" + esc(s) + "</option>").join("");
    return inScope.map((m) => {
      const id = m[cfg.idKey];
      const steps = byId[id] || [];
      const stepList = steps.length
        ? steps.map((a) => '<div class="prow"><div style="font-size:12px">' + esc(a.description) +
            ' <span class="muted" style="font-size:10px">' +
            (a.due_date ? "due " + esc(a.due_date) + " · " : "") + esc(a.status || "Open") + "</span></div></div>").join("")
        : '<div class="muted" style="font-size:11px">No remediation yet.</div>';
      return '<div class="card" style="margin-bottom:8px">' +
        '<div class="row" style="justify-content:space-between;align-items:center">' +
        '<b class="modelid">' + esc(id) + "</b>" + (m.name ? ' <span class="muted">' + esc(m.name) + "</span>" : "") +
        '<div><span class="muted" style="font-size:11px">Outcome</span> ' +
        '<select data-analysis-status="' + esc(id) + '">' + opts(m.analysis_status) + "</select></div></div>" +
        '<div class="field" style="margin-top:6px"><label>Discussion note</label>' +
        '<div class="row" style="align-items:flex-end;gap:6px">' +
        '<input data-analysis-note="' + esc(id) + '" value="' + esc(m.analysis_note || "") + '" style="flex:1">' +
        '<button class="btn small" data-analysis-note-save="' + esc(id) + '">Save note</button></div></div>' +
        '<div class="section-header" style="margin-top:8px;font-size:11px">Follow-on remediation</div>' + stepList +
        '<div class="row" style="margin-top:6px;flex-wrap:wrap;align-items:flex-end">' +
        '<div class="field"><label>Remediation</label><input id="act-desc-' + esc(id) + '"></div>' +
        '<div class="field"><label>Owner</label><input id="act-owner-' + esc(id) + '"></div>' +
        '<div class="field"><label>Due date</label><input type="date" id="act-date-' + esc(id) + '"></div>' +
        '<button class="btn small" data-act-add="' + esc(id) + '">Add remediation</button></div></div>';
    }).join("");
  },

  _scopeTable(cfg) {
    const inScope = new Set(cfg.inScope.map((m) => m[cfg.idKey]));
    const filter = this._scopeFilter();
    const candidates = this._candidates(cfg);
    const mrc = (this._meeting.data || {}).mrc;
    const mrcNote = mrc ? " for MRC <b>" + esc(mrc) + "</b>" : "";
    const lc = cfg.label.toLowerCase();
    const banner = filter
      ? '<div class="muted" style="margin-bottom:6px">Showing ' + lc + "s the MRC oversees" +
        mrcNote + " — " + esc(filter.key) + " <b>" + esc(filter.value) + "</b>. " +
        '<label style="margin-left:8px"><input type="checkbox" data-show-all="' + cfg.kind + '"' +
        (this[cfg.showAllKey] ? " checked" : "") + "> Show all</label></div>"
      : '<div class="muted" style="margin-bottom:6px">Company-wide MRC' + mrcNote +
        " — every " + lc + " is a candidate.</div>";
    const docBy = {}, presBy = {};
    cfg.inScope.forEach((r) => {
      if (r.analysis_original_name) docBy[r[cfg.idKey]] = r.analysis_original_name;
      if (r.presenter) presBy[r[cfg.idKey]] = r.presenter;
    });
    const rows = candidates.length ? candidates.map((m) => {
      const d = m.data || {};
      const id = m[cfg.idKey];
      const inS = inScope.has(id);
      return '<tr><td><input type="checkbox" data-scope="' + esc(id) + '"' + (inS ? " checked" : "") +
        '></td><td class="modelid">' + esc(id) + "</td><td>" + fieldDisplay(d[cfg.nameKey]) +
        "</td><td>" + tierBadge(d.tier) + "</td><td>" + ragBadge(d.rag_rating) +
        "</td><td>" + this._presenterCell(id, inS, presBy) +
        "</td><td>" + this._analysisCell(cfg, id, inS, docBy) + "</td></tr>";
    }).join("") : '<tr><td colspan="7" class="empty">No ' + lc + "s match this scope.</td></tr>";
    return banner +
      "<table><thead><tr><th></th><th>" + cfg.label + " ID</th><th>Name</th><th>Tier</th><th>RAG</th>" +
      "<th>Presenter</th><th>Analysis</th></tr></thead><tbody>" + rows + "</tbody></table>" +
      '<div class="row" style="margin-top:10px">' +
      '<button class="btn small primary" data-save-scope="' + cfg.kind + '">Save selection&hellip;</button>' +
      '<span class="muted" style="margin-left:8px">' + inScope.size + " in scope.</span></div>";
  },

  // Presenter per in-scope item: a dropdown of people from the register.
  _presenterCell(id, inScope, byId) {
    if (!inScope) return '<span class="muted">—</span>';
    const cur = byId[id] || "";
    const opts = ['<option value=""></option>'].concat((this._people || []).map((p) =>
      "<option" + (p.name === cur ? " selected" : "") + ">" + esc(p.name) + "</option>")).join("");
    return '<select data-presenter="' + esc(id) + '">' + opts + "</select>";
  },

  // Analysis document per in-scope item: a download link (if uploaded) + upload.
  _analysisCell(cfg, id, inScope, byId) {
    if (!inScope) return '<span class="muted" style="font-size:11px">add to scope first</span>';
    const name = byId[id];
    const link = name
      ? '<a href="/api/meetings/' + esc(this._id) + "/" + cfg.base + "/" + esc(id) +
        '/analysis" target="_blank">' + esc(name) + "</a> "
      : "";
    return link + '<input type="file" id="an-file-' + esc(id) + '" style="display:none">' +
      '<button class="btn small" data-an-upload="' + esc(id) + '">' + (name ? "Replace" : "Upload") + "&hellip;</button>";
  },

  _bindModels() {
    const self = this;
    this._bindSignoffs();
    const cfg = this._scopeCfg(this._analysisKind === "product" ? "product" : "model");
    const reload = () => self.show(self._id, "models_in_scope");
    // Analysis sub-tab switch (Models | Products) — re-render from cached data.
    document.querySelectorAll("[data-atab]").forEach(function (b) {
      b.onclick = function () { self._analysisKind = b.getAttribute("data-atab"); self._render(); };
    });
    const toggle = document.querySelector("[data-show-all]");
    if (toggle) toggle.onchange = function () { self[cfg.showAllKey] = toggle.checked; self._render(); };
    const itemById = {};
    cfg.inScope.forEach((r) => { itemById[r[cfg.idKey]] = r.item_id; });
    const scopePath = (id) => "/api/meetings/" + self._id + "/collections/" + cfg.collection + "/" + itemById[id];
    document.querySelectorAll("[data-analysis-status]").forEach(function (sel) {
      const id = sel.getAttribute("data-analysis-status");
      sel.onchange = () => App.amend("Set analysis outcome for " + id + " → " + sel.value + ".", "POST",
        scopePath(id), { fields: { analysis_status: sel.value } }, reload);
    });
    // The discussion note saves via an explicit button, not on blur: a
    // blur-triggered amend would collide with a subsequent click (e.g. Add
    // remediation), and the single pending-amend slot would silently drop one of
    // the two changes.
    document.querySelectorAll("[data-analysis-note-save]").forEach(function (btn) {
      const id = btn.getAttribute("data-analysis-note-save");
      btn.onclick = function () {
        const inp = document.querySelector('[data-analysis-note="' + id + '"]');
        App.amend("Set analysis note for " + id + ".", "POST",
          scopePath(id), { fields: { analysis_note: inp.value } }, reload);
      };
    });
    document.querySelectorAll("[data-presenter]").forEach(function (sel) {
      const id = sel.getAttribute("data-presenter");
      sel.onchange = () => App.amend("Set presenter for " + id + ".", "POST",
        scopePath(id), { fields: { presenter: sel.value } }, reload);
    });
    document.querySelectorAll("[data-act-add]").forEach(function (btn) {
      const id = btn.getAttribute("data-act-add");
      btn.onclick = function () {
        const desc = (document.getElementById("act-desc-" + id) || {}).value;
        if (!desc) { App.toast("Remediation description is required", "error"); return; }
        const owner = (document.getElementById("act-owner-" + id) || {}).value;
        const dt = (document.getElementById("act-date-" + id) || {}).value;
        const fields = { description: desc, status: "Open" };
        if (owner) fields.owner = owner;
        if (dt) fields.due_date = dt;
        App.amend("Add remediation for " + id + ".", "POST",
          "/api/" + cfg.base + "/" + id + "/collections/remediation_steps", { fields: fields }, reload);
      };
    });
    document.querySelectorAll("[data-an-upload]").forEach(function (btn) {
      const id = btn.getAttribute("data-an-upload");
      const fileInput = document.getElementById("an-file-" + id);
      btn.onclick = function () { fileInput.click(); };
      fileInput.onchange = function () {
        if (!fileInput.files.length) return;
        const form = new FormData();
        form.append("file", fileInput.files[0]);
        fetch("/api/meetings/" + self._id + "/" + cfg.base + "/" + id + "/analysis", {
          method: "POST", headers: { "X-Auth-Request-User": App.actor() }, body: form,
        }).then(async (res) => {
          if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || "upload failed"); }
          App.toast("Analysis uploaded", "ok");
          reload();
        }).catch((e) => App.toast(e.message, "error"));
      };
    });
    const saveBtn = document.querySelector("[data-save-scope]");
    if (saveBtn) saveBtn.onclick = function () {
      const selected = [];
      document.querySelectorAll("[data-scope]").forEach(function (cb) {
        if (cb.checked) selected.push(cb.getAttribute("data-scope"));
      });
      // Carry across in-scope ids the current filter hid, so a filtered save
      // doesn't silently drop them.
      const visible = new Set(self._candidates(cfg).map((m) => m[cfg.idKey]));
      cfg.inScope.forEach(function (m) { if (!visible.has(m[cfg.idKey])) selected.push(m[cfg.idKey]); });
      const body = {}; body[cfg.setKey] = selected;
      App.amend("Set " + selected.length + " " + cfg.label.toLowerCase() + "s in scope.", "POST",
        "/api/meetings/" + self._id + "/collections/" + cfg.collection + "/set", body, reload);
    };
  },
});
