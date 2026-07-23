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
    if (this._analysisKind === "handoff") {
      return this._approvalsSection() +
        '<div class="section-header" style="margin-top:18px">Analysis</div>' +
        this._analysisSubtabs("handoff") + this._handoffAnalysis();
    }
    const cfg = this._scopeCfg(this._analysisKind === "product" ? "product" : "model");
    // First pass has no document list yet; fetch it, then re-render once. The
    // picker shows a placeholder in the meantime rather than an empty dropdown.
    if (this._reviewableDocs === undefined || this._reviewableDocsKind !== cfg.kind) {
      this._reviewableDocsKind = cfg.kind;
      this._reviewableDocs = {};
      this._loadReviewableDocs(cfg).then(() => this._render());
    }
    return this._approvalsSection() +
      '<div class="section-header" style="margin-top:18px">Analysis</div>' +
      this._analysisSubtabs(cfg.kind) +
      '<p class="muted" style="font-size:12px">Choose the ' + cfg.label.toLowerCase() +
      "s in scope, then record the confirmation to proceed and any follow-on actions.</p>" +
      this._scopeTable(cfg) + this._analysisReview(cfg);
  },

  // Handoffs crossing the models in scope: the compatibility record the committee
  // reviews alongside the models either side of it. Derived from the meeting's
  // sign-off items rather than a scope collection — a handoff reaches a meeting by
  // being raised for sign-off, not by being ticked into scope.
  _handoffAnalysis() {
    const items = this._signoffItems("handoff");
    if (!items.length) {
      return '<div class="muted" style="font-size:12px;margin-top:8px">No handoffs ' +
        "tabled at this meeting. They arrive by being raised for compatibility sign-off.</div>";
    }
    const rows = items.map((it) => {
      const pair = String(it.subject_handoff_id || "").split("~");
      return '<div class="card" style="margin-bottom:8px">' +
        '<div class="row" style="justify-content:space-between;align-items:center">' +
        "<div>" + this._subjectLabelHtml(pair[0] || "") +
        ' <span class="muted">&rarr;</span> ' + this._subjectLabelHtml(pair[1] || "") + "</div>" +
        "<div>" + statusBadge(it.status) + "</div></div></div>";
    }).join("");
    return '<p class="muted" style="font-size:12px">The producer &rarr; consumer handoffs ' +
      "tabled here, with the committee's compatibility decision.</p>" + rows;
  },

  _analysisSubtabs(kind) {
    const btn = (k, label) => '<button class="dtab' + (k === kind ? " active" : "") +
      '" data-atab="' + k + '">' + label + "</button>";
    return '<div class="dtabs" style="margin-bottom:8px">' +
      btn("model", "Models") + btn("product", "Products") +
      btn("handoff", "Handoffs") + "</div>";
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
      // One line per item, expanding to its review block. A committee works
      // through these one at a time, so seven open blocks is six too many.
      const open = this._reviewOpen === id;
      const head = '<div class="row" data-review-toggle="' + esc(id) +
        '" style="justify-content:space-between;align-items:center;cursor:pointer">' +
        "<div><span class=\"muted\">" + (open ? "&minus;" : "+") + "</span> " +
        '<b class="modelid">' + esc(id) + "</b>" +
        (m.name ? ' <span class="muted">' + esc(m.name) + "</span>" : "") + "</div>" +
        '<div><span class="muted" style="font-size:11px">Outcome</span> ' +
        '<select data-analysis-status="' + esc(id) + '">' + opts(m.analysis_status) + "</select></div></div>";
      if (!open) return '<div class="card" style="margin-bottom:6px">' + head + "</div>";
      return '<div class="card" style="margin-bottom:8px">' + head +
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

  // The reviewable documents held by each in-scope model, fetched once per render
  // so the picker can offer them without a request per row.
  async _loadReviewableDocs(cfg) {
    const ids = cfg.inScope.map((m) => m[cfg.idKey]);
    if (!ids.length) { this._reviewableDocs = {}; return; }
    const out = {};
    await Promise.all(ids.map(async (id) => {
      try { out[id] = await App.get("/api/" + cfg.base + "/" + id + "/reviewable-documents"); }
      catch (e) { out[id] = []; }
    }));
    this._reviewableDocs = out;
  },

  _bindModels() {
    const self = this;
    this._bindSignoffs();
    const cfg = this._scopeCfg(this._analysisKind === "product" ? "product" : "model");
    const reload = () => self.show(self._id, "models_in_scope");
    // Analysis sub-tab switch (Models | Products) — re-render from cached data.
    // Scope picker disclosure, its search filter, and the review accordion.
    // The tabled paper is a reference to a document the model holds.
    document.querySelectorAll("[data-analysis-ref]").forEach(function (sel) {
      const id = sel.getAttribute("data-analysis-ref");
      sel.onchange = function () {
        const row = (cfg.inScope || []).find((m) => m[cfg.idKey] === id);
        if (!row) return;
        App.amend("Table " + (sel.value ? "a paper" : "no paper") + " for " + id + ".",
          "POST", "/api/meetings/" + self._id + "/collections/" + cfg.collection + "/" + row.item_id,
          { fields: { analysis_item_id: sel.value } },
          () => self.show(self._id, self._tab));
      };
    });
    document.querySelectorAll("[data-scope-toggle]").forEach(function (b) {
      const k = b.getAttribute("data-scope-toggle");
      b.onclick = function () { self["_scopeOpen_" + k] = !self._scopeOpen(k); self._render(); };
    });
    document.querySelectorAll("[data-review-toggle]").forEach(function (b) {
      const id = b.getAttribute("data-review-toggle");
      b.onclick = function (e) {
        // The outcome dropdown lives in the header; clicking it must not collapse.
        if (e.target.closest("select")) return;
        self._reviewOpen = self._reviewOpen === id ? null : id;
        self._render();
      };
    });
    const search = document.getElementById("scope-search-" + cfg.kind);
    if (search) {
      // Filter in place rather than re-rendering: a re-render would lose focus
      // and the caret after every keystroke.
      search.oninput = function () {
        const q = search.value.trim().toLowerCase();
        search.closest(".card, div").parentNode
          .querySelectorAll(".scope-scroll tbody tr").forEach(function (tr) {
            tr.style.display = !q || tr.textContent.toLowerCase().indexOf(q) >= 0 ? "" : "none";
          });
      };
    }
    document.querySelectorAll("[data-sgtab]").forEach(function (b) {
      b.onclick = function () { self._approvalKind = b.getAttribute("data-sgtab"); self._render(); };
    });
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
