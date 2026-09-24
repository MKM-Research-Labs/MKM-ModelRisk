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

// Detail — the Overview tab: Model Details + Governance columns, the MRC status
// / MRC-committee rows, per-field inline editing, the Danger (retire) tab, and
// the Risk-Rating sign-off request.
Object.assign(Detail, {
  _overview(d) {
    const left = OVERVIEW_LEFT.map((k) => this._row(k, d)).join("");
    // Governance: MRC first, then owner/rating/lifecycle/review-status, then the
    // MRC status (a summary of the MRC linkage) and the MRC-set next review.
    const right = this._mrcRow() +
      OVERVIEW_RIGHT_TOP.map((k) => this._row(k, d)).join("") +
      this._mrcStatusRow(d) + this._row("next_review_date", d);
    const status = this._model.retired
      ? '<div style="margin-top:var(--space-7)"><span class="pill">retired — read only</span></div>' : "";
    // Full-width summary of what the model does, spanning both columns.
    const summary = '<div class="inforow" id="row-description" style="margin-bottom:var(--space-7)">' +
      '<div class="k">Summary</div><div class="v">' + fieldDisplay(d.description) + "</div>" +
      this._editLink("description") + "</div>";
    return summary +
      '<div class="grid2"><div><div class="section-header">Model Details</div>' + left + "</div>" +
      '<div><div class="section-header">Governance</div>' + right +
      "</div></div>" + status;
  },

  // MRC status: a one-line summary of the model's MRC linkage — its latest
  // sign-off decision (or a pending request), linking through to the full record.
  _mrcStatusRow(d) {
    const hist = d.signoff_history || [];
    const latest = hist.length ? hist[hist.length - 1] : null;
    const pending = (this._risk || {}).pending_signoff;
    let value;
    if (latest) {
      const outcome = latest.outcome || "Approved";
      const color = outcome === "Rejected" ? "var(--red)" : Theme.value("green");
      value = '<span style="color:' + color + ';font-weight:600">' + esc(outcome) + "</span> at " +
        '<span class="code">' + esc(latest.meeting_id) + "</span>" +
        (latest.date ? " (" + esc(latest.date) + ")" : "");
    } else if (pending) {
      value = pending.status === "Attached"
        ? 'Pending — on the agenda of <span class="code">' + esc(pending.meeting_id) + "</span>"
        : "Pending — queued for " + esc(pending.target_mrc || "its MRC");
    } else {
      value = '<span class="muted">No MRC decision yet</span>';
    }
    return '<div class="inforow"><div class="k">MRC status</div><div class="v">' + value +
      '</div><span class="edit-btn" data-open-linkage="1">view</span></div>';
  },

  // The MRC responsible for this model, derived from its division / line of business.
  // A missing committee is flagged in red — sign-off can't be routed without one.
  _mrcRow() {
    const m = this._mrc || {};
    if (m.mrc) {
      const c = m.mrc;
      // Every record is signed off by the committee it is assigned to.
      const why = "";
      return '<div class="inforow"><div class="k">MRC</div><div class="v">' +
        esc(c.name || c.value) + ' <span class="pill">' + esc(c.value) + "</span> " +
        '<span class="muted" style="font-size:var(--size-xs)">' + esc(m.level || "") +
        "-level</span>" + why + "</div></div>";
    }
    const d = this._model.data || {};
    const org = [d.division, d.line_of_business].filter(Boolean).join(" / ") || "no division / line of business set";
    return '<div class="inforow"><div class="k">MRC</div>' +
      '<div class="v" style="color:var(--red)">&#9888; No committee covers this model (' +
      esc(org) + "). Set one up under Admin &rarr; MRC.</div></div>";
  },

  // The Danger tab is DangerZone's, drawn from the record and the noun. The model
  // screen had this flow first and now shares it, so a change to how a hibernation
  // is asked for reaches every record type rather than only this one.
  _dangerContent() {
    return DangerZone.content("model", this._model);
  },

  _editLink(key) {
    return this._model.retired ? "" : '<span class="edit-btn" data-edit="' + key + '">edit</span>';
  },

  _row(key, d) {
    const f = this.specByKey(key);
    if (!f) return "";
    // Through the spec, so a status vocabulary shows its label rather than the
    // word the record stores.
    let value = optionLabel(f, d[key]);
    // The owner takes the model as soon as they are named, but the appointment is
    // the committee's to ratify — so the record shows the new name and says the
    // sign-off is outstanding rather than pretending the change is settled.
    if (key === "owner") {
      const pending = pendingOwnerRatification(d);
      if (pending) {
        value += ' <span class="badge" style="background:var(--amber)" title="' +
          esc((pending.from_owner || "unassigned") + " → " + (pending.to_owner || "unassigned")) +
          '">MRC sign-off outstanding</span>';
      }
    }
    if (key === "review_status") {
      // Set by the review workflow (each interim approval carries it forward), so
      // it is not typed here — it links to the tab that moves it instead.
      return '<div class="inforow" id="row-review_status"><div class="k">' + esc(f.label) +
        '</div><div class="v">' + value +
        ' <a href="#" data-goreview="1" style="font-size:var(--size-sm)">open review</a></div></div>';
    }
    if (key === "rag_rating") {
      // Show the owner's RAG alongside what the tier heatmap ("the table") says,
      // so any divergence needing MRC sign-off is visible at a glance.
      const tableRag = (this._risk.heatmap || {}).rag;
      value = '<span class="muted" style="font-size:var(--size-xs)">Owner</span> ' + ragBadge(d[key], d.division) +
        '<span class="muted" style="font-size:var(--size-xs);margin-left:var(--space-6)">Table</span> ' +
        (tableRag ? ragBadge(tableRag, d.division) : '<span class="muted">&mdash;</span>');
      // A proposed rating waits for the committee, so the stored rating does not
      // move when it is raised. Saying so here is the difference between "my
      // change was ignored" and "my change is with the MRC" — without it the
      // screen looks identical after a save and invites the owner to try again.
      const pending = (d.signoff_requests || []).filter(
        (r) => (r.kind || "rag") === "rag" &&
               (r.status === "Pending" || r.status === "Attached"));
      if (pending.length) {
        const p = pending[pending.length - 1];
        value += '<div class="muted" style="font-size:var(--size-xs);margin-top:var(--space-2)">Proposed ' +
          ragBadge(p.proposed_rag, d.division) + " &mdash; awaiting " +
          esc(p.target_mrc || "MRC") +
          (p.meeting_id ? " at " + esc(p.meeting_id) : " (not yet on an agenda)") +
          "</div>";
      }
    } else if (DetailShell.fieldValue(key, f, d) !== null) {
      // The three risk dimensions, shown as the admin defined the band (colour, name,
      // explanation) rather than as the stored score. Shared with every detail screen.
      value = DetailShell.fieldValue(key, f, d);
    } else if (key === "source_module" && d[key]) {
      value = '<span class="code">' + esc(d[key]) + "</span>";
    } else if (key === "mrc_signoff_date" && d.mrc_signoff_meeting) {
      // MRC sign-off shows the granting meeting (not the raw date) once approved.
      value = '<span class="code">' + esc(d.mrc_signoff_meeting) + "</span>";
    }
    // Sign-off + next review are set by the MRC at sign-off, not edited by hand, and
    // an immutable field (the model class) is never edited at all.
    const editLink = (key === "mrc_signoff_date" || key === "next_review_date" ||
                      f.immutable) ? "" : this._editLink(key);
    return '<div class="inforow" id="row-' + key + '"><div class="k">' +
      esc(riskFieldLabel(f, d.division)) +
      '</div><div class="v">' + value + "</div>" + editLink + "</div>";
  },

  // The Risk tab's assessment table: each dimension beside the band the owner picked and
  // the justification for picking it. The overall-rating cell shows what that lands on —
  // the committee sets it, so only its rationale is editable.
  _riskTable(d) {
    const rag = (this._risk.heatmap || {}).rag;
    return riskAssessmentTable({
      data: d,
      division: d.division,
      spec: (key) => this.specByKey(key),
      editLink: (key) => this._editLink(key),
      ratingBadge: rag ? ragBadge(rag, d.division) : "",
    });
  },
});
