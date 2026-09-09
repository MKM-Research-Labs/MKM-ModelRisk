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

// A committee's meetings: the form that schedules one, and the list of the ones it
// has held.
//
// Split from mrc.js, which is about the committees themselves — which of them the
// selected region covers, and what one is (its chair, its cadence, its Terms of
// Reference). This is what the committee does, which is a different question and the
// only part of the tab that writes.
//
// A meeting is scheduled INTO the open committee: the form never offers an MRC field,
// because the committee is the screen you are on, and the rest of the meeting's org
// scope is derived from it rather than re-entered. Opening a row hands over to
// MeetingDetail — one meeting is its own screen.
//
// Assigns onto MRC; loads after mrc.js.

Object.assign(MRC, {

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
});
