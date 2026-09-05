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
// How a review closes.
//
// What still blocks sign-off, the signed report the MRC receives, and the next cycle
// the sign-off schedules.
//
// The blockers are computed rather than stored, and they are named rather than
// counted: "3 outstanding" sends somebody hunting through seven stages. An unanswered
// fairness finding or a failed evaluation blocks here too — those registers are
// controls, so a review cannot be signed off over the top of one.
//
// Assigns onto ReviewPanel; loads after review_panel.js.

Object.assign(ReviewPanel, {

  // What stands between this review and its sign-off. Computed here from the same
  // facts the endpoint uses, so the button says exactly why it is disabled and the
  // server refuses for exactly those reasons.
  _signoffBlockers(d) {
    const agreed = new Set((d.review_progress || []).map((r) => r.stage));
    const out = this._rvStages().filter((s) => s.key !== "signoff" && !agreed.has(s.key))
      .map((s) => s.label + " not agreed");
    const notes = d.review_notes || [];
    const answered = new Set(notes.map((n) => n.resolves).filter(Boolean));
    const open = notes.filter((n) => n.kind === "Challenge" && !answered.has(n.item_id));
    if (open.length) {
      out.push(open.length + " open challenge" + (open.length === 1 ? "" : "s") +
        " (" + open.map((n) => n.item_id).join(", ") + ")");
    }
    return out;
  },

  // The filed report is served by document item, not by filename, so the link is
  // built from the document this sign-off produced.
  _reportLink(d, signoff) {
    const doc = (d.documents || []).find((x) => x.filename === signoff.report_filename);
    if (!doc) return "";
    return '<a class="btn small" style="margin-top:var(--space-3)" target="_blank" rel="noopener" href="' + this._rvApi() +
      esc(this._rvId()) + "/documents/" + esc(doc.item_id) +
      '/download">&darr; Model Review Report</a>';
  },

  _signoffPanel(d) {
    const signed = (d.review_signoffs || []);
    const history = signed.map((s) =>
      '<div class="inforow"><div class="k">' + esc((s.signed_at || "").slice(0, 10)) +
      '</div><div class="v"><b>' + esc(s.signed_by || "") + "</b>" +
      '<div style="white-space:pre-wrap;margin-top:var(--space-2)">' + esc(s.commentary || "") + "</div>" +
      this._reportLink(d, s) + "</div></div>").join("");
    const blockers = this._signoffBlockers(d);
    const gate = blockers.length
      ? '<div class="quorum-banner">The review is not finished: ' +
        esc(blockers.join("; ")) + ".</div>"
      : "";
    const form = this._rvRetired() ? "" :
      '<div class="field" style="margin-top:var(--space-4)"><label for="rs-commentary">Final commentary</label>' +
      '<textarea id="' + this._rvPfx() + 'rs-commentary" rows="4" placeholder="What the reviewer concludes, in ' +
      'their own words — this is printed in the report the committee reads"></textarea></div>' +
      '<button class="btn small primary" id="' + this._rvPfx() + 'rs-signoff"' +
      (blockers.length ? " disabled" : "") + ">Sign off &amp; file the report&hellip;</button>";
    return this._nextCycle(d) + '<div class="section-header">Reviewer sign-off</div>' +
      '<p class="muted" style="font-size:var(--size-sm)">Signing off files the Model Review Report ' +
      "against this model &mdash; every stage, both sides of the nine questions, the registers " +
      "and the record of challenge. The MRC receives that report and signs off the risk " +
      "rating; it does not adjudicate the review.</p>" +
      (history ? '<div class="section-header" style="margin-top:var(--space-6)">Signed</div>' + history : "") +
      gate + form + this._thread("signoff", d);
  },

  // Once a review is signed off, the tab's job is to start the next one — and to
  // say why it is happening, because what a reviewer should look at differs
  // between a periodic review, a new version, a change of owner and a direction
  // from the committee.
  _nextCycle(d) {
    const signed = (d.review_signoffs || []).length;
    const started = (d.review_progress || []).filter((r) => r.stage === "cycle-start").length;
    if (!signed || this._rvRetired()) return "";
    if (started > signed - 1 && d.review_status !== "Signed off") return "";
    return '<div class="section-header">Start the next review</div>' +
      '<p class="muted" style="font-size:var(--size-sm)">This review is signed off. Starting another ' +
      "clears the stages for the new one &mdash; nothing is erased: the approvals, the " +
      "record of challenge and the report just signed stay on the model.</p>" +
      '<div class="row" style="align-items:center">' +
      '<select id="' + this._rvPfx() + 'rc-trigger">' +
      ((this._rvSpecs()).review_triggers || this._rvTriggers()).map((x) =>
        "<option>" + esc(x) + "</option>").join("") + "</select>" +
      '<input id="' + this._rvPfx() + 'rc-note" placeholder="Why now (optional)" style="flex:1">' +
      '<button class="btn small" id="' + this._rvPfx() + 'rc-start">Start a review&hellip;</button></div>';
  },

  _bindCycle() {
    const btn = this._rvEl("rc-start");
    if (!btn) return;
    btn.onclick = () => {
      App.amend("Start a new review of " + this._rvId() + ".", "POST",
        this._rvApi() + this._rvId() + "/review/start-cycle",
        { trigger: this._rvVal("rc-trigger"), note: this._rvVal("rc-note") },
        () => { this._reviewStage = "documents"; this._rvReload(); });
    };
  },

  _bindSignoff() {
    const btn = this._rvEl("rs-signoff");
    if (!btn || btn.disabled) return;
    btn.onclick = () => {
      const commentary = this._rvVal("rs-commentary");
      if (!commentary) { App.toast("The sign-off needs your final commentary", "error"); return; }
      App.amend("Sign off the review of " + this._rvId() + " and file the report.", "POST",
        this._rvApi() + this._rvId() + "/review/sign-off", { commentary: commentary },
        () => this._rvReload());
    };
  },
});
