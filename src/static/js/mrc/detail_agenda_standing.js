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

// MeetingDetail — the standing agenda items. Each of the five seeded items has a
// focused purpose: rollcall (confirm the meeting is open + quorate), sign-off of
// the previous minutes (attach + confirm), and read-only status lists for model
// sign-off and analysis. Confirmations record a minute.
Object.assign(MeetingDetail, {
  // Resolve a standing item's kind: the stored `kind`, or a title fallback for
  // meetings seeded before the kind field existed.
  _agendaKind(item) {
    if (item.kind) return item.kind;
    const t = (item.title || "").toLowerCase();
    if (t.indexOf("rollcall") >= 0) return "rollcall";
    if (t.indexOf("previous") >= 0 && t.indexOf("minutes") >= 0) return "minutes_signoff";
    if (t.indexOf("model sign-off") >= 0 || t.indexOf("model signoff") >= 0) return "review_signoff";
    if (t.indexOf("model analysis") >= 0) return "review_analysis";
    if (t.indexOf("completeness") >= 0) return "completeness_audit";
    if (t.indexOf("aob") >= 0 || t.indexOf("other business") >= 0) return "aob";
    return "";
  },

  _agendaShell(item, idx, body, actions) {
    return '<div class="card" style="margin-bottom:var(--space-4)" id="agrow-' + esc(item.item_id) + '">' +
      '<div class="row" style="justify-content:space-between;align-items:flex-start">' +
      "<div><b>" + (idx + 1) + ". " + esc(item.title || "") + "</b>" +
      (item.description ? '<div class="muted" style="margin-top:var(--space-1)">' + esc(item.description) + "</div>" : "") +
      '</div><div class="rowact">' + (actions || "") + "</div></div>" + (body || "") + "</div>";
  },

  _standingCard(item, idx) {
    const kind = this._agendaKind(item);
    const done = item.status === "Completed";
    if (kind === "rollcall") {
      const q = this._quorum(this._meeting.data || {});
      const actions = done ? statusBadge("Completed")
        : '<button class="btn small primary" data-ag-confirm="rollcall" data-ag-id="' + esc(item.item_id) + '"' +
          (q.met ? "" : ' disabled title="Quorum not met"') + ">Confirm meeting open</button>";
      const body = '<div class="muted" style="margin-top:var(--space-4);font-size:var(--size-sm)">Chair calls the meeting to order; ' +
        "secretary confirms quorum. " + (q.met ? "Quorate." : "Not yet quorate.") + "</div>";
      return this._agendaShell(item, idx, body, actions);
    }
    if (kind === "minutes_signoff") {
      const actions = done ? statusBadge("Completed")
        : '<button class="btn small primary" data-ag-confirm="minutes" data-ag-id="' + esc(item.item_id) + '">Sign off</button>';
      const body = '<div style="margin-top:var(--space-4);font-size:var(--size-sm)">' + this._prevMinutesPicker(item) +
        '<div style="margin-top:var(--space-3)">' + this._agendaDoc(item) + "</div></div>";
      return this._agendaShell(item, idx, body, actions);
    }
    const complete = (label) => done ? statusBadge("Completed")
      : '<button class="btn small primary" data-ag-confirm="' + kind + '" data-ag-id="' +
        esc(item.item_id) + '">' + label + "</button>";
    if (kind === "review_signoff") return this._agendaShell(item, idx, this._signoffStatusList(), complete("Mark reviewed"));
    if (kind === "review_analysis") return this._agendaShell(item, idx, this._analysisStatusList(), complete("Mark reviewed"));
    if (kind === "actions_review") return this._actionsReviewCard(item, idx, done);
    if (kind === "completeness_audit") return this._completenessAuditCard(item, idx, done);
    if (kind === "membership") return this._membershipCard(item, idx, done);
    return this._agendaShell(item, idx,   // aob
      '<div class="muted" style="margin-top:var(--space-4);font-size:var(--size-sm)">Any other business raised by members.</div>' +
      this._aobSignoffs(),
      complete("Complete"));
  },

  // The previous-minutes chooser on the minutes sign-off item: pick a prior
  // closed meeting (from /prior-minutes) whose saved minutes are under review,
  // then download them. Selecting stores the reference on the agenda item.
  _prevMinutesPicker(item) {
    const prior = this._priorMinutes || [];
    if (!prior.length) return '<span class="muted">No prior meeting minutes on file.</span>';
    const opts = ['<option value="">&mdash; select previous meeting &mdash;</option>'].concat(
      prior.map((p) => '<option value="' + esc(p.meeting_id) + '"' +
        (p.meeting_id === item.prev_minutes_meeting ? " selected" : "") + ">" +
        esc((p.title || p.meeting_id) + (p.date ? " (" + p.date + ")" : "")) + "</option>")).join("");
    const dl = item.prev_minutes_meeting
      ? ' <a href="/api/meetings/' + esc(item.prev_minutes_meeting) +
        '/minutes.pdf" target="_blank">&darr; Previous minutes</a>' : "";
    return '<select data-prevmin="' + esc(item.item_id) + '">' + opts + "</select>" + dl;
  },

  // Read-only list of the meeting's sign-offs and their status (decisions taken
  // in the Models tab).
  _signoffStatusList() {
    const items = this._signoffItems();
    if (!items.length) {
      return '<div class="muted" style="margin-top:var(--space-4);font-size:var(--size-sm)">No sign-offs routed to this meeting.</div>';
    }
    return '<div style="margin-top:var(--space-4)">' + items.map((it) => {
      const subj = subjectOf(it);
      return '<div class="prow"><div style="font-size:var(--size-sm)">' + this._subjectLabelHtml(subj) + " &rarr; " +
        ragBadge(it.proposed_rag) + "</div>" + statusBadge(it.status) + "</div>";
    }).join("") +
      '</div><p class="muted" style="font-size:var(--size-xs);margin-top:var(--space-3)">Decisions are taken in the Models tab (Approvals).</p>';
  },

  // Read-only list of in-scope models and their analysis outcome.
  _analysisStatusList() {
    const models = this._models || [];
    if (!models.length) {
      return '<div class="muted" style="margin-top:var(--space-4);font-size:var(--size-sm)">No models in scope.</div>';
    }
    return '<div style="margin-top:var(--space-4)">' + models.map((m) =>
      '<div class="prow"><div style="font-size:var(--size-sm)"><span class="code">' + esc(m.model_id) + "</span>" +
      (m.name ? " " + esc(m.name) : "") + "</div>" +
      statusBadge(m.analysis_status || "Pending") + "</div>").join("") +
      '</div><p class="muted" style="font-size:var(--size-xs);margin-top:var(--space-3)">Outcomes are recorded in the Models tab (Analysis).</p>';
  },

  // Committee membership and roles: the changes Admin has proposed for the people this
  // committee covers. A role is what lets somebody own, validate or approve, so the
  // committee grants it here — Admin only asks. Ratifying takes effect at once; declining
  // leaves the person with what they already hold.
  _membershipCard(item, idx, done) {
    const proposals = this._membership || [];
    const body = proposals.length
      ? '<div style="margin-top:var(--space-4)">' + proposals.map((p) => {
          const roles = (list) => list.length
            ? list.map((r) => '<span class="pill">' + esc(r) + "</span>").join(" ")
            : '<span class="muted">none</span>';
          return '<div class="prow"><div style="font-size:var(--size-sm)"><b>' + esc(p.name || "") + "</b>" +
            (p.division ? ' <span class="muted">' + esc(p.division) + "</span>" : "") +
            '<div style="margin-top:var(--space-1)">' + roles(p.holds) +
            ' <span class="muted">&rarr;</span> ' + roles(p.proposed) + "</div></div>" +
            '<div class="rowact"><button class="btn small primary" data-mem-ratify="' +
            esc(p.item_id) + '">Ratify&hellip;</button> ' +
            '<button class="btn small" data-mem-decline="' + esc(p.item_id) +
            '">Decline&hellip;</button></div></div>';
        }).join("") + "</div>"
      : '<div class="muted" style="margin-top:var(--space-4);font-size:var(--size-sm)">No membership or role ' +
        "changes are waiting on this committee. Changes are proposed in Admin &rarr; People.</div>";
    const actions = done ? statusBadge("Completed")
      : '<button class="btn small primary" data-ag-confirm="membership" data-ag-id="' +
        esc(item.item_id) + '">Mark reviewed</button>';
    return this._agendaShell(item, idx, body, actions);
  },

  // The Governance completeness audit standing item: run (or re-run) the audit
  // scoped to this committee's in-scope models/products, review the saved PDF,
  // record the committee's comfort, then sign it off. Runs are allowed until the
  // meeting closes; the version and the latest PDF are stamped on the item.
  _completenessAuditCard(item, idx, done) {
    const d = this._meeting.data || {};
    const closed = d.status === "Completed";
    const nModels = (d.models_in_scope || []).length;
    const nProducts = (d.products_in_scope || []).length;
    const has = !!item.audit_filename;
    const latest = has
      ? '<div style="font-size:var(--size-sm)">Version ' + esc(item.audit_version || "1") +
        " &middot; generated by " + esc(item.audit_generated_by || "—") +
        (item.audit_generated_at ? " at " + esc(item.audit_generated_at) : "") +
        " &middot; " + esc(item.audit_entities || "0") + " record(s), " +
        esc(item.audit_findings || "0") + " finding(s) &middot; " +
        '<a href="/api/meetings/' + esc(this._id) +
        '/completeness-audit.pdf" target="_blank" rel="noopener">View / download</a></div>'
      : '<div class="muted" style="font-size:var(--size-sm)">Not yet run.</div>';
    const dis = closed ? " disabled" : "";
    const body = '<div style="margin-top:var(--space-4)">' +
      '<div class="muted" style="font-size:var(--size-sm)">Scoped to ' + nModels + " model(s) and " +
      nProducts + " product(s) in scope for this committee.</div>" +
      '<div style="margin-top:var(--space-3)">' + latest + "</div>" +
      '<div class="field" style="margin-top:var(--space-4)"><label>Committee notes on the audit outcome</label>' +
      '<textarea data-audit-note="' + esc(item.item_id) + '" rows="2" style="width:100%;resize:vertical"' +
      dis + ">" + esc(item.audit_notes || "") + "</textarea></div></div>";
    const runBtn = '<button class="btn small" data-audit-run="' + esc(item.item_id) + '"' +
      (closed ? ' disabled title="Meeting closed"' : "") + ">" + (has ? "Re-run audit" : "Run audit") + "&hellip;</button>";
    const review = done ? statusBadge("Completed")
      : '<button class="btn small primary" data-ag-confirm="completeness_audit" data-ag-id="' +
        esc(item.item_id) + '"' + (has ? "" : ' disabled title="Run the audit first"') + ">Mark reviewed</button>";
    return this._agendaShell(item, idx, body, runBtn + " " + review);
  },

  // Run (or re-run) the scoped completeness audit; the PDF compile is synchronous
  // so give the user immediate feedback, then reload to show the new version.
  _runAudit(id) {
    const self = this;
    App.toast("Running completeness audit…");
    App.send("POST", "/api/meetings/" + this._id + "/completeness-audit/run", {})
      .then(() => { App.toast("Completeness audit generated", "ok"); self.show(self._id, "agenda"); })
      .catch((e) => App.toast(e.message, "error"));
  },
});
