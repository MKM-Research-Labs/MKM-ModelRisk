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

// The MRC tab. There can be several MRC committees (set up under Admin > MRC);
// a selector picks one, and the page then shows that committee's chair/cadence,
// its Terms of Reference and its meetings — so meetings are scheduled per MRC.
const MRC = {
  _specs: null,
  _committees: [],
  _ref: {},         // reference data (mrc / division / department) for the org tree
  _mrc: null,       // the selected committee's id (value), survives re-renders

  async specs() {
    // Always re-fetch: field options (incl. references) track the admin lists.
    this._specs = await App.get("/api/meetings/fields");
    return this._specs;
  },

  specFieldByKey(key) {
    return this._specs.fields.find((f) => f.key === key);
  },

  _committee() {
    return this._committees.find((c) => c.value === this._mrc) || null;
  },

  async render() {
    const specs = await this.specs();
    // Archived committees are retained for history but never offered for
    // scheduling new meetings — filter them out of the selector. Reference data
    // is shared/cached via MrcNav so switching tabs doesn't re-fetch it.
    const nav = await MrcNav.load();
    this._ref = nav.ref;
    this._committees = nav.committees;
    const el = document.getElementById("tab-mrc");
    if (!this._committees.length) {
      el.innerHTML = '<div class="card"><div class="empty">No MRC committees yet. ' +
        "Create one under Admin &rarr; MRC, then schedule meetings against it.</div></div>";
      return;
    }
    // The active committee follows the shared MRC-region selection (persisted
    // across the Models/Products/Audit tabs); the page always resolves to one.
    this._mrc = MrcNav.activeCommittee(this._committees, this._ref);
    const committee = this._committee();
    el.innerHTML =
      this._selector() +
      this._headerCards(committee) +
      this._torCard(committee) +
      this._scheduleCard(specs, committee) +
      '<div id="mt-summary"></div>' +
      '<div class="card"><h3>Meetings</h3><div id="mt-list"></div></div>' +
      '<div id="mt-detail"></div>';
    // Picking a division jumps to its first committee; selections update the
    // shared MRC-region state so the choice carries to the other tabs.
    el.querySelectorAll("[data-div]").forEach((btn) => {
      btn.onclick = () => {
        const group = MrcNav.groups(this._committees, this._ref)[btn.getAttribute("data-div")] || [];
        if (group.length) {
          MrcNav.selectCommittee(this._committees, this._ref, group[0].value);
          this.render();
        }
      };
    });
    el.querySelectorAll("[data-mrc]").forEach((btn) => {
      btn.onclick = () => {
        MrcNav.selectCommittee(this._committees, this._ref, btn.getAttribute("data-mrc"));
        this.render();
      };
    });
    document.getElementById("mt-schedule").onclick = () => this._schedule();
    await this.loadList();
  },

  // Two-tier selector: divisions on top; the active division's committees below.
  // Division grouping is shared with the Models/Products pages via MrcNav; here a
  // committee is always selected (the page needs one to show its cards/schedule).
  _selector() {
    const groups = MrcNav.groups(this._committees, this._ref);
    const activeDiv = MrcNav.divisionOf(this._committee(), this._ref);
    const divTabs = MrcNav.orderedDivisions(groups, this._ref).map((dv) =>
      '<button class="dtab' + (dv === activeDiv ? " active" : "") + '" data-div="' + esc(dv) +
      '">' + esc(dv) + "</button>").join("");
    const committeeTabs = (groups[activeDiv] || []).map((c) =>
      '<button class="dtab' + (c.value === this._mrc ? " active" : "") + '" data-mrc="' + esc(c.value) +
      '">' + esc(c.name || c.value) + "</button>").join("");
    return '<div class="card" style="padding:8px 12px;margin-bottom:12px">' +
      '<div class="dtabs">' + divTabs + "</div>" +
      '<div class="dtabs" style="margin-top:8px;border-top:1px solid var(--line);padding-top:8px">' +
      committeeTabs + "</div></div>";
  },

  _headerCards(c) {
    const card = (label, value, color) =>
      '<div class="scard" style="border-left-color:' + color + ';flex:1"><div class="lbl">' +
      label + '</div><div class="val" style="font-size:15px">' + fieldDisplay(value) + "</div></div>";
    return '<div class="summary" style="margin-bottom:14px">' +
      card("MRC", (c.name || c.value) + " · " + fieldDisplay(c.level) +
        (c.scope_value ? " (" + esc(c.scope_value) + ")" : ""), "#1976d2") +
      card("CHAIR", c.chair, "#1976d2") +
      card("FREQUENCY", c.frequency, "#f57c00") + "</div>";
  },

  _torCard(c) {
    if (!c.tor_filename) return "";
    return '<div class="card" style="display:flex;align-items:center;gap:12px">' +
      "<span><b>Terms of Reference:</b> " +
      '<a href="/api/reference/collections/mrc/' + esc(c.item_id) + '/tor" target="_blank">&darr; ' +
      esc(c.tor_original_name || "Terms of Reference") + "</a></span></div>";
  },

  _scheduleCard(specs, committee) {
    let inputs =
      '<div class="field"><label>Meeting ID *</label><input id="sc-meeting_id" placeholder="MRC-2026-Q3"></div>';
    specs.fields.forEach(function (f) {
      // The MRC is fixed to the selected committee; status defaults on schedule.
      if (f.key === "status" || f.key === "mrc") return;
      const req = f.key === "title" || f.key === "date" ? " *" : "";
      inputs += '<div class="field"><label>' + esc(f.label) + req + "</label>" +
        inputControl("sc-" + f.key, f) + "</div>";
    });
    return '<div class="card"><h3>Schedule a meeting for ' + esc(committee.name || committee.value) +
      "</h3><div class=\"row\">" + inputs +
      '<button class="btn primary" id="mt-schedule">Schedule…</button></div></div>';
  },

  _schedule() {
    const id = val("sc-meeting_id"), title = val("sc-title"), date = val("sc-date");
    if (!id || !title || !date) {
      App.toast("Meeting ID, title and date are required", "error");
      return;
    }
    // Allocate the meeting to the selected committee; the rest of its org scope
    // and chair are derived from that MRC.
    const fields = { mrc: this._mrc };
    this._specs.fields.forEach(function (f) {
      if (f.key === "title" || f.key === "date" || f.key === "status" || f.key === "mrc") return;
      const v = val("sc-" + f.key);
      if (v !== "") fields[f.key] = v;
    });
    App.amend('Schedule meeting "' + id + '" for ' + this._mrc + ".", "POST", "/api/meetings",
      { meeting_id: id, title: title, date: date, fields: fields }, () => this.render());
  },

  _summary(meetings) {
    const c = (s) => meetings.filter((m) => m.status === s).length;
    const card = (lbl, v, color) =>
      '<div class="scard" style="border-left-color:' + color + '"><div class="lbl">' +
      lbl + '</div><div class="val">' + v + "</div></div>";
    return '<div class="summary">' +
      card("Total", meetings.length, "#1976d2") +
      card("Scheduled", c("Scheduled"), "#1976d2") +
      card("Completed", c("Completed"), "#388e3c") + "</div>";
  },

  async loadList() {
    const all = await App.get("/api/meetings");
    const meetings = all.filter((m) => (m.data || {}).mrc === this._mrc);
    document.getElementById("mt-summary").innerHTML = this._summary(meetings);
    const box = document.getElementById("mt-list");
    if (!meetings.length) {
      box.innerHTML = '<div class="empty">No meetings for this MRC yet. Schedule one above.</div>';
      return;
    }
    let rows = "";
    meetings.forEach(function (m) {
      const d = m.data || {};
      const n = (k) => (d[k] || []).length;
      rows += '<tr class="clickable" data-id="' + esc(m.meeting_id) + '">' +
        '<td class="modelid">' + esc(m.meeting_id) + "</td>" +
        "<td>" + fieldDisplay(d.title) + "</td>" +
        "<td>" + fieldDisplay(d.date) + "</td>" +
        "<td>" + statusBadge(m.status) + "</td>" +
        '<td class="num">' + n("models_in_scope") + '</td><td class="num">' + n("agenda") + "</td>" +
        '<td class="num">' + n("minutes") + '</td><td class="num">' + n("documents") + "</td></tr>";
    });
    box.innerHTML =
      "<table><thead><tr><th>ID</th><th>Title</th><th>Date</th><th>Status</th>" +
      "<th>Models</th><th>Agenda</th><th>Minutes</th><th>Docs</th></tr></thead><tbody>" +
      rows + "</tbody></table>";
    box.querySelectorAll("tr.clickable").forEach(function (tr) {
      tr.title = "Open meeting";
      tr.onclick = function () { MeetingDetail.show(tr.getAttribute("data-id")); };
    });
  },
};
