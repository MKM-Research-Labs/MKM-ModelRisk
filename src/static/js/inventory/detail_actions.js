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

// Detail — the model's Actions tab. Actions are owned by the model; the MRC
// revisits and updates them. Each action carries a history of dated updates to
// its expected completion; the top-level target/status track the latest.
Object.assign(Detail, {
  _actionsTab(d) {
    const actions = d.actions || [];
    const cards = actions.length
      ? actions.map((a) => this._actionCard(a)).join("")
      : '<div class="empty">No actions yet.</div>';
    const add = this._model.retired ? "" :
      '<div class="section-header" style="margin-top:14px">Add action</div>' +
      '<div class="row" style="flex-wrap:wrap;align-items:flex-end">' +
      '<div class="field"><label>Action *</label><input id="act-desc"></div>' +
      '<div class="field"><label>Owner</label><input id="act-owner"></div>' +
      '<div class="field"><label>Target date</label><input type="date" id="act-target"></div>' +
      '<button class="btn small primary" id="act-add">Add&hellip;</button></div>';
    return '<p class="muted">Outstanding actions for this model. The MRC revisits and updates them; ' +
      "each carries a history of changes to its expected completion.</p>" +
      '<div id="actions-list">' + cards + "</div>" + add;
  },

  // One action with its expandable update history and an inline Add-update form.
  _actionCard(a) {
    const retired = this._model.retired;
    const updates = a.updates || [];
    const hist = updates.length
      ? updates.map((u) => '<div class="prow"><div style="font-size:12px">' +
          (u.date ? '<span class="code">' + esc(u.date) + "</span> " : "") + esc(u.note || "") +
          (u.target_date ? ' <span class="muted">→ target ' + esc(u.target_date) + "</span>" : "") +
          "</div>" + statusBadge(u.status) + "</div>").join("")
      : '<div class="muted" style="font-size:11px">No updates yet.</div>';
    const addUpd = retired ? "" :
      '<div class="row" style="margin-top:6px;flex-wrap:wrap;align-items:flex-end">' +
      '<div class="field"><label>Update note</label><input id="upd-note-' + esc(a.item_id) + '"></div>' +
      '<div class="field"><label>Revised target</label><input type="date" id="upd-target-' + esc(a.item_id) + '"></div>' +
      '<div class="field"><label>Status</label><select id="upd-status-' + esc(a.item_id) + '">' +
      ["Open", "Closed"].map((s) => "<option" + (s === a.status ? " selected" : "") + ">" + s + "</option>").join("") +
      '</select></div><button class="btn small" data-act-update="' + esc(a.item_id) + '">Add update</button></div>';
    return '<div class="card" style="margin-bottom:8px">' +
      '<div class="row" style="justify-content:space-between;align-items:flex-start">' +
      "<div><b>" + esc(a.description) + "</b>" +
      '<div class="muted" style="font-size:11px;margin-top:2px">' +
      (a.owner ? "Owner: " + esc(a.owner) + " &nbsp;·&nbsp; " : "") +
      "Target: " + fieldDisplay(a.target_date) + "</div></div>" +
      '<div class="rowact">' + statusBadge(a.status) +
      (retired ? "" : ' <button class="btn small danger" data-act-rm="' + esc(a.item_id) + '">Remove</button>') +
      "</div></div>" +
      '<div class="section-header" style="margin-top:8px;font-size:11px">Update history</div>' + hist + addUpd +
      "</div>";
  },

  _bindActions() {
    const self = this;
    const d = this._model.data || {};
    const base = "/api/models/" + this._id + "/collections/actions";
    const today = new Date().toISOString().slice(0, 10);
    const addBtn = document.getElementById("act-add");
    if (addBtn) addBtn.onclick = function () {
      const desc = val("act-desc");
      if (!desc) { App.toast("Action description is required", "error"); return; }
      const target = val("act-target");
      const fields = { description: desc, status: "Open",
        updates: [{ date: today, note: "Raised", target_date: target || "", status: "Open" }] };
      const owner = val("act-owner"); if (owner) fields.owner = owner;
      if (target) fields.target_date = target;
      App.amend("Add action for " + self._id + ".", "POST", base, { fields: fields },
        () => self.show(self._id, "actions"));
    };
    document.querySelectorAll("[data-act-update]").forEach(function (btn) {
      const id = btn.getAttribute("data-act-update");
      btn.onclick = function () {
        const action = (d.actions || []).find((a) => a.item_id === id) || {};
        const note = (document.getElementById("upd-note-" + id) || {}).value;
        const target = (document.getElementById("upd-target-" + id) || {}).value;
        const status = (document.getElementById("upd-status-" + id) || {}).value;
        const updates = (action.updates || []).concat(
          [{ date: today, note: note, target_date: target, status: status }]);
        const fields = { updates: updates, status: status };
        if (target) fields.target_date = target;
        App.amend("Add update to action " + id + ".", "POST", base + "/" + id, { fields: fields },
          () => self.show(self._id, "actions"));
      };
    });
    document.querySelectorAll("[data-act-rm]").forEach(function (btn) {
      const id = btn.getAttribute("data-act-rm");
      btn.onclick = () => App.amend("Remove action " + id + ".", "POST", base + "/" + id + "/delete", {},
        () => self.show(self._id, "actions"));
    });
  },
});
