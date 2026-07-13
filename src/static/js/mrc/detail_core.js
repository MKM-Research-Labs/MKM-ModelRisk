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

// Tabbed MRC meeting detail (the MeetingDetail package). This core module owns
// the shell: state, the render loop, the header/info bar, tab routing, and the
// info-bar field editor. The participants/quorum, minutes, agenda, sign-off and
// models sections augment MeetingDetail from their own modules (loaded after).

// Sensible default for a sign-off's next review date: one year out. The
// committee can still change it before signing off.
function oneYearAhead() {
  const d = new Date();
  d.setFullYear(d.getFullYear() + 1);
  return d.toISOString().slice(0, 10);
}

const MeetingDetail = {
  _id: null, _meeting: null, _specs: null, _models: [], _inventory: [], _products: [],
  _tab: "agenda", _showAll: false,

  async show(meetingId, tab) {
    this._id = meetingId;
    this._specs = await MRC.specs();
    this._meeting = await App.get("/api/meetings/" + meetingId);
    this._models = await App.get("/api/meetings/" + meetingId + "/models");
    this._inventory = await App.get("/api/models");
    this._products = await App.get("/api/products");
    this._people = (await App.get("/api/reference")).data.people || [];
    if (tab) this._tab = tab;
    this._render();
    document.getElementById("mt-detail").scrollIntoView({ block: "start" });
  },

  collSpec(key) { return this._specs.collections.find((c) => c.key === key); },

  _render() {
    const m = this._meeting, d = m.data || {};
    // Participants live in a persistent left panel (with the live quorum badge)
    // beside the tabbed content. A meeting that is not quorate cannot proceed:
    // a banner shows, and the forward-moving actions are disabled below.
    const q = this._quorum(d);
    const banner = q.met ? "" :
      '<div class="quorum-banner">Quorum not met — this meeting cannot proceed until it is quorate' +
      (q.missing.length ? " (needs " + esc(q.missing.join(", ")) + ")" : "") + ".</div>";
    document.getElementById("mt-detail").innerHTML =
      '<div class="card">' + this._header(m, d) + this._info(d) +
      '<div class="mtd-cols">' + this._participantsPanel(d) +
      '<div class="mtd-main">' + banner + this._tabbar(d) +
      '<div id="mtd-content"></div></div></div></div>';
    document.querySelectorAll("[data-mtab]").forEach((b) => {
      b.onclick = () => { this._tab = b.getAttribute("data-mtab"); this._render(); };
    });
    this._bindInfo(d);
    this._bindParticipantsPanel(d);
    this._renderContent();
    if (!q.met) this._applyQuorumLock();
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
    // date/time/location are fixed at scheduling — all shown read-only. Only
    // Status stays editable: it's the meeting's lifecycle control (Scheduled →
    // Held/Completed), and nothing else in the UI moves it.
    const readOnly = (label, key) => '<span class="datechip" id="minfo-' + key + '">' +
      '<span class="muted">' + label + ':</span> <b>' + fieldDisplay(d[key]) + "</b></span>";
    const editable = (label, key) => '<span class="datechip" id="minfo-' + key + '"><span class="muted">' +
      label + ':</span> <b>' + fieldDisplay(d[key]) + "</b> " +
      '<span class="edit-btn" data-minfo="' + key + '">edit</span></span>';
    return '<div class="dh-dates">' + readOnly("MRC", "mrc") + readOnly("Division", "division") +
      readOnly("Department", "department") + readOnly("Chair", "chair") + "</div>" +
      '<div class="dh-dates">' + readOnly("Date", "date") + readOnly("Time", "time") +
      readOnly("Location", "location") + editable("Status", "status") + "</div>";
  },

  _tabbar(d) {
    // The agenda badge counts only what the tab shows — sign-off items render in
    // the Models tab, so they don't inflate the agenda count.
    const n = (k) => {
      const arr = d[k] || [];
      if (k === "agenda") return arr.filter((a) => !(a.subject_model_id || a.subject_product_id)).length;
      return arr.length;
    };
    // Participants moved out to the persistent left panel — no longer a tab.
    const tabs = [
      ["agenda", "Agenda"], ["models_in_scope", "Models"], ["actions", "Actions"],
      ["minutes", "Minutes"],
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
    // Minutes has a bespoke form: presenter from the participants, a related
    // model/product picker, and an expandable text box.
    if (this._tab === "minutes") { box.innerHTML = this._minutesContent(); this._bindMinutes(); return; }
    const spec = this.collSpec(this._tab);
    // Decisions / actions accept multiple new entries at once; participants and
    // minutes have their own bespoke tabs.
    const bulk = ["decisions", "actions"].indexOf(this._tab) >= 0;
    box.innerHTML = Collections.render(d, { collections: [spec] }, false, bulk);
    Collections.bind("/api/meetings/" + this._id + "/collections/", { collections: [spec] },
      false, () => this.show(this._id, this._tab), d, bulk);
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
