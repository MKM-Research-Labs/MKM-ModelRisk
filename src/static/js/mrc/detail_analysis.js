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
// The analysis a meeting reviews, and the handoff behind it.
//
// What is put in front of the committee about a model or product: the analysis
// sub-tabs and the review itself. Split from detail_models.js, which is about which
// records are IN SCOPE for the meeting -- a different question from what the meeting
// is shown about them.
//
// Assigns onto MeetingDetail; loads after detail_models.js.

Object.assign(MeetingDetail, {

  // Handoffs crossing the models in scope: the compatibility record the committee
  // reviews alongside the models either side of it. Derived from the meeting's
  // sign-off items rather than a scope collection — a handoff reaches a meeting by
  // being raised for sign-off, not by being ticked into scope.
  _handoffAnalysis() {
    const items = this._signoffItems("handoff");
    if (!items.length) {
      return '<div class="muted" style="font-size:var(--size-sm);margin-top:var(--space-4)">No handoffs ' +
        "tabled at this meeting. They arrive by being raised for compatibility sign-off.</div>";
    }
    const rows = items.map((it) => {
      const pair = String(it.subject_handoff_id || "").split("~");
      return '<div class="card" style="margin-bottom:var(--space-4)">' +
        '<div class="row" style="justify-content:space-between;align-items:center">' +
        "<div>" + this._subjectLabelHtml(pair[0] || "") +
        ' <span class="muted">&rarr;</span> ' + this._subjectLabelHtml(pair[1] || "") + "</div>" +
        "<div>" + statusBadge(it.status) + "</div></div></div>";
    }).join("");
    return '<p class="muted" style="font-size:var(--size-sm)">The producer &rarr; consumer handoffs ' +
      "tabled here, with the committee's compatibility decision.</p>" + rows;
  },

  // One sub-tab per record type the meeting can put in scope, from the served table,
  // plus Handoffs. Hard-coding the list is what left ML Applications and AI Systems
  // off a screen whose endpoints already existed.
  _analysisSubtabs(kind) {
    const btn = (k, label) => '<button class="dtab' + (k === kind ? " active" : "") +
      '" data-atab="' + k + '">' + label + "</button>";
    const plural = { model: "Models", product: "Products",
                     ml_application: "ML Applications", ai_system: "AI Systems" };
    const tabs = this._scopeKinds().map((s) => btn(s.kind, plural[s.kind] || s.noun));
    return '<div class="dtabs" style="margin-bottom:var(--space-4)">' +
      tabs.join("") + btn("handoff", "Handoffs") + "</div>";
  },

  // One review block per in-scope item: the MRC's confirmation to proceed with a
  // note, plus follow-on remediation (owned by the model/product).
  _analysisReview(cfg) {
    const inScope = cfg.inScope;
    if (!inScope.length) {
      return '<div class="muted" style="font-size:var(--size-sm);margin-top:var(--space-4)">Add ' + cfg.plural +
        " to scope above to record their analysis outcome and remediation.</div>";
    }
    const byId = {};
    cfg.inventory.forEach((m) => { byId[m[cfg.idKey]] = (m.data || {}).remediation_steps || []; });
    const opts = (cur) => ["Pending", "Reviewed — agreed to proceed"].map((s) =>
      "<option" + (s === (cur || "Pending") ? " selected" : "") + ">" + esc(s) + "</option>").join("");
    return inScope.map((m) => {
      const id = m[cfg.idKey];
      const steps = byId[id] || [];
      const stepList = steps.length
        ? steps.map((a) => '<div class="prow"><div style="font-size:var(--size-sm)">' + esc(a.description) +
            ' <span class="muted" style="font-size:var(--size-xxs)">' +
            (a.due_date ? "due " + esc(a.due_date) + " · " : "") + esc(a.status || "Open") + "</span></div></div>").join("")
        : '<div class="muted" style="font-size:var(--size-xs)">No remediation yet.</div>';
      // One line per item, expanding to its review block. A committee works
      // through these one at a time, so seven open blocks is six too many.
      const open = this._reviewOpen === id;
      const head = '<div class="row" data-review-toggle="' + esc(id) +
        '" style="justify-content:space-between;align-items:center;cursor:pointer">' +
        "<div><span class=\"muted\">" + (open ? "&minus;" : "+") + "</span> " +
        '<b class="modelid">' + esc(id) + "</b>" +
        (m.name ? ' <span class="muted">' + esc(m.name) + "</span>" : "") + "</div>" +
        '<div><span class="muted" style="font-size:var(--size-xs)">Outcome</span> ' +
        '<select data-analysis-status="' + esc(id) + '">' + opts(m.analysis_status) + "</select></div></div>";
      if (!open) return '<div class="card" style="margin-bottom:var(--space-3)">' + head + "</div>";
      // The presenter's supporting analysis: a document uploaded against this
      // meeting item, shown as a download link once present.
      const fileLink = m.analysis_filename
        ? '<a href="/api/meetings/' + this._id + "/" + cfg.base + "/" + esc(id) +
          '/analysis" target="_blank" rel="noopener">' +
          esc(m.analysis_original_name || m.analysis_filename) + "</a>"
        : '<span class="muted" style="font-size:var(--size-sm)">None uploaded.</span>';
      return '<div class="card" style="margin-bottom:var(--space-4)">' + head +
        // Note and basis auto-save on change (blur / Enter) — no Save button.
        '<div class="field" style="margin-top:var(--space-3)"><label>Discussion note</label>' +
        '<input data-analysis-note="' + esc(id) + '" value="' + esc(m.analysis_note || "") +
        '" style="width:100%"></div>' +
        // What the MRC is allowing the presenter to proceed on the basis of.
        '<div class="field" style="margin-top:var(--space-3)">' +
        "<label>Basis the MRC is allowing the presenter to proceed on</label>" +
        '<textarea data-analysis-basis="' + esc(id) + '" rows="2" style="width:100%;resize:vertical">' +
        esc(m.proceed_basis || "") + "</textarea></div>" +
        // The presenter uploads their supporting analysis here.
        '<div class="field" style="margin-top:var(--space-3)"><label>Supporting analysis</label>' +
        '<div class="row" style="align-items:center;gap:var(--space-4)">' + fileLink +
        '<input type="file" id="an-file-' + esc(id) + '" style="display:none">' +
        '<button class="btn small" data-an-upload="' + esc(id) + '">' +
        (m.analysis_filename ? "Replace" : "Upload") + "&hellip;</button>" +
        (m.analysis_filename
          ? '<button class="btn small danger" data-an-remove="' + esc(id) + '">Remove</button>'
          : "") +
        "</div></div>" +
        '<div class="section-header" style="margin-top:var(--space-4);font-size:var(--size-xs)">Follow-on remediation</div>' + stepList +
        '<div class="row" style="margin-top:var(--space-3);flex-wrap:wrap;align-items:flex-end">' +
        '<div class="field"><label>Remediation</label><input id="act-desc-' + esc(id) + '"></div>' +
        '<div class="field"><label>Owner</label><input id="act-owner-' + esc(id) + '"></div>' +
        '<div class="field"><label>Due date</label><input type="date" id="act-date-' + esc(id) + '"></div>' +
        '<button class="btn small" data-act-add="' + esc(id) + '">Add remediation</button></div></div>';
    }).join("");
  },
});
