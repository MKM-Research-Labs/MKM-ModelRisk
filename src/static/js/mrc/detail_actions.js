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

// MeetingDetail — the meeting's Actions tab. An agreed action starts from the model
// it concerns, because that is what the owner tick-boxes default from; an action may
// be owned by several people; and progress is recorded as dated updates rather than a
// target date, the same shape a product-owned action already uses.

// The date an update is stamped with. Local midnight, ISO — what every other dated
// entry on a meeting records.
function actionUpdateDate() {
  return new Date().toISOString().slice(0, 10);
}

Object.assign(MeetingDetail, {
  _actionsLocked() { return this._meeting.status === CLOSED_MEETING_STATUS; },

  _actionField(key) {
    const spec = this.collSpec("actions") || {};
    return (spec.fields || []).find((f) => f.key === key) || {};
  },

  // Owners as a list, tolerating what is already on record: an action minuted before
  // an action could have more than one owner holds a bare string.
  _actionOwners(action) {
    const owner = (action || {}).owner;
    if (!owner) return [];
    return Array.isArray(owner) ? owner : [owner];
  },

  // The registered owner of a model — what the tick-boxes start on once a model is picked.
  _modelOwner(modelId) {
    const model = (this._inventory || []).find((m) => m.model_id === modelId);
    return model ? (model.data || {}).owner || "" : "";
  },

  // Models in scope for this meeting first, then the rest of the inventory. An action
  // usually concerns something the committee is sitting on, but not always.
  _actionModelSelect(id, selected) {
    const inScope = (this._models || []).map((m) => m.model_id).filter(Boolean);
    const self = this;
    const option = function (modelId) {
      const name = self._subjectName(modelId);
      return '<option value="' + esc(modelId) + '"' +
        (modelId === selected ? " selected" : "") + ">" +
        esc(modelId + (name ? " — " + name : "")) + "</option>";
    };
    const others = (this._actionField("model_id").options || [])
      .filter((m) => inScope.indexOf(m) < 0);
    const group = (label, ids) => (ids.length
      ? '<optgroup label="' + esc(label) + '">' + ids.map(option).join("") + "</optgroup>" : "");
    return '<select id="' + id + '"><option value=""></option>' +
      group("In scope for this meeting", inScope) +
      group("Other registered models", others) + "</select>";
  },

  // Tick-boxes rather than a multi-select: the committee should be able to see every
  // candidate owner at once and tick several without a modifier key.
  _ownerBoxes(group, ticked) {
    const people = this._actionField("owner").options || [];
    if (!people.length) {
      return '<span class="muted" style="font-size:11px">No people in the directory — ' +
        "add them under Admin &rarr; People.</span>";
    }
    return people.map((person) =>
      '<label class="tickbox"><input type="checkbox" data-owner="' + esc(group) + '" value="' +
      esc(person) + '"' + (ticked.indexOf(person) >= 0 ? " checked" : "") + ">" +
      esc(person) + "</label>").join("");
  },

  _tickedOwners(group) {
    return Array.from(document.querySelectorAll('[data-owner="' + group + '"]'))
      .filter((box) => box.checked).map((box) => box.value);
  },

  // The status vocabulary and its opening value both come from the field spec, so the
  // screen never decides that an agreed action starts Open (coding rule R1). Closed is
  // withheld: an owner requests closure and the committee grants it, so offering the
  // closed status here would only produce a refusal from the domain.
  _actionStatusSelect(id, selected) {
    const spec = this._actionField("status");
    const chosen = selected || spec.default || "";
    const labels = spec.option_labels || {};
    const options = (spec.options || []).filter((s) => s !== CLOSED_ACTION_STATUS);
    return '<select id="' + esc(id) + '">' + options.map((s) =>
      '<option value="' + esc(s) + '"' + (s === chosen ? " selected" : "") + ">" +
      esc(labels[s] || s) + "</option>").join("") + "</select>";
  },

  _actionsContent() {
    const actions = (this._meeting.data || {}).actions || [];
    const cards = actions.length
      ? actions.map((a) => this._actionCard(a)).join("")
      : '<div class="empty">No actions agreed yet.</div>';
    return '<p class="muted">Actions agreed by the committee. Start with the model the ' +
      "action concerns — the owner tick-boxes default to that model&rsquo;s owner. Progress " +
      "is recorded as dated updates against the action.</p>" +
      '<div id="mact-list">' + cards + "</div>" + this._actionAddForm();
  },

  _actionAddForm() {
    if (this._actionsLocked()) {
      return '<p class="muted" style="margin-top:12px">This meeting is closed — its actions ' +
        "can no longer be changed.</p>";
    }
    return '<div class="section-header" style="margin-top:14px">Agree an action</div>' +
      '<div class="row" style="flex-wrap:wrap;align-items:flex-end">' +
      '<div class="field"><label>Model</label>' + this._actionModelSelect("mact-model", "") + "</div>" +
      '<div class="field" style="flex:1;min-width:240px"><label>Action *</label>' +
      '<input id="mact-desc" style="width:100%"></div></div>' +
      '<div class="field" style="margin-top:6px"><label>Owners</label>' +
      '<div id="mact-owners">' + this._ownerBoxes("mact-owners", []) + "</div></div>" +
      '<div class="row" style="margin-top:8px">' +
      '<div class="field"><label>Status</label>' + this._actionStatusSelect("mact-status", "") +
      "</div>" +
      '<button class="btn small primary" id="mact-add">Add&hellip;</button></div>';
  },

  _actionCard(action) {
    const owners = this._actionOwners(action);
    const model = action.model_id
      ? "Model: " + this._subjectLabelHtml(action.model_id) + " &nbsp;·&nbsp; " : "";
    const remove = this._actionsLocked() ? "" :
      ' <button class="btn small danger" data-mact-rm="' + esc(action.item_id) + '">Remove</button>';
    return '<div class="card" style="margin-bottom:8px">' +
      '<div class="row" style="justify-content:space-between;align-items:flex-start">' +
      "<div><b>" + esc(action.description || "") + "</b>" +
      '<div class="muted" style="font-size:11px;margin-top:2px">' + model +
      "Owners: " + (owners.length ? esc(owners.join(", ")) : "unassigned") + "</div></div>" +
      '<div class="rowact">' + statusBadge(action.status) + remove + "</div></div>" +
      '<div class="section-header" style="margin-top:8px;font-size:11px">Update history</div>' +
      this._actionUpdates(action) + this._actionUpdateForm(action) + "</div>";
  },

  _actionUpdates(action) {
    const updates = action.updates || [];
    if (!updates.length) return '<div class="muted" style="font-size:11px">No updates yet.</div>';
    const base = "/api/meetings/" + this._id + "/collections/actions/" +
      encodeURIComponent(action.item_id) + "/evidence/";
    return updates.map((u) => {
      const evidence = u.filename
        ? ' <a href="' + base + encodeURIComponent(u.filename) + '">&darr; ' +
          esc(u.original_name || u.filename) + "</a>"
        : "";
      return '<div class="prow"><div style="font-size:12px">' +
        (u.date ? '<span class="code">' + esc(u.date) + "</span> " : "") + esc(u.note || "") +
        (u.owners ? ' <span class="muted">→ ' + esc(u.owners) + "</span>" : "") +
        evidence + "</div>" + statusBadge(u.status) + "</div>";
    }).join("");
  },

  // Recording progress is an update, not an edit: the note, the status it moved to and
  // any supporting file are appended, so the action carries its own history rather than
  // only its latest state. Evidence travels with the note that explains it — a file
  // filed on its own says nothing about what it is meant to show.
  _actionUpdateForm(action) {
    if (this._actionsLocked()) return "";
    // A closed action is settled. Reopening it is the committee's decision to take at a
    // meeting, not something an owner does by posting one more update — offering the
    // form here would let a ratified closure be undone without anyone ratifying that.
    if (action.status === CLOSED_ACTION_STATUS) {
      return '<div class="muted" style="font-size:11px;margin-top:6px">Closed by the ' +
        "committee. Reopening it is a decision for a meeting.</div>";
    }
    const id = esc(action.item_id);
    const awaiting = action.status === REQUESTED_CLOSURE_ACTION_STATUS
      ? '<div class="muted" style="font-size:11px;margin-top:6px">Closure requested — ' +
        "the committee ratifies it at its next meeting; until then the action stays " +
        "outstanding.</div>"
      : "";
    return awaiting +
      '<div class="row" style="margin-top:6px;flex-wrap:wrap;align-items:flex-end">' +
      '<div class="field" style="flex:1;min-width:200px"><label>Update note</label>' +
      '<input id="mupd-note-' + id + '" style="width:100%"></div>' +
      '<div class="field"><label>Supporting evidence</label>' +
      '<input type="file" id="mupd-file-' + id + '"></div>' +
      '<div class="field"><label>Status</label>' +
      this._actionStatusSelect("mupd-status-" + id, action.status) + "</div>" +
      '<button class="btn small" data-mact-upd="' + id + '">Add update</button></div>';
  },

  _bindActions() {
    const self = this;
    if (this._actionsLocked()) return;
    const base = "/api/meetings/" + this._id + "/collections/actions";
    const refresh = () => self.show(self._id, "actions");

    // Picking the model re-ticks the owners: that model's owner is the answer nine
    // times in ten, and the committee only has to correct the tenth.
    const modelSelect = document.getElementById("mact-model");
    if (modelSelect) modelSelect.onchange = function () {
      const owner = self._modelOwner(modelSelect.value);
      document.getElementById("mact-owners").innerHTML =
        self._ownerBoxes("mact-owners", owner ? [owner] : []);
    };

    const addBtn = document.getElementById("mact-add");
    if (addBtn) addBtn.onclick = function () {
      const description = val("mact-desc");
      if (!description) { App.toast("Action is required", "error"); return; }
      const status = val("mact-status");
      const owners = self._tickedOwners("mact-owners");
      const fields = {
        description: description, status: status, owner: owners,
        updates: [{ date: actionUpdateDate(), note: "Agreed", status: status,
                    owners: owners.join(", ") }],
      };
      const modelId = val("mact-model");
      if (modelId) fields.model_id = modelId;
      App.amend("Agree an action.", "POST", base, { fields: fields }, refresh);
    };

    // Multipart, because an update may carry a file. The server stamps the date and
    // appends the entry, so the history cannot be rewritten from here.
    document.querySelectorAll("[data-mact-upd]").forEach(function (btn) {
      const id = btn.getAttribute("data-mact-upd");
      btn.onclick = function () {
        const action = ((self._meeting.data || {}).actions || [])
          .find((a) => a.item_id === id) || {};
        const note = val("mupd-note-" + id);
        const status = val("mupd-status-" + id);
        const picked = (document.getElementById("mupd-file-" + id) || {}).files;
        if (!note && !(picked && picked.length) && status === action.status) {
          App.toast("Add a note, a file, or change the status", "error"); return;
        }
        const form = new FormData();
        form.append("note", note);
        form.append("status", status);
        if (picked && picked.length) form.append("file", picked[0]);
        fetch(base + "/" + encodeURIComponent(id) + "/updates", {
          method: "POST", headers: { "X-Auth-Request-User": App.actor() }, body: form,
        }).then(async (res) => {
          if (!res.ok) {
            const e = await res.json().catch(() => ({}));
            throw new Error(e.error || "update failed");
          }
          App.toast(status === REQUESTED_CLOSURE_ACTION_STATUS
            ? "Closure requested — it goes to the committee to ratify" : "Update added", "ok");
          refresh();
        }).catch((e) => App.toast(e.message, "error"));
      };
    });

    document.querySelectorAll("[data-mact-rm]").forEach(function (btn) {
      const id = btn.getAttribute("data-mact-rm");
      btn.onclick = () => App.amend("Remove action " + id + ".", "POST",
        base + "/" + id + "/delete", {}, refresh);
    });
  },
});
