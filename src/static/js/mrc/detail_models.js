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
  // Read from the served scope table (GET /api/meetings/fields), never restated
  // here. The console used to carry its own copy for models and products, which is
  // how ML Applications and AI Systems could be governed by a committee that had no
  // way to put them in front of itself: the record types existed, and the screen did
  // not know about them.
  _scopeKinds() { return (this._specs || {}).scope || []; },

  _scopeCfg(kind) {
    const served = this._scopeKinds().find((s) => s.kind === kind)
      || this._scopeKinds()[0] || {};
    // Where this screen keeps the two lists each kind needs: everything of that type,
    // and the rows already in scope at this meeting.
    const store = {
      model: { inventory: "_inventory", inScope: "_models", showAll: "_showAll" },
      product: { inventory: "_products", inScope: "_meetingProducts",
                 showAll: "_showAllProducts" },
      ml_application: { inventory: "_mlApplications", inScope: "_meetingMlApplications",
                        showAll: "_showAllMlApplications" },
      ai_system: { inventory: "_aiSystems", inScope: "_meetingAiSystems",
                   showAll: "_showAllAiSystems" },
    }[served.kind] || {};
    return {
      kind: served.kind, idKey: served.id_key, collection: served.collection,
      base: served.url, label: served.noun, plural: served.plural,
      nameKey: served.name_field,
      inventory: this[store.inventory] || [], inScope: this[store.inScope] || [],
      showAllKey: store.showAll, setKey: served.id_key + "s",
    };
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
        '<div class="section-header" style="margin-top:var(--space-9)">Analysis</div>' +
        this._analysisSubtabs("handoff") + this._handoffAnalysis();
    }
    const cfg = this._scopeCfg(this._analysisKind || "model");
    // First pass has no document list yet; fetch it, then re-render once. The
    // picker shows a placeholder in the meantime rather than an empty dropdown.
    if (this._reviewableDocs === undefined || this._reviewableDocsKind !== cfg.kind) {
      this._reviewableDocsKind = cfg.kind;
      this._reviewableDocs = {};
      this._loadReviewableDocs(cfg).then(() => this._render());
    }
    return this._approvalsSection() +
      '<div class="section-header" style="margin-top:var(--space-9)">Analysis</div>' +
      this._analysisSubtabs(cfg.kind) +
      '<p class="muted" style="font-size:var(--size-sm)">Choose the ' + cfg.plural +
      " in scope, then record the confirmation to proceed and any follow-on actions.</p>" +
      this._scopeTable(cfg) + this._analysisReview(cfg);
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
    const cfg = this._scopeCfg(this._analysisKind || "model");
    const reload = () => self.show(self._id, "models_in_scope");
    // Analysis sub-tab switch — one tab per record type the meeting can scope,
    // re-rendered from cached data.
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
    // The discussion note and the basis-to-proceed auto-save on change (blur /
    // Enter). Both are non-critical edits that apply without a confirmation dialog,
    // so there is no pending-confirm slot for a following click to collide with.
    document.querySelectorAll("[data-analysis-note]").forEach(function (inp) {
      const id = inp.getAttribute("data-analysis-note");
      inp.onchange = () => App.amend("Set analysis note for " + id + ".", "POST",
        scopePath(id), { fields: { analysis_note: inp.value } }, reload);
    });
    document.querySelectorAll("[data-analysis-basis]").forEach(function (inp) {
      const id = inp.getAttribute("data-analysis-basis");
      inp.onchange = () => App.amend("Set basis to proceed for " + id + ".", "POST",
        scopePath(id), { fields: { proceed_basis: inp.value } }, reload);
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
    document.querySelectorAll("[data-an-remove]").forEach(function (btn) {
      const id = btn.getAttribute("data-an-remove");
      btn.onclick = () => App.amend("Remove the analysis for " + id + ".", "POST",
        "/api/meetings/" + self._id + "/" + cfg.base + "/" + id + "/analysis/remove", {}, reload);
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
      App.amend("Set " + selected.length + " " + cfg.plural + " in scope.", "POST",
        "/api/meetings/" + self._id + "/collections/" + cfg.collection + "/set", body, reload);
    };
  },
});
