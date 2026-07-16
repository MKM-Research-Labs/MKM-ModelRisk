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

// MeetingDetail — sign-offs (the Models tab's Approvals section). Sign-off items
// are agenda items carrying a subject + proposed RAG; they render here (not on
// the agenda) with the committee's Sign off / Reject decision + next review.
Object.assign(MeetingDetail, {
  // Sign-off items live in the Models tab (Approvals), so the agenda shows only
  // the high-level running order.
  _signoffItems() {
    return ((this._meeting.data || {}).agenda || []).filter(
      (a) => a.subject_model_id || a.subject_product_id);
  },

  // A sign-off (Approvals) row for the Models tab: subject → proposed RAG, with
  // the committee's decision (Sign off / Reject + next review). Keeps the
  // data-agapprove/data-agreject attrs so the not-quorate lock still applies.
  _signoffRow(item) {
    const subjectId = item.subject_model_id || item.subject_product_id;
    const pending = item.status === "Pending";
    const decision = pending
      ? '<span class="muted" style="font-size:11px">Next review</span> ' +
        '<input type="date" id="ag-nextreview-' + esc(item.item_id) + '" value="' + oneYearAhead() +
        '" style="padding:3px 6px;font-size:11px"> ' +
        '<button class="btn small primary" data-agapprove="' + esc(item.item_id) + '">Sign off</button> ' +
        '<button class="btn small danger" data-agreject="' + esc(item.item_id) + '">Reject</button>'
      : statusBadge(item.status);
    const doc = item.document_original_name
      ? ' &nbsp;·&nbsp; <a href="/api/meetings/' + esc(this._id) + "/agenda/" + esc(item.item_id) +
        '/document" target="_blank">' + esc(item.document_original_name) + "</a>"
      : "";
    return '<div class="card" style="margin-bottom:8px"><div class="row" ' +
      'style="justify-content:space-between;align-items:center">' +
      "<div>" + this._subjectLabelHtml(subjectId) + " &rarr; " + ragBadge(item.proposed_rag) +
      doc + '</div><div class="rowact">' + decision + "</div></div></div>";
  },

  _approvalsSection() {
    const items = this._signoffItems();
    const rows = items.length
      ? items.map((it) => this._signoffRow(it)).join("")
      : '<div class="empty">No sign-offs routed to this meeting.</div>';
    return '<div class="section-header">Approvals — risk-rating sign-offs</div>' +
      '<p class="muted" style="font-size:12px">Owner-raised sign-offs routed to this committee. ' +
      "Signing off stamps the subject's rating and records a minute.</p>" + rows;
  },

  _bindSignoffs() {
    const self = this;
    const items = this._signoffItems();
    const byId = (attr, el) => items.find((i) => i.item_id === el.getAttribute(attr));
    const nextReview = (id) => (document.getElementById("ag-nextreview-" + id) || {}).value || null;
    document.querySelectorAll("[data-agapprove]").forEach(function (btn) {
      const item = byId("data-agapprove", btn);
      const subj = item.subject_model_id || item.subject_product_id;
      btn.onclick = () => {
        const nr = nextReview(item.item_id);
        App.amend("Sign off " + subj + " → " + item.proposed_rag +
          ". Sets next review" + (nr ? " " + nr : "") + "; add any comments below.", "POST",
          "/api/meetings/" + self._id + "/agenda/" + item.item_id + "/approve-signoff",
          { next_review_date: nr }, () => self.show(self._id, "models_in_scope"));
      };
    });
    document.querySelectorAll("[data-agreject]").forEach(function (btn) {
      const item = byId("data-agreject", btn);
      const subj = item.subject_model_id || item.subject_product_id;
      btn.onclick = () => {
        const nr = nextReview(item.item_id);
        App.amend("Reject sign-off for " + subj + " → " + item.proposed_rag +
          " (rating not promoted). Add any comments below.", "POST",
          "/api/meetings/" + self._id + "/agenda/" + item.item_id + "/reject-signoff",
          { next_review_date: nr }, () => self.show(self._id, "models_in_scope"));
      };
    });
  },
});
