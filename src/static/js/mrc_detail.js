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
    const chip = (label, key) => '<span class="datechip" id="minfo-' + key + '"><span class="muted">' +
      label + ':</span> <b>' + fieldDisplay(d[key]) + "</b> " +
      '<span class="edit-btn" data-minfo="' + key + '">edit</span></span>';
    return '<div class="dh-dates">' + chip("Company", "company") + chip("Division", "division") +
      chip("Department", "department") + "</div>" +
      '<div class="dh-dates">' + chip("Date", "date") + chip("Time", "time") +
      chip("Location", "location") + chip("Chair", "chair") + chip("Status", "status") + "</div>";
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
    if (this._tab === "documents") {
      box.innerHTML = '<div class="empty">Document uploads are coming next.</div>'; return;
    }
    const spec = this.collSpec(this._tab);
    // Agenda / minutes / decisions / actions accept multiple new entries at
    // once; participants stays single because one-at-a-time matches the way
    // attendees are added in practice.
    const bulk = ["agenda", "minutes", "decisions", "actions"].indexOf(this._tab) >= 0;
    box.innerHTML = Collections.render(d, { collections: [spec] }, false, bulk);
    Collections.bind("/api/meetings/" + this._id + "/collections/", { collections: [spec] },
      false, () => this.show(this._id, this._tab), d, bulk);
  },

  // Org-scope filter: pick the most specific level set on the meeting and
  // show models that match it (department > division > company > all).
  _scopeFilter() {
    const md = this._meeting.data || {};
    if (md.department) return { key: "department", value: md.department };
    if (md.division) return { key: "division", value: md.division };
    if (md.company) return { key: "company", value: md.company };
    return null;
  },

  _candidateModels() {
    const filter = this._scopeFilter();
    if (this._showAll || !filter) return this._inventory.slice();
    return this._inventory.filter((m) => (m.data || {})[filter.key] === filter.value);
  },

  _modelsTab() {
    const inScope = new Set(this._models.map((m) => m.model_id));
    const filter = this._scopeFilter();
    const candidates = this._candidateModels();
    const banner = filter
      ? '<div class="muted" style="margin-bottom:6px">Filtered to ' + esc(filter.key) +
        " = <b>" + esc(filter.value) + "</b>. " +
        '<label style="margin-left:8px"><input type="checkbox" id="mt-show-all"' +
        (this._showAll ? " checked" : "") + "> Show all models</label></div>"
      : '<div class="muted" style="margin-bottom:6px">No org scope set on this meeting; ' +
        "showing all inventory.</div>";
    const rows = candidates.length ? candidates.map((m) => {
      const d = m.data || {};
      const checked = inScope.has(m.model_id) ? " checked" : "";
      return '<tr><td><input type="checkbox" data-mscope="' + esc(m.model_id) + '"' + checked +
        '></td><td class="modelid">' + esc(m.model_id) + "</td><td>" + fieldDisplay(d.name) +
        "</td><td>" + tierBadge(d.tier) + "</td><td>" + ragBadge(d.rag_rating) +
        "</td><td>" + fieldDisplay(d.company) + "</td></tr>";
    }).join("") :
      '<tr><td colspan="6" class="empty">No models match this scope.</td></tr>';
    return banner +
      "<table><thead><tr><th></th><th>Model ID</th><th>Name</th><th>Tier</th><th>RAG</th>" +
      "<th>Company</th></tr></thead><tbody>" + rows + "</tbody></table>" +
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
