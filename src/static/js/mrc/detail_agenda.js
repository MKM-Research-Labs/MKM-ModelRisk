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
      (it) => !subjectOf(it));
  },

  // The running order comes from the server, which sorts against the committee's own
  // agenda list (Admin > Agenda) — so the console and the minutes cannot disagree, and
  // a committee that reorders its agenda is obeyed. This used to be a rank map here,
  // which meant every newly shipped standing item had to be remembered in two places:
  // it never was, so `membership` had been ranking as a manual item.
  _orderedAgenda() { return this._agendaItems(); },

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
      ? '<div class="row" style="justify-content:space-between;align-items:center;margin-bottom:var(--space-5)">' +
        '<span class="badge" style="background:var(--green)">Agenda finalised</span><span>' +
        '<a class="btn small primary" href="/api/meetings/' + esc(this._id) +
        '/distribution.zip">&darr; Distribution pack (ZIP)</a> ' +
        '<button class="btn small" data-agenda-unlock="1">Unlock</button></span></div>'
      : '<div class="row" style="justify-content:flex-end;margin-bottom:var(--space-5)">' +
        '<button class="btn small" data-agenda-lock="1">Finalise agenda for distribution&hellip;</button></div>';
    let html = bar + '<div id="agenda-list">' + cards + "</div>" + this._eventReviewSection();
    if (!locked) {
      const names = this._participantNames(this._meeting.data || {});
      const presenterOpts = ['<option value=""></option>'].concat(
        names.map((n) => "<option>" + esc(n) + "</option>")).join("");
      html += '<div class="section-header" style="margin-top:var(--space-7)">Add agenda item</div>' +
        '<div class="row" style="flex-wrap:wrap;align-items:flex-end">' +
        '<div class="field"><label>Title *</label><input id="ag-add-title"></div>' +
        '<div class="field"><label>Description</label><input id="ag-add-description"></div>' +
        '<div class="field"><label>Presenter</label><select id="ag-add-presenter">' + presenterOpts + "</select></div>" +
        '<button class="btn small primary" id="ag-add">Add&hellip;</button></div>' +
        '<p class="muted" style="font-size:var(--size-xs);margin-top:var(--space-2)">Attach a document from the item once added.</p>';
    }
    return html;
  },

  // Compact card for a manually-added (kind-less) item.
  _manualCard(item, idx) {
    const meta = [];
    if (item.presenter) meta.push("Presenter: <b>" + esc(item.presenter) + "</b>");
    meta.push("Status: " + statusBadge(item.status));
    // Edit/Remove disappear once the agenda is locked for distribution, but
    // acknowledging an item does not: that is what happens *during* the meeting.
    const done = item.status === "Completed";
    const actions = (this._agendaLocked() ? "" :
      '<button class="btn small" data-aged="' + esc(item.item_id) + '">Edit</button> ' +
      '<button class="btn small danger" data-agrm="' + esc(item.item_id) + '">Remove</button> ') +
      (done ? "" : '<button class="btn small primary" data-agdone="' + esc(item.item_id) +
        '">Mark reviewed</button>');
    return '<div class="card" style="margin-bottom:var(--space-4)" id="agrow-' + esc(item.item_id) + '">' +
      '<div class="row" style="justify-content:space-between;align-items:flex-start">' +
      "<div><b>" + (idx + 1) + ". " + esc(item.title || "") + "</b>" +
      (item.description ? '<div class="muted" style="margin-top:var(--space-1)">' + esc(item.description) + "</div>" : "") +
      '</div><div class="rowact">' + actions + "</div></div>" +
      '<div class="muted" style="margin-top:var(--space-4)">' + meta.join(" &nbsp;·&nbsp; ") + "</div>" +
      '<div style="margin-top:var(--space-3);font-size:var(--size-sm)">' + this._agendaDoc(item) + "</div></div>";
  },

  // Operational events fed up from products (allocated when the meeting was
  // scheduled). The committee receives each one with comments and action items.
  _eventReviewItems() {
    return ((this._meeting.data || {}).agenda || []).filter((it) => it.subject_event_id);
  },

  _eventReviewSection() {
    const items = this._eventReviewItems();
    if (!items.length) return "";
    return '<div class="section-header" style="margin-top:var(--space-8)">Operational events for review</div>' +
      '<p class="muted">Events raised on this committee’s products. Receive each one, ' +
      "recording comments and any action items from the discussion.</p>" +
      items.map((it) => this._eventCard(it)).join("");
  },

  _eventCard(item) {
    const title = "<b>" + esc(item.title || "") + "</b>";
    if (item.status === "Completed") {
      return '<div class="card" style="margin-bottom:var(--space-4)">' + title +
        ' <span class="badge" style="background:var(--green)">Received</span></div>';
    }
    const id = esc(item.item_id);
    return '<div class="card" style="margin-bottom:var(--space-4)" id="evrow-' + id + '">' + title +
      '<div class="field" style="max-width:none;margin-top:var(--space-4)"><label>Comments</label>' +
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
});
