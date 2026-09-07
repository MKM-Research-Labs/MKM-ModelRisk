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
// Confirming a standing agenda item, and the minute it records.
//
// The five seeded items are drawn by detail_agenda_standing.js; this is what happens
// when the committee agrees one. Every confirmation writes a minute, because the
// governance record of a meeting is what it decided, not that somebody clicked.
//
// Assigns onto MeetingDetail; loads after detail_agenda_standing.js.

Object.assign(MeetingDetail, {

  _bindStandingAgenda() {
    const self = this;
    document.querySelectorAll("[data-audit-run]").forEach(function (btn) {
      if (btn.disabled) return;
      const id = btn.getAttribute("data-audit-run");
      btn.onclick = () => self._runAudit(id);
    });
    document.querySelectorAll("[data-audit-note]").forEach(function (inp) {
      const id = inp.getAttribute("data-audit-note");
      inp.onchange = () => App.amend("Record the committee's notes on the completeness audit.", "POST",
        "/api/meetings/" + self._id + "/collections/agenda/" + id,
        { fields: { audit_notes: inp.value } }, () => self.show(self._id, "agenda"));
    });
    document.querySelectorAll("[data-ag-confirm]").forEach(function (btn) {
      if (btn.disabled) return;
      const kind = btn.getAttribute("data-ag-confirm");
      const id = btn.getAttribute("data-ag-id");
      btn.onclick = () => self._confirmStanding(kind, id);
    });
    // Membership and roles: the committee grants or declines what Admin proposed. Both
    // go through the confirm-to-amend flow — granting somebody the right to approve is
    // not a click to make absent-mindedly.
    const rule = (attr, verb, summary) =>
      document.querySelectorAll("[" + attr + "]").forEach(function (btn) {
        const itemId = btn.getAttribute(attr);
        const person = (self._membership || []).find((p) => p.item_id === itemId) || {};
        btn.onclick = () => App.amend(
          summary.replace("%s", person.name || itemId) +
            " (" + (person.proposed || []).join(", ") + ").",
          "POST", "/api/meetings/" + self._id + "/membership/" + itemId + "/" + verb, {},
          () => self.show(self._id, "agenda"));
      });
    rule("data-mem-ratify", "ratify", "Ratify %s's roles");
    rule("data-mem-decline", "decline", "Decline the proposed roles for %s");

    // The ratifications raised under AOB — risk categorisation and functional groups —
    // are drawn and wired by detail_agenda_signoffs.js.
    self._bindAobSignoffs();
    document.querySelectorAll("[data-prevmin]").forEach(function (sel) {
      const id = sel.getAttribute("data-prevmin");
      sel.onchange = function () {
        App.amend("Reference the previous minutes under review.", "POST",
          "/api/meetings/" + self._id + "/collections/agenda/" + id,
          { fields: { prev_minutes_meeting: sel.value } },
          () => self.show(self._id, "agenda"));
      };
    });
  },

  // The minute recorded when a standing agenda item is confirmed complete.
  _standingMinute(kind, d) {
    if (kind === "rollcall") return { title: "Meeting opened",
      text: "Meeting called to order by the chair" + (d.chair ? " (" + d.chair + ")" : "") +
        "; quorum confirmed by the secretary" + (d.secretary ? " (" + d.secretary + ")" : "") + "." };
    if (kind === "minutes") return { title: "Previous minutes signed off",
      text: "The minutes of the previous MRM were reviewed and signed off." };
    if (kind === "actions_review") {
      const rows = this._outstandingActions() || [];
      const requested = closureRequestedActions(rows).length;
      return { title: "Outstanding actions reviewed",
        text: "The committee reviewed the " + rows.length + " action(s) outstanding across " +
          "this committee" + (requested ? ", including " + requested + " awaiting closure" : "") +
          ". Closures granted at this meeting are minuted separately." };
    }
    // Without its own branch this fell through to the AOB default below, and
    // ratifying the committee's membership was minuted as "any other business".
    if (kind === "membership") return { title: "Committee membership and roles reviewed",
      text: "The committee reviewed the proposed changes to its membership and the roles " +
        "its members hold. Each change ratified or declined is minuted separately." };
    if (kind === "review_signoff") return { title: "Model sign-offs reviewed",
      text: "The committee reviewed the model risk-rating sign-offs tabled at this meeting (see the Models tab, Approvals)." };
    if (kind === "review_analysis") return { title: "Model analyses reviewed",
      text: "The committee reviewed the model analyses tabled at this meeting and confirmed the outcomes (see the Models tab, Analysis)." };
    if (kind === "completeness_audit") {
      const it = (d.agenda || []).find((a) => a.kind === "completeness_audit") || {};
      const detail = it.audit_version
        ? " (version " + it.audit_version + " — " + (it.audit_entities || "0") + " record(s), "
          + (it.audit_findings || "0") + " finding(s))"
        : "";
      const notes = it.audit_notes ? " Committee notes: " + it.audit_notes : "";
      return { title: "Completeness audit reviewed",
        text: "The committee reviewed the governance completeness audit for the models and products in "
          + "scope for this committee" + detail + "." + notes };
    }
    return { title: "Any other business", text: "Any other business was invited by the chair." };
  },

  // Confirming a standing item records its minute and closes the item off, via
  // the shared completion path in detail_agenda.js.
  _confirmStanding(kind, id) {
    this._completeAgendaItem(id, this._standingMinute(kind, this._meeting.data || {}));
  },
});
