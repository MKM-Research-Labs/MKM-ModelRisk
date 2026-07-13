// Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
//
// This software is licensed by MKM Research Labs for non-commercial
// research and educational use only. Any commercial use, including
// but not limited to use in or for products or services offered for sale,
// internal business operations intended for commercial advantage, or
// research and development conducted for a commercial entity, is expressly
// prohibited unless separately authorized in writing by MKM Research Labs.
//
// Use, reproduction, distribution, or modification of this code is subject to the
// terms and conditions of the license agreement provided with this software.
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
    const hist = d.rag_signoff_history || [];
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

  // The MRC responsible for this model, derived from its division/department.
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
    const org = [d.division, d.department].filter(Boolean).join(" / ") || "no division/department set";
    return '<div class="inforow"><div class="k">MRC</div>' +
      '<div class="v" style="color:var(--red)">&#9888; No committee covers this model (' +
      esc(org) + "). Set one up under Admin &rarr; MRC.</div></div>";
  },

  // Contents of the "Danger" dtab — replaces the earlier below-card danger zone.
  // Sits inside #dt-content so the tab bar handles activation, and reuses the
  // existing .danger-zone card styling for the red border + header.
  _dangerContent() {
    if (this._model.retired) {
      return '<div class="empty">This model is retired and read-only. Nothing further can be changed.</div>';
    }
    return '<div class="danger-zone">' +
      '<div class="dz-header">Danger Zone</div>' +
      '<div class="dz-row">' +
      '<div class="dz-text"><b>Retire this model</b>' +
      '<p class="muted">Retired models become read-only — no further amendments are accepted. ' +
      "Existing data and audit trail are preserved.</p></div>" +
      '<div class="dz-action"><button class="btn danger small" id="d-retire">Retire model&hellip;</button></div>' +
      "</div></div>";
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
      value = '<span class="muted" style="font-size:11px">Owner</span> ' + ragBadge(d[key]) +
        '<span class="muted" style="font-size:11px;margin-left:12px">Table</span> ' +
        (tableRag ? ragBadge(tableRag) : '<span class="muted">&mdash;</span>');
    } else if (key === "tier" && (d[key] || d[key] === 0)) {
      value = tierBadge(d[key]) + ' <span class="muted">' + esc(tierFullLabel(d[key])) + "</span>";
    } else if (key === "source_module" && d[key]) {
      value = '<span class="code">' + esc(d[key]) + "</span>";
    } else if (key === "mrc_signoff_date" && d.mrc_signoff_meeting) {
      // MRC sign-off shows the granting meeting (not the raw date) once approved.
      value = '<span class="code">' + esc(d.mrc_signoff_meeting) + "</span>";
    }
    // Sign-off + next review are set by the MRC at sign-off, not edited by hand.
    const editLink = (key === "mrc_signoff_date" || key === "next_review_date")
      ? "" : this._editLink(key);
    return '<div class="inforow" id="row-' + key + '"><div class="k">' + esc(f.label) +
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
  },

  _bindRetire() {
    if (this._model.retired) return;
    const self = this;
    const retire = document.getElementById("d-retire");
    if (retire) retire.onclick = function () {
      App.amend("Retire model " + self._id + " (it can no longer be edited).", "POST",
        "/api/models/" + self._id + "/retire", {}, function () { Inventory.render(); });
    };
  },

  _edit(f, current) {
    const row = document.getElementById("row-" + f.key);
    row.innerHTML = '<div class="k">' + esc(f.label) + '</div><div class="editor">' +
      inputControl("ed-input", f) + '<button class="btn small primary" id="ed-save">Save…</button>' +
      '<button class="btn small" id="ed-cancel">Cancel</button></div>';
    const input = document.getElementById("ed-input");
    if (current !== null && current !== undefined) input.value = current;
    document.getElementById("ed-cancel").onclick = () => this.show(this._id, this._tab);
    document.getElementById("ed-save").onclick = () => {
      let value = input.value.trim();
      if (f.type === "tier") value = parseInt(value, 10);
      App.amend("Set " + f.label + ' = "' + input.value + '" on ' + this._id + ".", "POST",
        "/api/models/" + this._id + "/field", { field: f.key, value: value },
        () => { this.show(this._id, this._tab); Inventory.loadList(); });
    };
  },
});
