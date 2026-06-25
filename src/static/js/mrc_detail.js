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
  _id: null, _meeting: null, _specs: null, _models: [], _tab: "agenda",

  async show(meetingId, tab) {
    this._id = meetingId;
    this._specs = await MRC.specs();
    this._meeting = await App.get("/api/meetings/" + meetingId);
    this._models = await App.get("/api/meetings/" + meetingId + "/models");
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
    box.innerHTML = Collections.render(d, { collections: [spec] }, false);
    Collections.bind("/api/meetings/" + this._id + "/collections/", { collections: [spec] },
      false, () => this.show(this._id, this._tab), d);
  },

  _modelsTab() {
    const rows = this._models.length ? this._models.map((m) =>
      '<tr><td class="modelid">' + esc(m.model_id) + "</td><td>" + fieldDisplay(m.name) + "</td><td>" +
      tierBadge(m.tier) + "</td><td>" + ragBadge(m.rag_rating) + "</td><td>" + reviewBadge(m.review_status) +
      '</td><td class="rowact"><span class="edit-btn" data-rmmodel="' + esc(m.item_id) +
      '">remove</span></td></tr>').join("") :
      '<tr><td colspan="6" class="empty">No models in scope.</td></tr>';
    return "<table><thead><tr><th>Model ID</th><th>Name</th><th>Tier</th><th>RAG</th><th>Status</th><th></th></tr></thead><tbody>" +
      rows + "</tbody></table>" +
      '<div class="row" style="margin-top:8px"><div class="field"><label>Model ID</label>' +
      '<input id="mt-add-model" placeholder="MKM-SI-001"></div>' +
      '<button class="btn small" id="mt-add-model-btn">Add model…</button></div>';
  },

  _bindModels() {
    const self = this;
    const base = "/api/meetings/" + this._id + "/collections/models_in_scope";
    document.getElementById("mt-add-model-btn").onclick = function () {
      const mid = val("mt-add-model");
      if (!mid) { App.toast("Model ID is required", "error"); return; }
      App.amend("Add model " + mid + " to scope.", "POST", base, { fields: { model_id: mid } },
        () => self.show(self._id, "models_in_scope"));
    };
    document.querySelectorAll("[data-rmmodel]").forEach(function (el) {
      const iid = el.getAttribute("data-rmmodel");
      el.onclick = function () {
        App.amend("Remove " + iid + " from scope.", "POST", base + "/" + iid + "/delete", {},
          () => self.show(self._id, "models_in_scope"));
      };
    });
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
