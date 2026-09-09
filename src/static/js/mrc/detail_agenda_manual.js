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

// Acting on a manually-added agenda item: completing it, minuting it, editing what it
// says, and attaching the paper it is about.
//
// The counterpart to detail_agenda_confirm.js, which does the same for the five
// standing items. Drawing an item and acting on one are separate subjects — the card
// in detail_agenda.js is read by everyone at the meeting, while everything here is a
// write, and a write into a meeting has to say who asked for it and what it decided.
//
// Completing an item records a minute for the same reason a standing confirmation
// does: the governance record of a meeting is what it resolved, not that a row
// changed colour. An item added off the template is still a thing the committee
// agreed, and a locked agenda closes the whole set to editing.
//
// Assigns onto MeetingDetail; loads after detail_agenda.js.

Object.assign(MeetingDetail, {

  _bindAgenda() {
    const self = this;
    const items = (this._meeting.data || {}).agenda || [];
    const byId = (attr, el) => items.find((i) => i.item_id === el.getAttribute(attr));
    const lock = document.querySelector("[data-agenda-lock]");
    if (lock) lock.onclick = () => App.amend("Finalise the agenda of " + self._id +
      " for distribution.", "POST", "/api/meetings/" + self._id + "/lock-agenda", {},
      () => self.show(self._id, "agenda"));
    const unlock = document.querySelector("[data-agenda-unlock]");
    if (unlock) unlock.onclick = () => App.amend("Re-open the agenda of " + self._id + ".",
      "POST", "/api/meetings/" + self._id + "/unlock-agenda", {},
      () => self.show(self._id, "agenda"));
    this._bindStandingAgenda();
    this._bindAgendaDocs();
    // Receiving an event is a committee decision — allowed even once the agenda is
    // finalised (it does not add/edit/remove agenda items on the fly).
    document.querySelectorAll("[data-receive-event]").forEach(function (btn) {
      const id = btn.getAttribute("data-receive-event");
      btn.onclick = function () {
        const comments = val("ev-comments-" + id);
        const actions = val("ev-actions-" + id).split("\n").map((s) => s.trim())
          .filter(Boolean).map((description) => ({ description: description }));
        App.amend("Receive this operational event on behalf of the committee?", "POST",
          "/api/meetings/" + self._id + "/agenda/" + id + "/receive-event",
          { comments: comments, actions: actions }, () => self.show(self._id, "agenda"));
      };
    });
    if (this._agendaLocked()) return;   // no add/edit/remove while finalised
    document.getElementById("ag-add").onclick = function () {
      const title = val("ag-add-title");
      if (!title) { App.toast("Title is required", "error"); return; }
      const fields = { title: title };
      const desc = val("ag-add-description"); if (desc) fields.description = desc;
      const pres = val("ag-add-presenter"); if (pres) fields.presenter = pres;
      App.amend("Add an agenda item.", "POST",
        "/api/meetings/" + self._id + "/collections/agenda", { fields: fields },
        () => self.show(self._id, "agenda"));
    };
    document.querySelectorAll("[data-agrm]").forEach(function (btn) {
      const id = btn.getAttribute("data-agrm");
      btn.onclick = () => App.amend("Remove agenda item " + id + ".", "POST",
        "/api/meetings/" + self._id + "/collections/agenda/" + id + "/delete", {},
        () => self.show(self._id, "agenda"));
    });
    document.querySelectorAll("[data-aged]").forEach(function (btn) {
      btn.onclick = () => self._agendaEdit(byId("data-aged", btn));
    });
    document.querySelectorAll("[data-agdone]").forEach(function (btn) {
      const id = btn.getAttribute("data-agdone");
      btn.onclick = () => self._confirmManual(id);
    });
  },

  // The minute recorded when the committee acknowledges a manually-added item.
  // It names the item, who presented it and the paper tabled with it, so the
  // minutes say what was actually reviewed rather than just "item 5 completed".
  _manualMinute(item) {
    const title = item.title || "Agenda item";
    const paper = item.document_original_name
      ? " The paper tabled with it (" + item.document_original_name + ") was reviewed."
      : "";
    return {
      title: title,
      presenter: item.presenter || "",
      text: "The committee reviewed " + title + "." + paper,
    };
  },

  _confirmManual(id) {
    const item = this._agendaItems().find((it) => it.item_id === id);
    if (!item) return;
    this._completeAgendaItem(id, this._manualMinute(item));
  },

  // Record an agenda item's minute, then mark the item Completed. Shared by the
  // standing items and the manually-added ones so both leave the same trail: a
  // minute linked to the item, and the item closed off.
  _completeAgendaItem(id, minute) {
    const self = this;
    App.amend("Confirm — " + minute.title + ".", "POST",
      "/api/meetings/" + this._id + "/collections/minutes",
      { fields: { title: minute.title, text: minute.text, agenda_item_id: id,
                  presenter: minute.presenter || "" } },
      () => {
        App.send("POST", "/api/meetings/" + self._id + "/collections/agenda/" + id,
          { fields: { status: "Completed" }, confirmed: true })
          .then(() => self.show(self._id, "agenda"))
          .catch(() => self.show(self._id, "agenda"));
      });
  },

  // Wire the per-item document upload buttons (manual + minutes-sign-off items).
  _bindAgendaDocs() {
    const self = this;
    document.querySelectorAll("[data-agdoc]").forEach(function (btn) {
      const id = btn.getAttribute("data-agdoc");
      const fileInput = document.getElementById("agdoc-file-" + id);
      btn.onclick = function () { fileInput.click(); };
      fileInput.onchange = function () {
        if (!fileInput.files.length) return;
        const form = new FormData();
        form.append("file", fileInput.files[0]);
        fetch("/api/meetings/" + self._id + "/agenda/" + id + "/document", {
          method: "POST", headers: { "X-Auth-Request-User": App.actor() }, body: form,
        }).then(async (res) => {
          if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || "upload failed"); }
          App.toast("Document attached", "ok");
          self.show(self._id, "agenda");
        }).catch((e) => App.toast(e.message, "error"));
      };
    });
  },

  // Inline edit of a manual item: Title / Description / Presenter (from participants).
  _agendaEdit(item) {
    const card = document.getElementById("agrow-" + item.item_id);
    const names = this._participantNames(this._meeting.data || {});
    const presenterOpts = ['<option value=""></option>'].concat(names.map((n) =>
      "<option" + (n === item.presenter ? " selected" : "") + ">" + esc(n) + "</option>")).join("");
    card.innerHTML =
      '<div class="row" style="flex-wrap:wrap;align-items:flex-end">' +
      '<div class="field"><label>Title</label><input id="ag-ed-title" value="' + esc(item.title || "") + '"></div>' +
      '<div class="field"><label>Description</label><input id="ag-ed-description" value="' +
      esc(item.description || "") + '"></div>' +
      '<div class="field"><label>Presenter</label><select id="ag-ed-presenter">' + presenterOpts + "</select></div>" +
      '<button class="btn small primary" id="ag-save">Save&hellip;</button>' +
      '<button class="btn small" id="ag-cancel">Cancel</button></div>';
    document.getElementById("ag-cancel").onclick = () => this.show(this._id, "agenda");
    document.getElementById("ag-save").onclick = () => {
      const fields = { title: val("ag-ed-title"), description: val("ag-ed-description"),
        presenter: val("ag-ed-presenter") };
      App.amend("Update agenda item " + item.item_id + ".", "POST",
        "/api/meetings/" + this._id + "/collections/agenda/" + item.item_id, { fields: fields },
        () => this.show(this._id, "agenda"));
    };
  },
});
