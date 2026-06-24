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

const MRC = {
  _specs: null,

  async specs() {
    if (!this._specs) this._specs = await App.get("/api/meetings/fields");
    return this._specs;
  },

  specFieldByKey(key) {
    return this._specs.fields.find((f) => f.key === key);
  },

  async render() {
    const specs = await this.specs();
    const settings = await App.get("/api/mrc/settings");
    const el = document.getElementById("tab-mrc");
    el.innerHTML =
      this._headerCards(settings.fields) +
      this._scheduleCard(specs) +
      '<div id="mt-summary"></div>' +
      '<div class="card"><h3>Meetings</h3><div id="mt-list"></div></div>' +
      '<div id="mt-detail"></div>';
    document.getElementById("mt-schedule").onclick = () => this._schedule();
    await this.loadList();
  },

  _headerCards(f) {
    const card = (label, value, color) =>
      '<div class="scard" style="border-left-color:' + color + ';flex:1"><div class="lbl">' +
      label + '</div><div class="val" style="font-size:15px">' + fieldDisplay(value) + "</div></div>";
    return '<div class="summary" style="margin-bottom:14px">' +
      card("CHAIR", f.chair, "#1976d2") +
      card("FREQUENCY", f.frequency, "#f57c00") + "</div>";
  },

  _scheduleCard(specs) {
    let inputs =
      '<div class="field"><label>Meeting ID *</label><input id="sc-meeting_id" placeholder="MRC-2026-Q2"></div>';
    specs.fields.forEach(function (f) {
      if (f.key === "status") return; // status defaults at scheduling time
      const req = f.key === "title" || f.key === "date" ? " *" : "";
      inputs += '<div class="field"><label>' + esc(f.label) + req + "</label>" +
        inputControl("sc-" + f.key, f) + "</div>";
    });
    return '<div class="card"><h3>Schedule a meeting</h3><div class="row">' + inputs +
      '<button class="btn primary" id="mt-schedule">Schedule…</button></div></div>';
  },

  _schedule() {
    const id = val("sc-meeting_id"), title = val("sc-title"), date = val("sc-date");
    if (!id || !title || !date) {
      App.toast("Meeting ID, title and date are required", "error");
      return;
    }
    const fields = {};
    this._specs.fields.forEach(function (f) {
      if (f.key === "title" || f.key === "date" || f.key === "status") return;
      const v = val("sc-" + f.key);
      if (v !== "") fields[f.key] = v;
    });
    App.amend('Schedule meeting "' + id + '".', "POST", "/api/meetings",
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
    const meetings = await App.get("/api/meetings");
    document.getElementById("mt-summary").innerHTML = this._summary(meetings);
    const box = document.getElementById("mt-list");
    if (!meetings.length) {
      box.innerHTML = '<div class="empty">No meetings yet. Schedule one above.</div>';
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
      tr.title = "Double-click to open";
      tr.ondblclick = function () { MeetingDetail.show(tr.getAttribute("data-id")); };
    });
  },
};
