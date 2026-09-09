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

// A model's MRC record: the rating sign-offs a committee has granted, and the decisions
// linked from the meeting log.
//
// The counterpart to product/detail_mrc.js, which draws the same view for a product.
// Split out of detail_core.js for the same reason that one is separate: what a
// committee has decided ABOUT a record is not part of the record, and a screen that
// drew them together would invite editing one of them.
//
// Everything here is read-only, and that is the point — a sign-off lands here once the
// MRC approves it, not when the owner asks. Actions used to be a read-only projection
// in this view and are now first-class on the model's own Actions tab, which is why
// they are not drawn here.
//
// Assigns onto Detail; loads after detail_core.js.

Object.assign(Detail, {

  // The model's MRC record: granted rating sign-offs (which land here once a
  // committee approves) plus decisions linked from the meeting log. Actions are
  // now first-class on the model (the Actions tab), not a read-only projection.
  _mrcLinkage(d) {
    const signoffs = d.signoff_history || [];
    const soSection = signoffs.length
      ? DetailTabs.signoffHistory(signoffs, d.division)
      : '<div class="section-header">Sign-off history</div>' +
        '<div class="empty">No MRC sign-offs granted yet.</div>';
    // Every meeting where this model's analysis was presented (it was in scope),
    // with the committee's outcome and a link to the paper if one was tabled.
    const pres = this._analysisPresentations || [];
    const presSection = pres.length
      ? pres.map((a) => {
          const paper = a.analysis_filename
            ? ' &middot; <a href="/api/meetings/' + esc(a.meeting_id) + "/models/" + esc(this._id) +
              '/analysis" target="_blank" rel="noopener">analysis paper</a>'
            : "";
          return '<div class="prow"><div style="font-size:var(--size-sm)"><b>' + esc(a.meeting_id) + "</b> " +
            '<span class="muted">' + esc(a.meeting_date || "") + "</span> &mdash; " +
            esc(a.analysis_status || "Pending") +
            (a.presenter ? ' <span class="muted">presented by ' + esc(a.presenter) + "</span>" : "") +
            paper + "</div></div>";
        }).join("")
      : '<div class="empty">No analysis presented to an MRC yet.</div>';
    // What the committee is still owed on this model, ahead of the historical record:
    // an outstanding action is the live obligation, so it leads rather than sitting
    // under the decisions that are already taken.
    const outstanding = outstandingActions(this._mrcActions);
    const settled = (this._mrcActions || []).length - outstanding.length;
    const settledNote = settled
      ? '<p class="muted" style="font-size:var(--size-xs)">' + settled + " closed action" +
        (settled === 1 ? "" : "s") + " not shown — the meeting that agreed each one still " +
        "holds it.</p>"
      : "";
    return '<p class="muted">The model&rsquo;s MRC record — actions still outstanding, granted ' +
      "rating sign-offs, the meetings its analysis was presented at, plus decisions linked from " +
      "meetings (read-only, sourced from the meeting log).</p>" +
      '<div class="section-header">MRC actions outstanding</div>' +
      DetailTabs.linkedItems("Actions outstanding", outstanding,
                             ["description", "owner", "status"]) + settledNote +
      soSection +
      '<div class="section-header">Analysis presented to the MRC</div>' + presSection +
      '<div class="section-header">Decisions</div>' +
      DetailTabs.linkedItems("Decisions", this._decisions, ["description", "date"]);
  },
});
