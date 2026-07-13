// Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
//
// This software is licensed by MKM Research Labs for non-commercial
// research and educational use only. Any commercial use, including
// but not limited to use in or for products or services offered for sale,
// internal business operations intended for commercial advantage, or
// research and development conducted for a commercial entity, is expressly
// prohibited unless separately authorized in writing by MKM Research Labs.
//
// Use, reproduction, distribution, or modification of this code is subject to the
// terms and conditions of the license agreement provided with this software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

// MeetingDetail — the Models tab: the home for every model decision point.
// Approvals (from the sign-off module) plus Analysis — the in-scope selection
// table, each model's confirmation to proceed + note, and follow-on actions.
Object.assign(MeetingDetail, {
  // Org-scope filter: pick the most specific level set on the meeting (which
  // is derived from its bound MRC via the enriched meeting read) and show
  // models that match it (department > division > all).
  _scopeFilter() {
    const md = this._meeting.data || {};
    if (md.department) return { key: "department", value: md.department };
    if (md.division) return { key: "division", value: md.division };
    return null;
  },

  _candidateModels() {
    const filter = this._scopeFilter();
    if (this._showAll || !filter) return this._inventory.slice();
    return this._inventory.filter((m) => (m.data || {})[filter.key] === filter.value);
  },

  // Phase MRC-3: name the MRC in the filter banner so the chair can see at a
  // glance which committee's remit is being surfaced.
  // The Models tab is the home for every model decision point: Approvals (the
  // risk-rating sign-offs) and Analysis (in-scope models with the MRC's
  // confirmation to proceed and any follow-on actions).
  _modelsTab() {
    return this._approvalsSection() +
      '<div class="section-header" style="margin-top:18px">Analysis</div>' +
      '<p class="muted" style="font-size:12px">Choose the models in scope, then record the ' +
      "confirmation to proceed and any follow-on actions.</p>" +
      this._scopeTable() + this._analysisReview();
  },

  // One review block per in-scope model: the MRC's confirmation to proceed
  // (reviewed, discussed, agreed) with a note, plus follow-on action items. The
  // actions are owned by the model; the committee adds them and files dated
  // updates here (the full history lives on the model's Actions tab).
  _analysisReview() {
    const inScope = this._models;
    if (!inScope.length) {
      return '<div class="muted" style="font-size:12px;margin-top:8px">' +
        "Add models to scope above to record their analysis outcome and actions.</div>";
    }
    const byId = {};
    (this._inventory || []).forEach((m) => { byId[m.model_id] = (m.data || {}).actions || []; });
    const opts = (cur) => ["Pending", "Reviewed — agreed to proceed"].map((s) =>
      "<option" + (s === (cur || "Pending") ? " selected" : "") + ">" + esc(s) + "</option>").join("");
    const blocks = inScope.map((m) => {
      const mid = m.model_id;
      const acts = byId[mid] || [];
      const actList = acts.length
        ? acts.map((a) => '<div class="prow"><div style="font-size:12px">' + esc(a.description) +
            ' <span class="muted" style="font-size:10px">' +
            (a.target_date ? "target " + esc(a.target_date) + " · " : "") + esc(a.status || "Open") + "</span></div>" +
            (a.status !== "Closed"
              ? '<div class="pact"><input placeholder="update…" id="mact-note-' + esc(mid) + "-" + esc(a.item_id) +
                '" style="font-size:11px;width:110px"> <button class="btn small" data-mact-update="' +
                esc(mid) + "|" + esc(a.item_id) + '">Update</button></div>' : "") + "</div>").join("")
        : '<div class="muted" style="font-size:11px">No actions yet.</div>';
      return '<div class="card" style="margin-bottom:8px">' +
        '<div class="row" style="justify-content:space-between;align-items:center">' +
        '<b class="modelid">' + esc(mid) + "</b>" +
        '<div><span class="muted" style="font-size:11px">Outcome</span> ' +
        '<select data-analysis-status="' + esc(mid) + '">' + opts(m.analysis_status) + "</select></div></div>" +
        '<div class="field" style="margin-top:6px"><label>Discussion note</label>' +
        '<input data-analysis-note="' + esc(mid) + '" value="' + esc(m.analysis_note || "") + '"></div>' +
        '<div class="section-header" style="margin-top:8px;font-size:11px">Follow-on actions</div>' + actList +
        '<div class="row" style="margin-top:6px;flex-wrap:wrap;align-items:flex-end">' +
        '<div class="field"><label>Action</label><input id="act-desc-' + esc(mid) + '"></div>' +
        '<div class="field"><label>Owner</label><input id="act-owner-' + esc(mid) + '"></div>' +
        '<div class="field"><label>Target</label><input type="date" id="act-date-' + esc(mid) + '"></div>' +
        '<button class="btn small" data-act-add="' + esc(mid) + '">Add action</button></div></div>';
    }).join("");
    return blocks;
  },

  _scopeTable() {
    const inScope = new Set(this._models.map((m) => m.model_id));
    const filter = this._scopeFilter();
    const candidates = this._candidateModels();
    const mrc = (this._meeting.data || {}).mrc;
    const mrcNote = mrc ? " for MRC <b>" + esc(mrc) + "</b>" : "";
    const banner = filter
      ? '<div class="muted" style="margin-bottom:6px">Showing models the MRC oversees' +
        mrcNote + " — " + esc(filter.key) + " <b>" + esc(filter.value) + "</b>. " +
        '<label style="margin-left:8px"><input type="checkbox" id="mt-show-all"' +
        (this._showAll ? " checked" : "") + "> Show all models</label></div>"
      : '<div class="muted" style="margin-bottom:6px">Company-wide MRC' + mrcNote +
        " — every inventory model is a candidate.</div>";
    const analysisByModel = {}, presenterByModel = {};
    this._models.forEach((r) => {
      if (r.analysis_original_name) analysisByModel[r.model_id] = r.analysis_original_name;
      if (r.presenter) presenterByModel[r.model_id] = r.presenter;
    });
    const rows = candidates.length ? candidates.map((m) => {
      const d = m.data || {};
      const inS = inScope.has(m.model_id);
      const checked = inS ? " checked" : "";
      return '<tr><td><input type="checkbox" data-mscope="' + esc(m.model_id) + '"' + checked +
        '></td><td class="modelid">' + esc(m.model_id) + "</td><td>" + fieldDisplay(d.name) +
        "</td><td>" + tierBadge(d.tier) + "</td><td>" + ragBadge(d.rag_rating) +
        "</td><td>" + this._presenterCell(m.model_id, inS, presenterByModel) +
        "</td><td>" + this._analysisCell(m.model_id, inS, analysisByModel) +
        "</td></tr>";
    }).join("") :
      '<tr><td colspan="7" class="empty">No models match this scope.</td></tr>';
    return banner +
      "<table><thead><tr><th></th><th>Model ID</th><th>Name</th><th>Tier</th><th>RAG</th>" +
      "<th>Presenter</th><th>Analysis</th></tr></thead><tbody>" + rows + "</tbody></table>" +
      '<div class="row" style="margin-top:10px">' +
      '<button class="btn small primary" id="mt-save-models">Save selection&hellip;</button>' +
      '<span class="muted" id="mt-models-summary" style="margin-left:8px">' +
      inScope.size + " model" + (inScope.size === 1 ? "" : "s") + " currently in scope." +
      "</span></div>";
  },

  // Presenter per in-scope model: a dropdown of people from the register.
  _presenterCell(modelId, inScope, byModel) {
    if (!inScope) return '<span class="muted">—</span>';
    const cur = byModel[modelId] || "";
    const opts = ['<option value=""></option>'].concat((this._people || []).map((p) =>
      "<option" + (p.name === cur ? " selected" : "") + ">" + esc(p.name) + "</option>")).join("");
    return '<select data-presenter="' + esc(modelId) + '">' + opts + "</select>";
  },

  // Analysis document per in-scope model: a download link (if uploaded) plus an
  // upload control. Only in-scope models can carry one (nothing to attach to
  // until the model set is saved).
  _analysisCell(modelId, inScope, byModel) {
    if (!inScope) return '<span class="muted" style="font-size:11px">add to scope first</span>';
    const name = byModel[modelId];
    const link = name
      ? '<a href="/api/meetings/' + esc(this._id) + "/models/" + esc(modelId) +
        '/analysis" target="_blank">' + esc(name) + "</a> "
      : "";
    return link + '<input type="file" id="an-file-' + esc(modelId) + '" style="display:none">' +
      '<button class="btn small" data-an-upload="' + esc(modelId) + '">' +
      (name ? "Replace" : "Upload") + "&hellip;</button>";
  },

  _bindModels() {
    const self = this;
    this._bindSignoffs();
    const toggle = document.getElementById("mt-show-all");
    if (toggle) toggle.onchange = function () {
      self._showAll = toggle.checked; self._render();
    };
    const itemByModel = {};
    self._models.forEach((r) => { itemByModel[r.model_id] = r.item_id; });
    // Confirmation to proceed + discussion note per in-scope model.
    document.querySelectorAll("[data-analysis-status]").forEach(function (sel) {
      const modelId = sel.getAttribute("data-analysis-status");
      sel.onchange = function () {
        App.amend("Set analysis outcome for " + modelId + " → " + sel.value + ".", "POST",
          "/api/meetings/" + self._id + "/collections/models_in_scope/" + itemByModel[modelId],
          { fields: { analysis_status: sel.value } }, () => self.show(self._id, "models_in_scope"));
      };
    });
    document.querySelectorAll("[data-analysis-note]").forEach(function (inp) {
      const modelId = inp.getAttribute("data-analysis-note");
      inp.onchange = function () {
        App.amend("Set analysis note for " + modelId + ".", "POST",
          "/api/meetings/" + self._id + "/collections/models_in_scope/" + itemByModel[modelId],
          { fields: { analysis_note: inp.value } }, () => self.show(self._id, "models_in_scope"));
      };
    });
    // Follow-on actions are owned by the model. Adding one seeds its update
    // history and records the meeting it was raised at.
    const today = new Date().toISOString().slice(0, 10);
    const byId = {};
    (self._inventory || []).forEach((m) => { byId[m.model_id] = (m.data || {}).actions || []; });
    document.querySelectorAll("[data-act-add]").forEach(function (btn) {
      const mid = btn.getAttribute("data-act-add");
      btn.onclick = function () {
        const desc = (document.getElementById("act-desc-" + mid) || {}).value;
        if (!desc) { App.toast("Action description is required", "error"); return; }
        const owner = (document.getElementById("act-owner-" + mid) || {}).value;
        const date = (document.getElementById("act-date-" + mid) || {}).value;
        const fields = { description: desc, status: "Open", raised_meeting: self._id,
          updates: [{ date: today, note: "Raised at " + self._id, target_date: date || "", status: "Open" }] };
        if (owner) fields.owner = owner;
        if (date) fields.target_date = date;
        App.amend("Add action for " + mid + ".", "POST",
          "/api/models/" + mid + "/collections/actions",
          { fields: fields }, () => self.show(self._id, "models_in_scope"));
      };
    });
    document.querySelectorAll("[data-mact-update]").forEach(function (btn) {
      const [mid, aid] = btn.getAttribute("data-mact-update").split("|");
      btn.onclick = function () {
        const note = (document.getElementById("mact-note-" + mid + "-" + aid) || {}).value;
        if (!note) { App.toast("Enter an update note", "error"); return; }
        const action = (byId[mid] || []).find((a) => a.item_id === aid) || {};
        const updates = (action.updates || []).concat(
          [{ date: today, note: note, target_date: action.target_date || "", status: action.status || "Open" }]);
        App.amend("Update action " + aid + " on " + mid + ".", "POST",
          "/api/models/" + mid + "/collections/actions/" + aid,
          { fields: { updates: updates } }, () => self.show(self._id, "models_in_scope"));
      };
    });
    document.querySelectorAll("[data-presenter]").forEach(function (sel) {
      const modelId = sel.getAttribute("data-presenter");
      sel.onchange = function () {
        App.amend("Set presenter for " + modelId + ".", "POST",
          "/api/meetings/" + self._id + "/collections/models_in_scope/" + itemByModel[modelId],
          { fields: { presenter: sel.value } }, () => self.show(self._id, "models_in_scope"));
      };
    });
    document.querySelectorAll("[data-an-upload]").forEach(function (btn) {
      const modelId = btn.getAttribute("data-an-upload");
      const fileInput = document.getElementById("an-file-" + modelId);
      btn.onclick = function () { fileInput.click(); };
      fileInput.onchange = function () {
        if (!fileInput.files.length) return;
        const form = new FormData();
        form.append("file", fileInput.files[0]);
        fetch("/api/meetings/" + self._id + "/models/" + modelId + "/analysis", {
          method: "POST", headers: { "X-Auth-Request-User": App.actor() }, body: form,
        }).then(async (res) => {
          if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || "upload failed"); }
          App.toast("Analysis uploaded", "ok");
          self.show(self._id, "models_in_scope");
        }).catch((e) => App.toast(e.message, "error"));
      };
    });
    document.getElementById("mt-save-models").onclick = function () {
      const selected = [];
      document.querySelectorAll("[data-mscope]").forEach(function (cb) {
        if (cb.checked) selected.push(cb.getAttribute("data-mscope"));
      });
      // Carry across any in-scope ids that the current filter hid, so the
      // user doesn't accidentally remove them by saving a filtered view.
      const visible = new Set(self._candidateModels().map((m) => m.model_id));
      self._models.forEach(function (m) {
        if (!visible.has(m.model_id)) selected.push(m.model_id);
      });
      App.amend("Set " + selected.length + " models in scope.", "POST",
        "/api/meetings/" + self._id + "/collections/models_in_scope/set",
        { model_ids: selected }, () => self.show(self._id, "models_in_scope"));
    };
  },
});
