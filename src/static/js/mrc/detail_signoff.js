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
// What a sign-off item is about, and which Approvals tab it belongs on. Written
// once: the subject was previously spelled out at every call site, so adding a
// third kind meant finding all of them.
const SUBJECT_LABEL = { model: "model", product: "product", handoff: "handoff" };

function subjectOf(item) {
  return item.subject_model_id || item.subject_product_id || item.subject_handoff_id || "";
}

function subjectKind(item) {
  if (item.subject_product_id) return "product";
  if (item.subject_handoff_id) return "handoff";
  return "model";
}

Object.assign(MeetingDetail, {
  // Every sign-off item lives in the Signoff tab (Approvals), so the agenda shows
  // only the high-level running order. Handoff compatibility sign-offs are
  // sign-offs like any other: an owner raises them and the committee ratifies them.
  _signoffItems(kind) {
    const items = ((this._meeting.data || {}).agenda || []).filter(subjectOf);
    return kind ? items.filter((a) => subjectKind(a) === kind) : items;
  },

  // What the committee is being asked to ratify. Items raised before the queue
  // carried a kind are rating decisions, which is the safe default.
  _signoffKind(item) {
    return item.signoff_kind || "rag";
  },

  // The "what" shown after the subject: a proposed rating, or a pill naming the
  // lifecycle decision. A retire/reactivate has no rating to show.
  _signoffAsk(item) {
    const kind = this._signoffKind(item);
    if (kind === "retire") {
      return '<span class="badge" style="background:var(--red)">Retire &middot; hibernate</span>';
    }
    if (kind === "reactivate") {
      return '<span class="badge" style="background:var(--accent)">Reactivate</span>';
    }
    return "&rarr; " + ragBadge(item.proposed_rag);
  },

  // A sign-off (Approvals) row for the Models tab: subject + what is asked, with
  // the committee's Approve / Reject decision. Keeps the data-agapprove/
  // data-agreject attrs so the not-quorate lock still applies. Only a rating
  // decision offers a next-review date — it is meaningless for a hibernation.
  _signoffRow(item) {
    const subjectId = subjectOf(item);
    const pending = item.status === "Pending";
    const nextReview = (pending && this._signoffKind(item) === "rag")
      ? '<span class="muted" style="font-size:11px">Next review</span> ' +
        '<input type="date" id="ag-nextreview-' + esc(item.item_id) + '" value="' + oneYearAhead() +
        '" style="padding:3px 6px;font-size:11px"> '
      : "";
    const decision = pending
      ? nextReview +
        '<button class="btn small primary" data-agapprove="' + esc(item.item_id) + '">Approve</button> ' +
        '<button class="btn small danger" data-agreject="' + esc(item.item_id) + '">Reject</button>'
      : statusBadge(item.status);
    const doc = item.document_original_name
      ? ' &nbsp;·&nbsp; <a href="/api/meetings/' + esc(this._id) + "/agenda/" + esc(item.item_id) +
        '/document" target="_blank">' + esc(item.document_original_name) + "</a>"
      : "";
    return '<div class="card" style="margin-bottom:8px"><div class="row" ' +
      'style="justify-content:space-between;align-items:center">' +
      "<div>" + this._subjectLabelHtml(subjectId) + " " + this._signoffAsk(item) +
      doc + '</div><div class="rowact">' + decision + "</div></div></div>";
  },

  // Approvals are split by what is being signed off, so a committee working
  // through model ratings is not reading past handoff items and vice versa. The
  // count sits on each tab: an empty one still has to be visibly empty.
  _approvalSubtabs() {
    const current = this._approvalKind || "model";
    const btn = (k, label) => {
      const n = this._signoffItems(k).length;
      return '<button class="dtab' + (k === current ? " active" : "") +
        '" data-sgtab="' + k + '">' + label + " (" + n + ")</button>";
    };
    return '<div class="dtabs" style="margin-bottom:8px">' +
      btn("model", "Models") + btn("product", "Products") + btn("handoff", "Handoffs") + "</div>";
  },

  _approvalsSection() {
    const kind = this._approvalKind || "model";
    const items = this._signoffItems(kind);
    const rows = items.length
      ? items.map((it) => this._signoffRow(it)).join("")
      : '<div class="empty">No ' + SUBJECT_LABEL[kind] + " sign-offs routed to this meeting.</div>";
    return '<div class="section-header">Approvals — MRC sign-offs</div>' +
      '<p class="muted" style="font-size:12px">Owner-raised requests routed to this committee — ' +
      "risk-rating sign-offs, retirements, reactivations and handoff compatibility. " +
      "Approving carries out the decision and records a minute.</p>" +
      this._approvalSubtabs() + rows;
  },

  // The decision, in words, for the confirm dialog + audit trail.
  _signoffSummary(item, approve) {
    const subj = subjectOf(item);
    const kind = this._signoffKind(item);
    if (kind === "retire") {
      return approve
        ? "Ratify retiring " + subj + " — it will be hibernated (out of the active inventory)."
        : "Reject the retire request for " + subj + " — it stays active.";
    }
    if (kind === "reactivate") {
      return approve
        ? "Ratify reactivating " + subj + " — it returns to the active inventory."
        : "Reject the reactivate request for " + subj + " — it stays hibernated.";
    }
    return approve
      ? "Sign off " + subj + " &rarr; " + item.proposed_rag + " and set its rating."
      : "Reject sign-off for " + subj + " &rarr; " + item.proposed_rag + " (rating not promoted).";
  },

  _bindSignoffs() {
    const self = this;
    const items = this._signoffItems();
    const byId = (attr, el) => items.find((i) => i.item_id === el.getAttribute(attr));
    // A next-review date only exists on the rating row (see _signoffRow).
    const nextReview = (id) => (document.getElementById("ag-nextreview-" + id) || {}).value || null;
    const decide = (attr, outcome, approve) =>
      document.querySelectorAll("[" + attr + "]").forEach(function (btn) {
        const item = byId(attr, btn);
        btn.onclick = () => {
          App.amend(
            self._signoffSummary(item, approve) + " Add any comments below.",
            "POST", "/api/meetings/" + self._id + "/agenda/" + item.item_id + "/" + outcome,
            { next_review_date: nextReview(item.item_id) },
            () => self.show(self._id, "models_in_scope"));
        };
      });
    decide("data-agapprove", "approve-signoff", true);
    decide("data-agreject", "reject-signoff", false);
  },
});
