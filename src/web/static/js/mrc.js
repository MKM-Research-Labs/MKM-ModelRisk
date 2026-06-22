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

const ACTION_STATUSES = ["Open", "In Progress", "Closed"];

const MRC = {
  async render() {
    const el = document.getElementById("tab-mrc");
    el.innerHTML =
      '<div class="card"><h3>Schedule a meeting</h3><div class="row">' +
      '<div class="field"><label>Meeting ID</label><input id="mt-id" placeholder="MRC-2026-Q2"></div>' +
      '<div class="field"><label>Title</label><input id="mt-title" placeholder="Q2 Model Risk Committee"></div>' +
      '<div class="field"><label>Date</label><input id="mt-date" placeholder="2026-06-30"></div>' +
      '<button class="btn primary" id="mt-schedule">Schedule…</button>' +
      "</div></div>" +
      '<div class="card"><h3>Meetings</h3><div id="mt-list"></div></div>' +
      '<div id="mt-detail"></div>';
    document.getElementById("mt-schedule").onclick = () => this._schedule();
    await this._loadList();
  },

  async _loadList() {
    const meetings = await App.get("/api/meetings");
    const box = document.getElementById("mt-list");
    if (!meetings.length) {
      box.innerHTML = '<div class="empty">No meetings yet. Schedule one above.</div>';
      return;
    }
    let rows = "";
    meetings.forEach(function (m) {
      const d = m.data || {};
      rows +=
        '<tr class="clickable" data-id="' + esc(m.meeting_id) + '">' +
        "<td>" + esc(m.meeting_id) + "</td><td>" + esc(d.title || "") + "</td>" +
        "<td>" + esc(d.date || "") + "</td><td>" + esc(m.status || "—") + "</td></tr>";
    });
    box.innerHTML =
      "<table><thead><tr><th>ID</th><th>Title</th><th>Date</th><th>Status</th></tr></thead><tbody>" +
      rows + "</tbody></table>";
    const self = this;
    box.querySelectorAll("tr.clickable").forEach(function (tr) {
      tr.onclick = function () { self._detail(tr.getAttribute("data-id")); };
    });
  },

  _schedule() {
    const id = val("mt-id"), title = val("mt-title"), date = val("mt-date");
    if (!id || !title || !date) { App.toast("Meeting ID, title and date are required", "error"); return; }
    App.amend('Schedule meeting "' + id + '".', "POST", "/api/meetings",
      { meeting_id: id, title: title, date: date }, () => this.render());
  },

  _list(items, render) {
    if (!items || !items.length) return '<div class="empty">None.</div>';
    return items.map(render).join("");
  },

  async _detail(id) {
    const m = await App.get("/api/meetings/" + id);
    const d = m.data || {};
    const agenda = this._list(d.agenda, function (a) {
      return "<tr><td>" + esc(a.item_id) + "</td><td>" + esc(a.title) +
        "</td><td>" + esc(a.presenter || "—") + "</td></tr>";
    });
    const decisions = this._list(d.decisions, function (x) {
      return "<tr><td>" + esc(x.decision_id) + "</td><td>" + esc(x.text) + "</td></tr>";
    });
    const self = this;
    const actions = (d.actions || []).map(function (a) {
      let opts = "";
      ACTION_STATUSES.forEach(function (s) {
        opts += '<option' + (s === a.status ? " selected" : "") + ">" + s + "</option>";
      });
      return "<tr><td>" + esc(a.action_id) + "</td><td>" + esc(a.description) +
        "</td><td>" + esc(a.owner) + '</td><td><select data-action="' + esc(a.action_id) +
        '">' + opts + "</select></td></tr>";
    }).join("") || '<tr><td colspan="4" class="empty">None.</td></tr>';

    document.getElementById("mt-detail").innerHTML =
      '<div class="card"><h3>' + esc(id) + " — " + esc(d.title || "") + "</h3>" +
      '<div class="kv"><div class="k">Date</div><div>' + esc(d.date || "") +
      '</div><div class="k">Status</div><div>' + esc(m.status || "") + "</div></div>" +
      this._statusRow(id) +
      '<div class="subhead">Agenda</div><table><tbody>' + agenda + "</tbody></table>" +
      '<div class="row" style="margin-top:8px"><input id="ag-title" placeholder="Agenda item title">' +
      '<input id="ag-presenter" placeholder="Presenter (optional)">' +
      '<button class="btn small" id="ag-add">Add item…</button></div>' +
      '<div class="subhead">Decisions</div><table><tbody>' + decisions + "</tbody></table>" +
      '<div class="row" style="margin-top:8px"><input id="dec-text" placeholder="Decision text" style="flex:1">' +
      '<button class="btn small" id="dec-add">Log decision…</button></div>' +
      '<div class="subhead">Actions</div><table><thead><tr><th>ID</th><th>Description</th><th>Owner</th><th>Status</th></tr></thead><tbody>' +
      actions + "</tbody></table>" +
      '<div class="row" style="margin-top:8px"><input id="act-desc" placeholder="Action description">' +
      '<input id="act-owner" placeholder="Owner"><button class="btn small" id="act-add">Raise action…</button></div></div>';

    this._bindDetail(id, self);
  },

  _statusRow(id) {
    return '<div class="row"><div class="field"><label>Set meeting status</label>' +
      '<select id="mt-status"><option>Scheduled</option><option>In Progress</option>' +
      "<option>Held</option><option>Cancelled</option></select></div>" +
      '<button class="btn small" id="mt-status-apply">Update…</button></div>';
  },

  _bindDetail(id, self) {
    document.getElementById("mt-status-apply").onclick = function () {
      App.amend("Set status of " + id + ' to "' + val("mt-status") + '".', "POST",
        "/api/meetings/" + id + "/field", { field: "status", value: val("mt-status") },
        function () { self._detail(id); self._loadList(); });
    };
    document.getElementById("ag-add").onclick = function () {
      App.amend("Add agenda item to " + id + ".", "POST", "/api/meetings/" + id + "/agenda",
        { title: val("ag-title"), presenter: val("ag-presenter") || null },
        function () { self._detail(id); });
    };
    document.getElementById("dec-add").onclick = function () {
      App.amend("Log a decision for " + id + ".", "POST", "/api/meetings/" + id + "/decisions",
        { text: val("dec-text") }, function () { self._detail(id); });
    };
    document.getElementById("act-add").onclick = function () {
      App.amend("Raise an action for " + id + ".", "POST", "/api/meetings/" + id + "/actions",
        { description: val("act-desc"), owner: val("act-owner") },
        function () { self._detail(id); });
    };
    document.querySelectorAll("select[data-action]").forEach(function (sel) {
      sel.onchange = function () {
        const aid = sel.getAttribute("data-action");
        App.amend("Set " + aid + ' to "' + sel.value + '" on ' + id + ".", "POST",
          "/api/meetings/" + id + "/actions/" + aid + "/status", { status: sel.value },
          function () { self._detail(id); });
      };
    });
  },
};
