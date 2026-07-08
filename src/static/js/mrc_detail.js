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

// Tabbed MRC meeting detail: Agenda / Minutes / Participants / Models /
// Decisions / Actions / Documents. The collection tabs reuse the shared
// Collections renderer (add/edit/remove); Models joins the inventory.
const MeetingDetail = {
  _id: null, _meeting: null, _specs: null, _models: [], _inventory: [],
  _tab: "agenda", _showAll: false,

  async show(meetingId, tab) {
    this._id = meetingId;
    this._specs = await MRC.specs();
    this._meeting = await App.get("/api/meetings/" + meetingId);
    this._models = await App.get("/api/meetings/" + meetingId + "/models");
    this._inventory = await App.get("/api/models");
    if (tab) this._tab = tab;
    this._render();
    document.getElementById("mt-detail").scrollIntoView({ block: "start" });
  },

  collSpec(key) { return this._specs.collections.find((c) => c.key === key); },

  _render() {
    const m = this._meeting, d = m.data || {};
    document.getElementById("mt-detail").innerHTML =
      '<div class="card">' + this._header(m, d) + this._info(d) + this._tabbar(d) +
      '<div id="mtd-content"></div></div>';
    document.querySelectorAll("[data-mtab]").forEach((b) => {
      b.onclick = () => { this._tab = b.getAttribute("data-mtab"); this._render(); };
    });
    this._bindInfo(d);
    this._renderContent();
  },

  _header(m, d) {
    return '<div class="detail-header"><div>' +
      '<button class="btn small" id="mt-back">&larr; Back</button> ' +
      '<span class="name" style="margin-left:8px">' + esc(d.title || m.meeting_id) + "</span> " +
      statusBadge(m.status) + "</div>" +
      '<div class="right"><button class="btn small" id="mt-pdf">&darr; Meeting Pack PDF</button></div></div>';
  },

  _info(d) {
    // Phase MRC-2/5: mrc + org tier and chair are derived from the MRC binding;
    // shown read-only. date/time/location/status stay editable.
    const readOnly = (label, key) => '<span class="datechip" id="minfo-' + key + '">' +
      '<span class="muted">' + label + ':</span> <b>' + fieldDisplay(d[key]) + "</b></span>";
    const editable = (label, key) => '<span class="datechip" id="minfo-' + key + '"><span class="muted">' +
      label + ':</span> <b>' + fieldDisplay(d[key]) + "</b> " +
      '<span class="edit-btn" data-minfo="' + key + '">edit</span></span>';
    return '<div class="dh-dates">' + readOnly("MRC", "mrc") + readOnly("Division", "division") +
      readOnly("Department", "department") + readOnly("Chair", "chair") + "</div>" +
      '<div class="dh-dates">' + editable("Date", "date") + editable("Time", "time") +
      editable("Location", "location") + editable("Status", "status") + "</div>";
  },

  _tabbar(d) {
    const n = (k) => (d[k] || []).length;
    const tabs = [
      ["agenda", "Agenda"], ["minutes", "Minutes"], ["participants", "Participants"],
      ["models_in_scope", "Models"], ["decisions", "Decisions"], ["actions", "Actions"],
      ["documents", "Documents"],
    ];
    return '<div class="dtabs">' + tabs.map((t) =>
      '<button class="dtab' + (t[0] === this._tab ? " active" : "") + '" data-mtab="' + t[0] + '">' +
      esc(t[1]) + " (" + n(t[0]) + ")</button>").join("") + "</div>";
  },

  _renderContent() {
    const d = this._meeting.data || {};
    const box = document.getElementById("mtd-content");
    if (this._tab === "models_in_scope") { box.innerHTML = this._modelsTab(); this._bindModels(); return; }
    // Agenda has a bespoke two-row layout (Title + Description on top, the rest
    // below) with its own add/edit/remove + sign-off actions.
    if (this._tab === "agenda") { box.innerHTML = this._agendaContent(); this._bindAgenda(); return; }
    if (this._tab === "documents") {
      box.innerHTML = '<div class="empty">Document uploads are coming next.</div>'; return;
    }
    const spec = this.collSpec(this._tab);
    // Minutes / decisions / actions accept multiple new entries at once;
    // participants stays single because one-at-a-time matches practice.
    const bulk = ["minutes", "decisions", "actions"].indexOf(this._tab) >= 0;
    box.innerHTML = Collections.render(d, { collections: [spec] }, false, bulk);
    Collections.bind("/api/meetings/" + this._id + "/collections/", { collections: [spec] },
      false, () => this.show(this._id, this._tab), d, bulk);
  },

  // Agenda: each item on two rows — Title + Description up top, the rest below —
  // plus an add form. Hidden fields (e.g. the escalation back-pointers) never
  // show. Sign-off items (subject model + proposed RAG) get Approve / Escalate.
  _agendaVisible() {
    return this.collSpec("agenda").fields.filter((f) => !f.hidden);
  },

  _agendaContent() {
    const items = (this._meeting.data || {}).agenda || [];
    const cards = items.length
      ? items.map((it, i) => this._agendaCard(it, i)).join("")
      : '<div class="empty">No agenda items yet.</div>';
    const addInputs = this._agendaVisible().map((f) =>
      '<div class="field"><label>' + esc(f.label) + (f.required ? " *" : "") + "</label>" +
      inputControl("ag-add-" + f.key, f) + "</div>").join("");
    return '<div id="agenda-list">' + cards + "</div>" +
      '<div class="section-header" style="margin-top:14px">Add agenda item</div>' +
      '<div class="row" style="flex-wrap:wrap;align-items:flex-end">' + addInputs +
      '<button class="btn small primary" id="ag-add">Add&hellip;</button></div>';
  },

  _agendaCard(item, idx) {
    const signoff = item.subject_model_id && item.proposed_rag;
    const meta = [];
    if (item.presenter) meta.push("Presenter: <b>" + esc(item.presenter) + "</b>");
    meta.push("Status: " + statusBadge(item.status));
    if (signoff) {
      meta.push('Sign-off: <span class="code">' + esc(item.subject_model_id) + "</span> &rarr; " +
        ragBadge(item.proposed_rag));
    }
    const pending = signoff && item.status === "Pending";
    const actions =
      '<span class="edit-btn" data-aged="' + esc(item.item_id) + '">edit</span> ' +
      '<span class="edit-btn" data-agrm="' + esc(item.item_id) + '">remove</span>' +
      (pending
        ? ' <span class="edit-btn" data-agapprove="' + esc(item.item_id) +
          '" style="color:#388e3c;font-weight:600">approve sign-off</span>' +
          ' <span class="edit-btn" data-agescalate="' + esc(item.item_id) +
          '" style="color:#f57c00;font-weight:600">escalate</span>'
        : "");
    return '<div class="card" style="margin-bottom:8px" id="agrow-' + esc(item.item_id) + '">' +
      '<div class="row" style="justify-content:space-between;align-items:flex-start">' +
      "<div><b>" + (idx + 1) + ". " + esc(item.title || "") + "</b>" +
      (item.description ? '<div class="muted" style="margin-top:2px">' + esc(item.description) + "</div>" : "") +
      '</div><div class="rowact">' + actions + "</div></div>" +
      '<div class="muted" style="margin-top:8px">' + meta.join(" &nbsp;·&nbsp; ") + "</div></div>";
  },

  _bindAgenda() {
    const self = this;
    const visible = this._agendaVisible();
    const items = (this._meeting.data || {}).agenda || [];
    const byId = (attr, el) => items.find((i) => i.item_id === el.getAttribute(attr));
    document.getElementById("ag-add").onclick = function () {
      const fields = {};
      visible.forEach((f) => { const v = val("ag-add-" + f.key); if (v !== "") fields[f.key] = v; });
      if (!fields.title) { App.toast("Title is required", "error"); return; }
      App.amend("Add an agenda item.", "POST",
        "/api/meetings/" + self._id + "/collections/agenda", { fields: fields },
        () => self.show(self._id, "agenda"));
    };
    document.querySelectorAll("[data-agrm]").forEach(function (btn) {
      const id = btn.getAttribute("data-agrm");
      btn.onclick = () => App.amend("Remove agenda item " + id + ".", "POST",
        "/api/meetings/" + self._id + "/collections/agenda/" + id + "/delete", {},
        () => self.show(self._id, "agenda"));
    });
    document.querySelectorAll("[data-aged]").forEach(function (btn) {
      btn.onclick = () => self._agendaEdit(byId("data-aged", btn), visible);
    });
    document.querySelectorAll("[data-agapprove]").forEach(function (btn) {
      const item = byId("data-agapprove", btn);
      btn.onclick = () => App.amend("Approve sign-off for " + item.subject_model_id +
        " → " + item.proposed_rag + ".", "POST",
        "/api/meetings/" + self._id + "/agenda/" + item.item_id + "/approve-signoff", {},
        () => self.show(self._id, "agenda"));
    });
    document.querySelectorAll("[data-agescalate]").forEach(function (btn) {
      btn.onclick = () => self._openEscalatePicker(byId("data-agescalate", btn));
    });
  },

  _agendaEdit(item, visible) {
    const card = document.getElementById("agrow-" + item.item_id);
    card.innerHTML =
      '<div class="row" style="flex-wrap:wrap;align-items:flex-end">' +
      visible.map((f) => '<div class="field"><label>' + esc(f.label) + "</label>" +
        inputControl("ag-ed-" + f.key, f) + "</div>").join("") +
      '<button class="btn small primary" id="ag-save">Save&hellip;</button>' +
      '<button class="btn small" id="ag-cancel">Cancel</button></div>';
    visible.forEach((f) => {
      const el = document.getElementById("ag-ed-" + f.key);
      if (item[f.key] !== null && item[f.key] !== undefined) el.value = item[f.key];
    });
    document.getElementById("ag-cancel").onclick = () => this.show(this._id, "agenda");
    document.getElementById("ag-save").onclick = () => {
      const fields = {};
      visible.forEach((f) => { const v = val("ag-ed-" + f.key); if (v !== "") fields[f.key] = v; });
      App.amend("Update agenda item " + item.item_id + ".", "POST",
        "/api/meetings/" + this._id + "/collections/agenda/" + item.item_id, { fields: fields },
        () => this.show(this._id, "agenda"));
    };
  },

  // Phase MRC-4: reuse the sign-off picker overlay to choose which parent-MRC
  // Scheduled meeting the escalation lands on.
  async _openEscalatePicker(item) {
    const meetings = (await App.get("/api/meetings")).filter(
      (m) => m.status === "Scheduled" && m.meeting_id !== this._id,
    );
    if (!meetings.length) {
      App.toast("No other Scheduled meetings available to escalate to.", "error");
      return;
    }
    const pick = document.getElementById("signoff-meeting-pick");
    pick.innerHTML = meetings.map((m) => "<option value=\"" + esc(m.meeting_id) + "\">" +
      esc(m.meeting_id) + " · " + esc(m.data.title || "") +
      (m.data.date ? " (" + esc(m.data.date) + ")" : "") + "</option>").join("");
    document.getElementById("signoff-summary").innerHTML =
      "Escalate sign-off for <b>" + esc(item.subject_model_id) +
      "</b> → proposed <b>" + esc(item.proposed_rag) + "</b> to a higher-tier MRC meeting.";
    const overlay = document.getElementById("signoff-overlay");
    overlay.classList.remove("hidden");
    const self = this;
    document.getElementById("signoff-cancel").onclick = () => overlay.classList.add("hidden");
    document.getElementById("signoff-submit").onclick = () => {
      const parentMeetingId = pick.value;
      overlay.classList.add("hidden");
      App.amend("Escalate sign-off to " + parentMeetingId + ".", "POST",
        "/api/meetings/" + self._id + "/agenda/" + item.item_id + "/escalate-signoff",
        { parent_meeting_id: parentMeetingId }, () => self.show(self._id, self._tab));
    };
  },

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
  _modelsTab() {
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
    const rows = candidates.length ? candidates.map((m) => {
      const d = m.data || {};
      const checked = inScope.has(m.model_id) ? " checked" : "";
      return '<tr><td><input type="checkbox" data-mscope="' + esc(m.model_id) + '"' + checked +
        '></td><td class="modelid">' + esc(m.model_id) + "</td><td>" + fieldDisplay(d.name) +
        "</td><td>" + tierBadge(d.tier) + "</td><td>" + ragBadge(d.rag_rating) +
        "</td><td>" + fieldDisplay(d.division) + "</td></tr>";
    }).join("") :
      '<tr><td colspan="6" class="empty">No models match this scope.</td></tr>';
    return banner +
      "<table><thead><tr><th></th><th>Model ID</th><th>Name</th><th>Tier</th><th>RAG</th>" +
      "<th>Division</th></tr></thead><tbody>" + rows + "</tbody></table>" +
      '<div class="row" style="margin-top:10px">' +
      '<button class="btn small primary" id="mt-save-models">Save selection&hellip;</button>' +
      '<span class="muted" id="mt-models-summary" style="margin-left:8px">' +
      inScope.size + " model" + (inScope.size === 1 ? "" : "s") + " currently in scope." +
      "</span></div>";
  },

  _bindModels() {
    const self = this;
    const toggle = document.getElementById("mt-show-all");
    if (toggle) toggle.onchange = function () {
      self._showAll = toggle.checked; self._render();
    };
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

  _bindInfo(d) {
    const self = this;
    document.getElementById("mt-back").onclick = function () {
      document.getElementById("mt-detail").innerHTML = ""; MRC.loadList();
    };
    document.getElementById("mt-pdf").onclick = function () {
      window.open("/api/meetings/" + self._id + "/pack.pdf", "_blank");
    };
    document.querySelectorAll("[data-minfo]").forEach(function (btn) {
      const key = btn.getAttribute("data-minfo");
      btn.onclick = function () { self._editField(key, d[key]); };
    });
  },

  _editField(key, current) {
    const f = MRC.specFieldByKey(key);
    const chip = document.getElementById("minfo-" + key);
    chip.innerHTML = inputControl("mf-input", f) +
      '<button class="btn small primary" id="mf-save">Save</button>' +
      '<button class="btn small" id="mf-cancel">Cancel</button>';
    const input = document.getElementById("mf-input");
    if (current !== null && current !== undefined) input.value = current;
    document.getElementById("mf-cancel").onclick = () => this.show(this._id, this._tab);
    document.getElementById("mf-save").onclick = () => {
      App.amend("Set " + f.label + ' = "' + input.value + '" on ' + this._id + ".", "POST",
        "/api/meetings/" + this._id + "/field", { field: key, value: input.value.trim() },
        () => { this.show(this._id, this._tab); MRC.loadList(); });
    };
  },
};
