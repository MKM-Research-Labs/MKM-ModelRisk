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

// MeetingDetail — agenda list. Standing template items render bespoke (see
// detail_agenda_standing.js); manually-added items get a compact card. Sign-off
// items are filtered out here (they render in the Models tab). The add form and
// per-item document/edit/remove wiring live here.
Object.assign(MeetingDetail, {
  // Non-sign-off agenda items (sign-offs render in Models → Approvals).
  _agendaItems() {
    return ((this._meeting.data || {}).agenda || []).filter(
      (it) => !(it.subject_model_id || it.subject_product_id));
  },

  // Standing items in a fixed order, then manual items, then AOB last.
  _orderedAgenda() {
    const order = { rollcall: 0, minutes_signoff: 1, review_signoff: 2, review_analysis: 3, aob: 100 };
    const rank = (it) => {
      const k = this._agendaKind(it);
      return k in order ? order[k] : 50;   // manual items sit between reviews and AOB
    };
    return this._agendaItems().slice().sort((a, b) => rank(a) - rank(b));
  },

  _agendaLocked() { return (this._meeting.data || {}).agenda_locked === "true"; },

  _agendaContent() {
    const locked = this._agendaLocked();
    const items = this._orderedAgenda();
    const cards = items.length
      ? items.map((it, i) => this._agendaKind(it) ? this._standingCard(it, i) : this._manualCard(it, i)).join("")
      : '<div class="empty">No agenda items yet.</div>';
    // Finalise/distribute bar: once the chair/secretary locks the agenda it is
    // read-only and can be downloaded as a distribution pack (ZIP) for members.
    const bar = locked
      ? '<div class="row" style="justify-content:space-between;align-items:center;margin-bottom:10px">' +
        '<span class="badge" style="background:#388e3c">Agenda finalised</span><span>' +
        '<a class="btn small primary" href="/api/meetings/' + esc(this._id) +
        '/distribution.zip">&darr; Distribution pack (ZIP)</a> ' +
        '<button class="btn small" data-agenda-unlock="1">Unlock</button></span></div>'
      : '<div class="row" style="justify-content:flex-end;margin-bottom:10px">' +
        '<button class="btn small" data-agenda-lock="1">Finalise agenda for distribution&hellip;</button></div>';
    let html = bar + '<div id="agenda-list">' + cards + "</div>" + this._eventReviewSection();
    if (!locked) {
      const names = this._participantNames(this._meeting.data || {});
      const presenterOpts = ['<option value=""></option>'].concat(
        names.map((n) => "<option>" + esc(n) + "</option>")).join("");
      html += '<div class="section-header" style="margin-top:14px">Add agenda item</div>' +
        '<div class="row" style="flex-wrap:wrap;align-items:flex-end">' +
        '<div class="field"><label>Title *</label><input id="ag-add-title"></div>' +
        '<div class="field"><label>Description</label><input id="ag-add-description"></div>' +
        '<div class="field"><label>Presenter</label><select id="ag-add-presenter">' + presenterOpts + "</select></div>" +
        '<button class="btn small primary" id="ag-add">Add&hellip;</button></div>' +
        '<p class="muted" style="font-size:11px;margin-top:4px">Attach a document from the item once added.</p>';
    }
    return html;
  },

  // Compact card for a manually-added (kind-less) item.
  _manualCard(item, idx) {
    const meta = [];
    if (item.presenter) meta.push("Presenter: <b>" + esc(item.presenter) + "</b>");
    meta.push("Status: " + statusBadge(item.status));
    const actions = this._agendaLocked() ? "" :
      '<button class="btn small" data-aged="' + esc(item.item_id) + '">Edit</button> ' +
      '<button class="btn small danger" data-agrm="' + esc(item.item_id) + '">Remove</button>';
    return '<div class="card" style="margin-bottom:8px" id="agrow-' + esc(item.item_id) + '">' +
      '<div class="row" style="justify-content:space-between;align-items:flex-start">' +
      "<div><b>" + (idx + 1) + ". " + esc(item.title || "") + "</b>" +
      (item.description ? '<div class="muted" style="margin-top:2px">' + esc(item.description) + "</div>" : "") +
      '</div><div class="rowact">' + actions + "</div></div>" +
      '<div class="muted" style="margin-top:8px">' + meta.join(" &nbsp;·&nbsp; ") + "</div>" +
      '<div style="margin-top:6px;font-size:12px">' + this._agendaDoc(item) + "</div></div>";
  },

  // Operational events fed up from products (allocated when the meeting was
  // scheduled). The committee receives each one with comments and action items.
  _eventReviewItems() {
    return ((this._meeting.data || {}).agenda || []).filter((it) => it.subject_event_id);
  },

  _eventReviewSection() {
    const items = this._eventReviewItems();
    if (!items.length) return "";
    return '<div class="section-header" style="margin-top:16px">Operational events for review</div>' +
      '<p class="muted">Events raised on this committee’s products. Receive each one, ' +
      "recording comments and any action items from the discussion.</p>" +
      items.map((it) => this._eventCard(it)).join("");
  },

  _eventCard(item) {
    const title = "<b>" + esc(item.title || "") + "</b>";
    if (item.status === "Completed") {
      return '<div class="card" style="margin-bottom:8px">' + title +
        ' <span class="badge" style="background:#388e3c">Received</span></div>';
    }
    const id = esc(item.item_id);
    return '<div class="card" style="margin-bottom:8px" id="evrow-' + id + '">' + title +
      '<div class="field" style="max-width:none;margin-top:8px"><label>Comments</label>' +
      '<textarea id="ev-comments-' + id + '" rows="2"></textarea></div>' +
      '<div class="field" style="max-width:none"><label>Action items (one per line)</label>' +
      '<textarea id="ev-actions-' + id + '" rows="2" placeholder="e.g. Add a feed heartbeat alarm"></textarea></div>' +
      '<button class="btn small primary" data-receive-event="' + id + '">Receive event&hellip;</button></div>';
  },

  // A document attach/replace/download control for an agenda item.
  _agendaDoc(item) {
    return '<input type="file" id="agdoc-file-' + esc(item.item_id) + '" style="display:none">' +
      (item.document_original_name
        ? '<a href="/api/meetings/' + esc(this._id) + "/agenda/" + esc(item.item_id) +
          '/document" target="_blank">' + esc(item.document_original_name) + "</a> "
        : '<span class="muted">No document. </span>') +
      '<button class="btn small" data-agdoc="' + esc(item.item_id) + '">' +
      (item.document_original_name ? "Replace" : "Attach") + " document&hellip;</button>";
  },

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
