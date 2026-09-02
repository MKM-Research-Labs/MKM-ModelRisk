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

// The MRC tab. Committees are set up under Admin > MRC and attach to the org tree
// at Company, Division or Line of Business level. The tab opens on a LIST of the
// committees the region navigator's current selection covers — as the Models and
// Products tabs do — and opening one shows that committee's chair/cadence, its
// Terms of Reference and its meetings, so meetings are scheduled per MRC.
const MRC = {
  _specs: null,
  _committees: [],
  _ref: {},         // reference data (mrc / division / line_of_business) for the org tree
  _mrc: null,       // the open committee's id (value); null while the list is showing
  _meetings: [],    // every meeting, for the list's per-committee counts

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

  // --- the committee list ---

  async render() {
    await this.specs();
    // Archived committees are retained for history but never offered for
    // scheduling new meetings — filter them out. Reference data is shared/cached
    // via MrcNav so switching tabs doesn't re-fetch it.
    const nav = await MrcNav.load();
    this._ref = nav.ref;
    this._committees = nav.committees;
    const el = document.getElementById("tab-mrc");
    if (!this._committees.length) {
      el.innerHTML = '<div class="card"><div class="empty">No MRC committees yet. ' +
        "Create one under Admin &rarr; MRC, then schedule meetings against it.</div></div>";
      return;
    }
    this._meetings = await App.get("/api/meetings");
    this._mrc = null;
    const scoped = this._committees.filter((c) => this._committeeInScope(c));
    el.innerHTML =
      '<div id="mrc-list">' + this._listSummary(scoped) + this._listTable(scoped) + "</div>" +
      '<div id="mrc-detail"></div>';
    const self = this;
    el.querySelectorAll("#mrc-list tr.clickable").forEach(function (tr) {
      tr.title = "Open committee";
      tr.onclick = function () { self.showCommittee(tr.getAttribute("data-mrc")); };
    });
  },

  // Which committees the current region selection covers. A committee is not a
  // rung of the org tree, so this reads its own scope against the selection:
  // Company-level committees govern everything and are always listed; a
  // Division-level one shows for its division (an unscoped one shows anywhere,
  // since it names no division to be excluded by); a Line of Business-level one
  // shows for its line of business, and also for that line's parent division
  // when only the division is selected.
  _committeeInScope(c) {
    const s = MrcNav.state || {};
    if (!s.div) return true;                            // "All"
    if (!c || c.level === "Company") return true;
    if (c.level === "Division") return !c.scope_value || c.scope_value === s.div;
    if (c.level === "Line of Business") {
      if (s.lob) return c.scope_value === s.lob;
      const lob = (this._ref.line_of_business || []).find((l) => l.value === c.scope_value);
      return !!lob && lob.division === s.div;
    }
    return true;
  },

  _meetingsFor(value) {
    return this._meetings.filter((m) => (m.data || {}).mrc === value);
  },

  _listSummary(scoped) {
    const ids = {};
    scoped.forEach((c) => { ids[c.value] = true; });
    const meetings = this._meetings.filter((m) => ids[(m.data || {}).mrc]);
    const c = (s) => meetings.filter((m) => m.status === s).length;
    const card = (lbl, v, color) =>
      '<div class="scard" style="border-left-color:' + color + '"><div class="lbl">' +
      lbl + '</div><div class="val">' + v + "</div></div>";
    return '<div class="summary">' +
      card("Committees", scoped.length, Theme.value("accent")) +
      card("Meetings", meetings.length, Theme.value("accent")) +
      card("Scheduled", c("Scheduled"), Theme.value("accent")) +
      card("Completed", c("Completed"), Theme.value("green")) + "</div>";
  },

  _listTable(scoped) {
    if (!scoped.length) {
      return '<div class="card"><div class="empty">No MRC committees cover this scope. ' +
        "Pick another region above, or create one under Admin &rarr; MRC.</div></div>";
    }
    const self = this;
    let rows = "";
    scoped.forEach(function (c) {
      const meetings = self._meetingsFor(c.value);
      rows += '<tr class="clickable" data-mrc="' + esc(c.value) + '">' +
        '<td class="modelid">' + esc(c.value) + "</td>" +
        "<td>" + fieldDisplay(c.name) + "</td>" +
        "<td>" + fieldDisplay(c.level) + "</td>" +
        "<td>" + fieldDisplay(c.scope_value) + "</td>" +
        "<td>" + fieldDisplay(c.chair) + "</td>" +
        "<td>" + fieldDisplay(c.frequency) + "</td>" +
        '<td class="num">' + meetings.length + "</td>" +
        '<td class="num">' +
        meetings.filter((m) => m.status === "Scheduled").length + "</td></tr>";
    });
    return '<div class="card"><h3>Model Risk Committees</h3>' +
      "<table><thead><tr><th>MRC</th><th>Name</th><th>Level</th><th>Scope</th>" +
      "<th>Chair</th><th>Frequency</th><th>Meetings</th><th>Scheduled</th>" +
      "</tr></thead><tbody>" + rows + "</tbody></table></div>";
  },

  // --- one committee ---

  // Render `value`'s detail in place of the list. Returns false when the id names
  // no live committee, so a caller with more to draw knows to stop.
  async showCommittee(value) {
    this._mrc = value;
    const committee = this._committee();
    if (!committee) { this._mrc = null; return false; }
    const list = document.getElementById("mrc-list");
    if (list) list.style.display = "none";
    document.getElementById("mrc-detail").innerHTML =
      '<div style="margin-bottom:var(--space-6)">' +
      '<button class="btn small" id="mrc-back">&larr; Back to committees</button></div>' +
      this._headerCards(committee) +
      this._torCard(committee) +
      this._scheduleCard(this._specs, committee) +
      '<div id="mt-summary"></div>' +
      '<div class="card"><h3>Meetings</h3><div id="mt-list"></div></div>' +
      '<div id="mt-detail"></div>';
    document.getElementById("mrc-back").onclick = () => this.render();
    document.getElementById("mt-schedule").onclick = () => this._schedule();
    await this.loadMeetings();
    return true;
  },

  // A deep link (#mrc/<meeting-id>) lands on the list, where the meeting detail
  // has nowhere to render — open the committee that owns the meeting first.
  async openMeeting(meetingId) {
    if (!this._committees.length) return;
    const m = this._meetings.find((x) => x.meeting_id === meetingId);
    const value = (m && (m.data || {}).mrc) ||
      MrcNav.activeCommittee(this._committees, this._ref);
    if (await this.showCommittee(value)) await MeetingDetail.show(meetingId);
  },

  _headerCards(c) {
    const card = (label, value, color) =>
      '<div class="scard" style="border-left-color:' + color + ';flex:1"><div class="lbl">' +
      label + '</div><div class="val" style="font-size:15px">' + fieldDisplay(value) + "</div></div>";
    return '<div class="summary" style="margin-bottom:var(--space-7)">' +
      card("MRC", (c.name || c.value) + " · " + fieldDisplay(c.level) +
        (c.scope_value ? " (" + esc(c.scope_value) + ")" : ""), Theme.value("accent")) +
      card("CHAIR", c.chair, Theme.value("accent")) +
      card("FREQUENCY", c.frequency, Theme.value("amber")) + "</div>";
  },

  _torCard(c) {
    if (!c.tor_filename) return "";
    return '<div class="card" style="display:flex;align-items:center;gap:var(--space-6)">' +
      "<span><b>Terms of Reference:</b> " +
      '<a href="/api/reference/collections/mrc/' + esc(c.item_id) + '/tor" target="_blank">&darr; ' +
      esc(c.tor_original_name || "Terms of Reference") + "</a></span></div>";
  },

  _scheduleCard(specs, committee) {
    let inputs =
      '<div class="field"><label>Meeting ID *</label><input id="sc-meeting_id" placeholder="MRC-2026-Q3"></div>';
    specs.fields.forEach(function (f) {
      // The MRC is fixed to the selected committee; status defaults on schedule.
      // Hidden fields (lifecycle flags/artefacts) are set by workflow, not here.
      if (f.key === "status" || f.key === "mrc" || f.hidden) return;
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
      if (f.key === "title" || f.key === "date" || f.key === "status" || f.key === "mrc" || f.hidden) return;
      const v = val("sc-" + f.key);
      if (v !== "") fields[f.key] = v;
    });
    const mrc = this._mrc;
    App.amend('Schedule meeting "' + id + '" for ' + mrc + ".", "POST", "/api/meetings",
      { meeting_id: id, title: title, date: date, fields: fields },
      () => this.render().then(() => this.showCommittee(mrc)));
  },

  _meetingSummary(meetings) {
    const c = (s) => meetings.filter((m) => m.status === s).length;
    const card = (lbl, v, color) =>
      '<div class="scard" style="border-left-color:' + color + '"><div class="lbl">' +
      lbl + '</div><div class="val">' + v + "</div></div>";
    return '<div class="summary">' +
      card("Total", meetings.length, Theme.value("accent")) +
      card("Scheduled", c("Scheduled"), Theme.value("accent")) +
      card("Completed", c("Completed"), Theme.value("green")) + "</div>";
  },

  async loadMeetings() {
    const all = await App.get("/api/meetings");
    this._meetings = all;
    const meetings = all.filter((m) => (m.data || {}).mrc === this._mrc);
    document.getElementById("mt-summary").innerHTML = this._meetingSummary(meetings);
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
