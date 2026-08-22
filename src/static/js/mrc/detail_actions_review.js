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

// MeetingDetail — the standing review of outstanding actions, and the committee's
// answer to the closures owners have asked for.
//
// Both read the same list: every action still owed across THIS COMMITTEE, not just
// this meeting, because an action agreed at one meeting is answered at a later one.
// The review item shows it; the granting of a closure happens under Signoff, beside
// the other things an owner raises and the committee ratifies.
Object.assign(MeetingDetail, {
  // Fetched on first use and cached for the render pass, mirroring how the Signoff
  // tab loads its reviewable documents: the first pass draws a placeholder, the
  // fetch then triggers exactly one re-render.
  _outstandingActions() {
    if (this._outstanding === undefined) {
      this._outstanding = null;
      App.get("/api/meetings/" + this._id + "/outstanding-actions")
        .then((rows) => { this._outstanding = rows || []; this._render(); })
        .catch(() => { this._outstanding = []; });
    }
    return this._outstanding;
  },

  _closureRequests() { return closureRequestedActions(this._outstandingActions() || []); },

  // One line per action: what it is, who owes it, and the meeting that agreed it —
  // an action carried over several meetings should say so on its face.
  _outstandingRow(action, trailing) {
    const owners = this._actionOwners(action);
    const from = action.meeting_id
      ? '<span class="muted"> · from ' + esc(action.meeting_id) +
        (action.meeting_date ? " (" + esc(action.meeting_date) + ")" : "") + "</span>"
      : "";
    const model = action.model_id
      ? " " + this._subjectLabelHtml(action.model_id) + " &middot;" : "";
    return '<div class="prow"><div style="font-size:var(--size-sm)">' +
      '<span class="code">' + esc(action.item_id) + "</span>" + model + " " +
      esc(action.description || "") +
      '<div class="muted" style="font-size:var(--size-xs)">Owners: ' +
      (owners.length ? esc(owners.join(", ")) : "unassigned") + from + "</div></div>" +
      '<div class="rowact">' + (trailing || statusBadge(action.status)) + "</div></div>";
  },

  // The standing agenda card. Lists everything outstanding and, separately, what is
  // waiting on the committee — the committee confirms it has reviewed them all, and
  // grants the closures under Signoff.
  _actionsReviewCard(item, idx, done) {
    const rows = this._outstandingActions();
    let body;
    if (rows === null) {
      body = '<div class="muted" style="font-size:var(--size-sm)">Loading outstanding actions…</div>';
    } else {
      const requested = closureRequestedActions(rows);
      const still = rows.filter((a) => requested.indexOf(a) < 0);
      body = '<div class="section-header" style="margin-top:var(--space-4);font-size:var(--size-xs)">' +
        "Outstanding (" + still.length + ")</div>" +
        (still.length ? still.map((a) => this._outstandingRow(a)).join("")
          : '<div class="muted" style="font-size:var(--size-xs)">Nothing outstanding.</div>') +
        '<div class="section-header" style="margin-top:var(--space-5);font-size:var(--size-xs)">' +
        "Closure requested (" + requested.length + ")</div>" +
        (requested.length
          ? requested.map((a) => this._outstandingRow(a)).join("") +
            '<div class="muted" style="font-size:var(--size-xs);margin-top:var(--space-2)">Ratify or decline ' +
            "each of these under Signoff &rarr; Action closures.</div>"
          : '<div class="muted" style="font-size:var(--size-xs)">None awaiting the committee.</div>');
    }
    const actions = done ? statusBadge("Completed")
      : '<button class="btn small primary" data-ag-confirm="actions_review" data-ag-id="' +
        esc(item.item_id) + '">Confirm all reviewed</button>';
    return this._agendaShell(item, idx, body, actions);
  },

  // The Signoff tab's Action closures rows. An owner has said an action is done; the
  // committee either accepts that or sends it back, and either way it is minuted.
  _closureSignoffRows() {
    const rows = this._outstandingActions();
    if (rows === null) {
      return '<div class="muted" style="font-size:var(--size-sm)">Loading closure requests…</div>';
    }
    const requested = closureRequestedActions(rows);
    if (!requested.length) {
      return '<div class="empty">No action closures awaiting this committee.</div>';
    }
    return requested.map((a) => {
      const decide =
        '<button class="btn small primary" data-clapprove="' + esc(a.item_id) +
        '" data-clsrc="' + esc(a.meeting_id || this._id) + '">Approve</button> ' +
        '<button class="btn small danger" data-clreject="' + esc(a.item_id) +
        '" data-clsrc="' + esc(a.meeting_id || this._id) + '">Reject</button>';
      return '<div class="card" style="margin-bottom:var(--space-4)">' +
        this._outstandingRow(a, decide) + this._closureEvidence(a) + "</div>";
    }).join("");
  },

  // What the owner is offering as evidence, linked from the request itself: the
  // committee should not have to go and find it before deciding.
  _closureEvidence(action) {
    const withFiles = (action.updates || []).filter((u) => u.filename);
    if (!withFiles.length) {
      return '<div class="muted" style="font-size:var(--size-xs)">No supporting evidence attached.</div>';
    }
    const base = "/api/meetings/" + encodeURIComponent(action.meeting_id || this._id) +
      "/collections/actions/" + encodeURIComponent(action.item_id) + "/evidence/";
    return '<div style="font-size:var(--size-xs)">Evidence: ' + withFiles.map((u) =>
      '<a href="' + base + encodeURIComponent(u.filename) + '">&darr; ' +
      esc(u.original_name || u.filename) + "</a>").join(" &nbsp; ") + "</div>";
  },

  _bindClosureSignoffs() {
    const self = this;
    const decide = (attr, route, verb) =>
      document.querySelectorAll("[" + attr + "]").forEach(function (btn) {
        const id = btn.getAttribute(attr);
        const source = btn.getAttribute("data-clsrc");
        btn.onclick = () => App.amend(
          verb + " the closure of action " + id + ". Add any comments below.",
          "POST", "/api/meetings/" + self._id + "/action-closures/" + route,
          { item_id: id, source_meeting_id: source },
          () => { self._outstanding = undefined; self.show(self._id, "models_in_scope"); });
      });
    decide("data-clapprove", "ratify", "Ratify");
    decide("data-clreject", "reject", "Decline");
  },
});
