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
// ML Application detail: what the division's MRC actually asks for.
//
// The policy the division ratified (Admin > ML Review Policy) -- which items it asks
// for, which a review cannot be completed without, and how far this record has got
// against them. Resolved server-side and sent with the record, so the screen never has
// to know that half the catalogue is code and half is a reference list.
//
// Kept in one file because these are one question asked of four things: a training
// field, a review question, the completeness panel, and the review panel's question
// list. Switching an item off in Admin must hide it in all four or in none.
//
// A field switched off is hidden, never erased: the record keeps whatever it already
// recorded. Loads after detail_core.js, which defines MLAppDetail.

Object.assign(MLAppDetail, {

  // The policy the division's MRC ratified: which items it asks for, and which a
  // review cannot be completed without. Resolved server-side and sent with the
  // record, so the screen never has to know that half the catalogue is code and half
  // is a reference list.
  _scope() { return (this._record || {}).review_scope || {}; },

  _inUse(key) {
    const list = this._scope().training_in_use;
    return !list || list.indexOf(key) >= 0;
  },

  _mandatory(key) {
    return (this._scope().training_mandatory || []).indexOf(key) >= 0;
  },

  // Questions join to the policy on their TOPIC, not on an id: a record's copy is
  // seeded with an id of its own, and a record migrated from a model carries that
  // model's questions. Anything the policy does not mention stays asked, so a
  // migration never drops questions off its own review.
  _questionKey(q) { return (q || {}).short_label || ""; },

  _questionInUse(q) {
    const list = this._scope().question_in_use;
    return !list || list.indexOf(this._questionKey(q)) >= 0;
  },

  _questionMandatory(q) {
    return (this._scope().question_mandatory || []).indexOf(this._questionKey(q)) >= 0;
  },

  // Outstanding mandatory questions, named above the table for the same reason the
  // Training tab names its own: "3 outstanding" sends somebody hunting.
  _questionGap() {
    const q = (this._scope().questions) || {};
    const missing = q.missing_mandatory || [];
    if (!missing.length) return "";
    return '<p style="margin:0 0 var(--space-3)"><span class="badge" ' +
      'style="background:var(--red)">' + missing.length + " mandatory outstanding" +
      '</span> <span class="muted">' + missing.map(esc).join(", ") + "</span></p>";
  },

  // What the evidence adds up to. Deliberately NOT the RAG rating: that is the risk
  // the committee signed off, and a thin Training tab is a different fact from a
  // risky model. Both appear on the record and a reader must be able to tell them
  // apart, so this one is named for what it is.
  _completenessPanel(d) {
    const c = (this._scope().training) || d.training_completeness || {};
    const findings = c.qualifications || [];
    const detail = findings.length
      ? '<span class="badge" style="background:var(--amber)">' + findings.length +
        " to tell a reviewer</span>" +
        '<ul style="margin:var(--space-3) 0 0 var(--space-9);padding:0;font-size:var(--size-sm)">' +
        findings.map((q) => "<li>" + esc(q) + "</li>").join("") + "</ul>"
      : '<span class="muted">Nothing recorded here that a reviewer must be told about.</span>';
    // Progress and permission are different questions, so the outstanding mandatory
    // items are named beside the count rather than folded into it. A bar at 40% that
    // is nonetheless completable is not a contradiction.
    const missing = (c.missing_mandatory || []);
    const required = missing.length
      ? '<div style="margin-top:var(--space-2)"><span class="badge" ' +
        'style="background:var(--red)">' + missing.length + " mandatory outstanding" +
        "</span> <span class=\"muted\">" + missing.map(esc).join(", ") + "</span></div>"
      : ((c.mandatory_total || 0)
        ? '<div style="margin-top:var(--space-2)"><span class="badge" ' +
          'style="background:var(--green)">every mandatory field recorded</span></div>'
        : "");
    return '<div class="inforow" style="align-items:flex-start"><div class="k">Evidence' +
      '</div><div class="v"><span class="muted">' + (c.filled || 0) + " of " +
      (c.total || 0) + ' fields recorded</span><div style="margin-top:var(--space-2)">' +
      detail + "</div>" + required + "</div></div>";
  },
});
