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

// MeetingDetail — the ratifications a committee is asked for under Any Other Business.
//
// Two of the division's settings are MRC-ratified and reach the committee the same way:
// the admin proposes, and the division's next open meeting carries the draft as a one-off
// AOB item. Both are drawn here rather than beside the meeting shell, because one agenda
// item carrying two ratifications is one subject — and because the shell had grown to the
// point where the second one would not have fitted beside the first.
//
// Only a PENDING draft appears, and only while the meeting is open: a committee cannot
// ratify what nobody has proposed, and a closed meeting is a record rather than a desk.
//
// Assigns onto MeetingDetail; loads after detail_agenda_standing.js.

Object.assign(MeetingDetail, {

  // The shell both ratifications share: an amber panel that says what is being asked
  // for, what approving it does, and what stays in force until then.
  _aobPanel(prefix, title, lede, body) {
    return '<div style="margin-top:var(--space-5);padding:var(--space-5) var(--space-6);' +
      'border:1px solid var(--amber);border-radius:var(--radius-md);background:var(--warn-bg)">' +
      "<b>" + title + "</b>" +
      '<p class="muted" style="font-size:var(--size-sm);margin:var(--space-2) 0">' + lede +
      "</p>" + body +
      '<div class="row" style="margin-top:var(--space-4);gap:var(--space-4)">' +
      '<button class="btn small primary" id="' + prefix + '-approve">Approve &amp; make ' +
      "live</button>" +
      '<button class="btn small danger" id="' + prefix + '-reject">Reject</button></div></div>';
  },

  // Both blocks answer the same three questions first: is there a division, is there a
  // draft, and is the meeting still open.
  _aobPending(detail) {
    const division = (this._meeting.data || {}).division;
    if (!division || !detail || detail.state !== "draft") return null;
    if (this._meeting.status === CLOSED_MEETING_STATUS) return null;
    return division;
  },

  // Everything raised under AOB for ratification, in the order a committee meets it.
  _aobSignoffs() {
    return this._categorisationAob() + this._functionalGroupsAob();
  },

  _categorisationAob() {
    const detail = this._categorisation;
    const division = this._aobPending(detail);
    if (!division) return "";
    const draft = detail.draft;
    const ratings = (draft.risk_ratings || []).map((r) =>
      '<span class="ragdot"><span class="dot" style="background:' + esc(r.colour) +
      '"></span><span style="color:' + esc(r.colour) + '">' + esc(r.name) +
      "</span></span>").join(" &nbsp; ");
    const doc = detail.document
      ? '<a href="/api/risk-policy/' + encodeURIComponent(division) +
        '/document" target="_blank">↓ ' + esc(detail.document.original_name) + "</a>"
      : '<span class="muted">none uploaded</span>';
    const body = '<div style="font-size:var(--size-sm)">Ratings: ' + ratings + "</div>" +
      '<div style="font-size:var(--size-sm);margin-top:var(--space-2)">Risk Policy ' +
      "document: " + doc + " &nbsp;|&nbsp; " +
      '<a href="/api/risk-policy/' + encodeURIComponent(division) +
      '/categorisation.pdf" target="_blank">↓ Proposed categorisation (PDF)</a></div>';
    return this._aobPanel("aob-cat",
      "Risk categorisation sign-off &mdash; " + esc(division),
      esc(division) + " has proposed a revised risk categorisation. Approving it makes " +
      "it live for this division's models; the current categorisation stays in force " +
      "until then.", body);
  },

  // The proposed carve-up of the division's estate by function. The committee is shown
  // the whole list rather than a diff: what it is ratifying is the list that will be in
  // force, and a diff invites approving a change without reading what it leaves behind.
  _functionalGroupsAob() {
    const detail = this._functionalGroups;
    const division = this._aobPending(detail);
    if (!division) return "";
    const live = (detail.live || []).length;
    const groups = (detail.draft || []).map((g) =>
      '<li><b>' + esc(g.name || g.id) + '</b> <span class="muted">' + esc(g.id) +
      (g.description ? " &mdash; " + esc(g.description) : "") + "</span></li>").join("");
    const body = '<ul style="font-size:var(--size-sm);margin:0;padding-left:var(--space-8)">' +
      (groups || '<li class="muted">None — this would leave the division with no ' +
       "groups.</li>") + "</ul>";
    return this._aobPanel("aob-fg",
      "Functional groups sign-off &mdash; " + esc(division),
      esc(division) + " has proposed " + (live ? "a revised" : "its first") +
      " set of functional groups — how its estate is grouped by what each record is " +
      "for. Approving it makes these the groups records can be filed under; " +
      (live ? "the current groups stay in force until then." : "until then the division " +
       "has none and no record can be filed."), body);
  },

  // Ratifying either one records the meeting on the event, because "the committee agreed
  // this" is only evidence if you can say which sitting agreed it.
  async _decideRatification(api, noun, division, action) {
    try {
      await App.send("POST", "/api/" + api + "/" + encodeURIComponent(division) + "/" +
        action, { meeting_id: this._id, confirmed: true });
      // What the committee has just made live is what every picker and every grouped
      // list must now offer, including on this page.
      await Groups.load();
      App.toast(noun + (action === "approve" ? " approved and live" : " rejected"), "ok");
      this.show(this._id, this._tab);   // reload so the AOB item reflects the new state
    } catch (e) { App.toast(e.message || "failed", "error"); }
  },

  _decidePolicy(division, action) {
    return this._decideRatification("risk-policy", "Risk categorisation", division, action);
  },

  _decideFunctionalGroups(division, action) {
    return this._decideRatification("functional-groups", "Functional groups", division,
                                    action);
  },

  // Wiring for whichever of the two blocks is present.
  _bindAobSignoffs() {
    const self = this;
    const division = (self._meeting.data || {}).division;
    const wire = (prefix, decide) => ["approve", "reject"].forEach((action) => {
      const btn = document.getElementById(prefix + "-" + action);
      if (btn) btn.onclick = () => decide.call(self, division, action);
    });
    wire("aob-cat", self._decidePolicy);
    wire("aob-fg", self._decideFunctionalGroups);
  },
});
