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
// A meeting's own particulars, and editing them.
//
// Where and when it sits, who chairs it, what its quorum is -- the facts about the
// meeting itself rather than about anything on its agenda. Split from detail_core.js,
// which had grown just past the limit holding both.
//
// Assigns onto MeetingDetail; loads after detail_core.js.

Object.assign(MeetingDetail, {

  _info(d) {
    // mrc + org tier and chair are derived from the MRC binding, so they stay
    // read-only — they change by re-binding the meeting, not by typing here.
    // Date, time and location are the meeting's own logistics and do move: rooms
    // change and meetings get postponed, and a governance record that cannot
    // record that is a record people keep somewhere else. Status is the lifecycle
    // control (Scheduled → Completed). Every one of these goes through the same
    // confirm-to-amend path, so a rescheduling is on the audit trail.
    const readOnly = (label, key) => '<span class="datechip" id="minfo-' + key + '">' +
      '<span class="muted">' + label + ':</span> <b>' + fieldDisplay(d[key]) + "</b></span>";
    // A closed meeting is a finished record: the domain refuses to amend it, so
    // the console withdraws the edit affordance rather than offering an action
    // that can only fail.
    const closed = this._meeting.status === CLOSED_MEETING_STATUS;
    const editable = (label, key) => closed ? readOnly(label, key) :
      '<span class="datechip" id="minfo-' + key + '"><span class="muted">' +
      label + ':</span> <b>' + fieldDisplay(d[key]) + "</b> " +
      '<span class="edit-btn" data-minfo="' + key + '">edit</span></span>';
    return '<div class="dh-dates">' + readOnly("MRC", "mrc") + readOnly("Division", "division") +
      readOnly("Line of Business", "line_of_business") + readOnly("Chair", "chair") + "</div>" +
      '<div class="dh-dates">' + editable("Date", "date") + editable("Time", "time") +
      editable("Location", "location") + editable("Status", "status") + "</div>";
  },

  _bindInfo(d) {
    const self = this;
    document.getElementById("mt-back").onclick = function () {
      document.getElementById("mt-detail").innerHTML = ""; MRC.loadMeetings();
    };
    document.getElementById("mt-pdf").onclick = function () {
      window.open("/api/meetings/" + self._id + "/pack.pdf", "_blank");
    };
    const closeBtn = document.getElementById("mt-close");
    if (closeBtn && !closeBtn.disabled) {
      closeBtn.onclick = function () {
        App.amend("Close " + self._id + " — this generates and files the minutes.",
          "POST", "/api/meetings/" + self._id + "/close", {},
          () => self.show(self._id, self._tab));
      };
    }
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
      // A required field cannot be emptied — clearing the title would leave the
      // meeting headed by its bare id in every list, pack and minute.
      if (f.required && !input.value.trim()) {
        App.toast(f.label + " cannot be empty", "error");
        return;
      }
      App.amend("Set " + f.label + ' = "' + input.value + '" on ' + this._id + ".", "POST",
        "/api/meetings/" + this._id + "/field", { field: key, value: input.value.trim() },
        () => { this.show(this._id, this._tab); MRC.loadMeetings(); });
    };
  },
});
