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
      ? '<div style="margin-top:14px"><span class="pill">retired — read only</span></div>' : "";
    // Full-width summary of what the model does, spanning both columns.
    const summary = '<div class="inforow" id="row-description" style="margin-bottom:14px">' +
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
      const color = outcome === "Rejected" ? "var(--red)" : "#388e3c";
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
      return '<div class="inforow"><div class="k">MRC</div><div class="v">' +
        esc(c.name || c.value) + ' <span class="pill">' + esc(c.value) + "</span> " +
        '<span class="muted" style="font-size:11px">' + esc(m.level || "") + "-level</span></div></div>";
    }
    const d = this._model.data || {};
    const org = [d.division, d.line_of_business].filter(Boolean).join(" / ") || "no division / line of business set";
    return '<div class="inforow"><div class="k">MRC</div>' +
      '<div class="v" style="color:var(--red)">&#9888; No committee covers this model (' +
      esc(org) + "). Set one up under Admin &rarr; MRC.</div></div>";
  },

  // Contents of the "Danger" dtab — replaces the earlier below-card danger zone.
  // Sits inside #dt-content so the tab bar handles activation, and reuses the
  // existing .danger-zone card styling for the red border + header.
  // The retire/reactivate request already queued with the MRC, if any. While one
  // is outstanding the model must not be able to raise another.
  _pendingLifecycle(d) {
    const open = (d.signoff_requests || []).filter(
      (r) => (r.kind === "retire" || r.kind === "reactivate") &&
        (r.status === "Pending" || r.status === "Attached"));
    return open.length ? open[open.length - 1] : null;
  },

  _dangerZone(body) {
    return '<div class="danger-zone"><div class="dz-header">Danger Zone</div>' +
      '<div class="dz-row">' + body + "</div></div>";
  },

  _dangerContent() {
    const d = this._model.data || {};
    const pending = this._pendingLifecycle(d);
    if (pending) {
      const where = pending.meeting_id
        ? " at " + esc(pending.meeting_id)
        : ", awaiting that committee's next meeting";
      return this._dangerZone(
        '<div class="dz-text"><b>' +
        (pending.kind === "retire" ? "Retirement" : "Reactivation") +
        " awaiting MRC ratification</b>" +
        '<p class="muted">Queued with ' + esc(pending.target_mrc || "the MRC") + where +
        ". Nothing changes until the committee approves it.</p></div>");
    }
    if (this._model.retired) {
      return this._dangerZone(
        '<div class="dz-text"><b>Reactivate this model</b>' +
        '<p class="muted">This model is hibernated: it is out of the active inventory and ' +
        "read-only. Bringing it back is the committee's decision, so this asks the MRC to " +
        "ratify it.</p></div>" +
        '<div class="dz-action"><button class="btn small" id="d-reactivate">' +
        "Request reactivate&hellip;</button></div>");
    }
    return this._dangerZone(
      '<div class="dz-text"><b>Retire this model</b>' +
      '<p class="muted">Retiring hibernates the model: it drops out of the active inventory ' +
      "and becomes read-only, though its data and audit trail are kept and it can be brought " +
      "back later. The MRC must ratify it, so the model stays active until the committee " +
      "approves.</p></div>" +
      '<div class="dz-action"><button class="btn danger small" id="d-retire">' +
      "Request retire&hellip;</button></div>");
  },

  _editLink(key) {
    return this._model.retired ? "" : '<span class="edit-btn" data-edit="' + key + '">edit</span>';
  },

  _row(key, d) {
    const f = this.specByKey(key);
    if (!f) return "";
    let value = fieldDisplay(d[key]);
    if (key === "rag_rating") {
      // Show the owner's RAG alongside what the tier heatmap ("the table") says,
      // so any divergence needing MRC sign-off is visible at a glance.
      const tableRag = (this._risk.heatmap || {}).rag;
      value = '<span class="muted" style="font-size:11px">Owner</span> ' + ragBadge(d[key], d.division) +
        '<span class="muted" style="font-size:11px;margin-left:12px">Table</span> ' +
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
        value += '<div class="muted" style="font-size:11px;margin-top:4px">Proposed ' +
          ragBadge(p.proposed_rag, d.division) + " &mdash; awaiting " +
          esc(p.target_mrc || "MRC") +
          (p.meeting_id ? " at " + esc(p.meeting_id) : " (not yet on an agenda)") +
          "</div>";
      }
    } else if (key === "tier" && (d[key] || d[key] === 0)) {
      value = tierBadge(d[key], d.division) + ' <span class="muted">' +
        esc(tierFullLabel(d[key], d.division)) + "</span>";
    } else if ((key === "materiality" || key === "complexity") && d[key]) {
      // Shown as the admin defined the band — its colour and its explanation — not as a
      // bare "High", so the level means the same thing here as it does in Admin → Risk.
      value = bandDisplay(f, d[key], d.division);
    } else if (key === "source_module" && d[key]) {
      value = '<span class="code">' + esc(d[key]) + "</span>";
    } else if (key === "mrc_signoff_date" && d.mrc_signoff_meeting) {
      // MRC sign-off shows the granting meeting (not the raw date) once approved.
      value = '<span class="code">' + esc(d.mrc_signoff_meeting) + "</span>";
    }
    // Sign-off + next review are set by the MRC at sign-off, not edited by hand.
    const editLink = (key === "mrc_signoff_date" || key === "next_review_date")
      ? "" : this._editLink(key);
    return '<div class="inforow" id="row-' + key + '"><div class="k">' +
      esc(riskFieldLabel(f, d.division)) +
      '</div><div class="v">' + value + "</div>" + editLink + "</div>";
  },

  _bindEdits() {
    const self = this;
    if (!this._model.retired) {
      document.querySelectorAll("[data-edit]").forEach(function (btn) {
        const key = btn.getAttribute("data-edit");
        btn.onclick = function () { self._edit(self.specByKey(key), self._model.data[key]); };
      });
    }
    // "MRC status" links through to the full MRC linkage record.
    const linkage = document.querySelector("[data-open-linkage]");
    if (linkage) linkage.onclick = function () { self._tab = "decisions"; self._render(); };
  },

  // W4c — open the sign-off picker, then hand the chosen meeting off to the
  // standard confirm-to-amend flow.
  _bindSignoffRequest() {
    const btn = document.getElementById("req-signoff");
    if (!btn) return;
    const self = this;
    btn.onclick = function () {
      const proposed = btn.getAttribute("data-proposed");
      // Routing is automatic — the request goes to the model's responsible MRC.
      const mrc = (self._mrc || {}).mrc;
      if (!mrc) {
        App.toast("No MRC covers this model — set one up under Admin → MRC first.", "error");
        return;
      }
      App.amend(
        "Request MRC sign-off for " + self._id + " → " + proposed +
          " (routed to " + (mrc.name || mrc.value) + ").",
        "POST", "/api/models/" + self._id + "/request-signoff",
        { proposed_rag: proposed },
        () => self.show(self._id, "risk"));
    };
    const revoke = document.getElementById("revoke-signoff");
    if (revoke) revoke.onclick = function () {
      App.amend("Revoke the MRC sign-off for " + self._id +
        " — the rating is kept but returns to needing sign-off.",
        "POST", "/api/models/" + self._id + "/revoke-signoff", {},
        () => self.show(self._id, "risk"));
    };
  },

  // Both buttons raise a request for the MRC rather than changing the model:
  // whichever is on screen depends on where the model currently sits.
  _bindRetire() {
    const self = this;
    const ask = function (id, path, summary) {
      const button = document.getElementById(id);
      if (button) button.onclick = function () {
        App.amend(summary, "POST", "/api/models/" + self._id + path, {},
          function () { Detail.show(self._id, "danger"); Inventory.loadList(); });
      };
    };
    ask("d-retire", "/request-retire",
      "Ask the MRC to ratify retiring " + self._id +
      ". It stays active until the committee approves.");
    ask("d-reactivate", "/request-reactivate",
      "Ask the MRC to ratify reactivating " + self._id +
      ". It stays hibernated until the committee approves.");
  },

  _edit(f, current) {
    const row = document.getElementById("row-" + f.key);
    const division = (this._model.data || {}).division;
    // A risk dimension is chosen from the division's bands as Admin → Risk presents them
    // (colour, name, the admin's explanation); everything else keeps the compact control.
    const picker = bandPicker("ed-input", f, division, current);
    row.innerHTML = '<div class="k">' + esc(riskFieldLabel(f, division)) + '</div><div class="editor">' +
      (picker || inputControl("ed-input", f, division)) +
      '<button class="btn small primary" id="ed-save">Save…</button>' +
      '<button class="btn small" id="ed-cancel">Cancel</button></div>';
    const input = document.getElementById("ed-input");
    if (picker) bindBandPicker("ed-input");
    else if (current !== null && current !== undefined) input.value = current;
    document.getElementById("ed-cancel").onclick = () => this.show(this._id, this._tab);
    document.getElementById("ed-save").onclick = () => {
      let value = input.value.trim();
      if (f.type === "tier") value = parseInt(value, 10);
      // Changing the RAG rating isn't applied directly — it is proposed to the
      // MRC for sign-off, and only takes effect once approved.
      if (f.key === "rag_rating") { this._proposeRag(value, current); return; }
      App.amend("Set " + f.label + ' = "' + input.value + '" on ' + this._id + ".", "POST",
        "/api/models/" + this._id + "/field", { field: f.key, value: value },
        () => { this.show(this._id, this._tab); Inventory.loadList(); });
    };
  },

  // Snag: a RAG-rating change must go through the MRC. Rather than setting the
  // field, raise a sign-off request proposing the new rating; the rating only
  // changes when the committee approves it.
  _proposeRag(value, current) {
    if (!value || value === current) { this.show(this._id, this._tab); return; }
    const mrc = (this._mrc || {}).mrc;
    if (!mrc) {
      App.toast("No MRC covers this model — set one up under Admin → MRC first.", "error");
      return;
    }
    App.amend("Propose RAG " + value + " for " + this._id + " — routed to " +
      (mrc.name || mrc.value) + " for MRC sign-off. The rating changes once approved.",
      "POST", "/api/models/" + this._id + "/request-signoff", { proposed_rag: value },
      () => { this.show(this._id, "risk"); Inventory.loadList(); });
  },
});
