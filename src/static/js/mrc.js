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

// The MRC tab. There can be several MRC committees (set up under Admin > MRC);
// a selector picks one, and the page then shows that committee's chair/cadence,
// its Terms of Reference and its meetings — so meetings are scheduled per MRC.
const MRC = {
  _specs: null,
  _committees: [],
  _ref: {},         // reference data (mrc / division / line_of_business) for the org tree
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
    // The active committee follows the shared MRC-region bar (persisted across
    // the Models/Products/Audit tabs); the page always resolves to one.
    this._mrc = MrcNav.activeCommittee(this._committees, this._ref);
    const committee = this._committee();
    el.innerHTML =
      this._headerCards(committee) +
      this._torCard(committee) +
      this._scheduleCard(specs, committee) +
      '<div id="mt-summary"></div>' +
      '<div class="card"><h3>Meetings</h3><div id="mt-list"></div></div>' +
      '<div id="mt-detail"></div>';
    document.getElementById("mt-schedule").onclick = () => this._schedule();
    await this.loadList();
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
