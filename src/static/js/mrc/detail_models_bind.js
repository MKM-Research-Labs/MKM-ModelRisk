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

// Wiring the Signoff tab: the analysis sub-tab switch, the scope picker and its search,
// and the review accordion each scoped record opens into.
//
// Split from detail_models.js, which draws the tab and holds the per-kind config that
// makes models and products behave identically. This is everything the committee can
// DO on it, and it is the larger half by some way — a scope table that can be searched,
// disclosed, switched between kinds and reviewed item by item is mostly behaviour.
//
// It stays driven by the same per-kind config rather than branching on the kind: the
// point of that config is that a product's review is not a special case of a model's,
// and a second code path here would quietly make it one.
//
// Assigns onto MeetingDetail; loads after detail_models.js.

Object.assign(MeetingDetail, {

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
