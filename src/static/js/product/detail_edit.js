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

// ProductDetail — per-field rows and inline editing: binding/field rows, the
// sign-off request panel, the Danger (retire) tab, and the shared field/rebind
// editor.
Object.assign(ProductDetail, {
  _editLink(key) {
    return this._product.retired ? "" : '<span class="edit-btn" data-edit="' + key + '">edit</span>';
  },

  _bindingRow(key, d) {
    const f = this.fieldSpec(key);
    return '<div class="inforow" id="row-' + key + '"><div class="k">' + esc(f.label) +
      '</div><div class="v"><span class="code">' + fieldDisplay(d[key]) + "</span></div>" +
      (this._product.retired ? "" : '<span class="edit-btn" data-rebind="' + key + '">rebind</span>') + "</div>";
  },

  _row(key, d) {
    const f = this.fieldSpec(key);
    let value = fieldDisplay(d[key]);
    if (key === "status") value = productStatusBadge(d[key], this._product.retired);
    else if (key === "rag_rating") {
      // Owner's RAG alongside the heatmap ("Table") RAG — any divergence needing
      // MRC sign-off is visible at a glance, exactly as on a model.
      const tableRag = (this._risk.heatmap || {}).rag;
      value = '<span class="muted" style="font-size:11px">Owner</span> ' + ragBadge(d[key]) +
        '<span class="muted" style="font-size:11px;margin-left:12px">Table</span> ' +
        (tableRag ? ragBadge(tableRag) : '<span class="muted">&mdash;</span>');
    } else if (key === "tier" && (d[key] || d[key] === 0)) {
      value = tierBadge(d[key]) + ' <span class="muted">' + esc(tierFullLabel(d[key])) + "</span>";
    }
    // MRC sign-off shows the granting meeting (not the raw date) once approved.
    else if (key === "mrc_signoff_date" && d.mrc_signoff_meeting) {
      value = '<span class="code">' + esc(d.mrc_signoff_meeting) + "</span>";
    }
    // The sign-off date/meeting are set by the MRC approval, not edited by hand.
    const editLink = key === "mrc_signoff_date" ? "" : this._editLink(key);
    return '<div class="inforow" id="row-' + key + '"><div class="k">' + esc(f.label) +
      '</div><div class="v">' + value + "</div>" + editLink + "</div>";
  },

  // MRC sign-off state: a pending/queued request, or a button to request one.
  _signoffPanel(d) {
    const pending = (this._mrc || {}).pending_signoff;
    if (pending) {
      const detail = pending.status === "Attached"
        ? 'on the agenda of <span class="code">' + esc(pending.meeting_id) + "</span>" +
          (pending.meeting_date ? " (" + esc(pending.meeting_date) + ")" : "")
        : "queued for <b>" + esc(pending.target_mrc || "its MRC") +
          "</b> — added to that committee's next scheduled meeting";
      return '<div class="dz-row" style="border:1px solid #f57c00;background:#fff8e1;' +
        'padding:10px 14px;border-radius:6px;margin:8px 0"><div class="dz-text">' +
        '<b>Pending MRC sign-off</b><p class="muted">Proposed <b>' + esc(pending.proposed_rag) +
        "</b> " + detail + ".</p></div></div>";
    }
    if (this._product.retired) return "";
    if (!d.rag_rating) {
      return '<p class="muted" style="font-size:12px;margin:6px 0">Set a RAG rating to request MRC sign-off.</p>';
    }
    if (!(this._mrc || {}).mrc) return "";   // _mrcRow already explains the missing committee
    return '<div class="dz-row" style="border:1px solid var(--line);padding:10px 14px;' +
      'border-radius:6px;margin:8px 0"><div class="dz-text"><b>' + esc(d.rag_rating) +
      " rating not yet signed off</b><p class=\"muted\">Request MRC sign-off — routed to the " +
      "product's committee, picked up at its next meeting.</p></div>" +
      '<div class="dz-action"><button class="btn small primary" id="preq-signoff" data-proposed="' +
      esc(d.rag_rating) + '">Request MRC sign-off&hellip;</button></div></div>';
  },

  _bindSignoffRequest() {
    const btn = document.getElementById("preq-signoff");
    if (!btn) return;
    const self = this;
    btn.onclick = function () {
      const mrc = (self._mrc || {}).mrc;
      if (!mrc) {
        App.toast("No MRC covers this product — bind a model / set up an MRC first.", "error");
        return;
      }
      App.amend("Request MRC sign-off for " + self._id + " → " + btn.getAttribute("data-proposed") +
        " (routed to " + (mrc.name || mrc.value) + ").", "POST",
        "/api/products/" + self._id + "/request-signoff", {},
        () => self.show(self._id, "overview"));
    };
  },

  // Danger tab: retire the Product (mirrors the model's Danger zone).
  _dangerContent() {
    if (this._product.retired) {
      return '<div class="empty">This Product is retired and read-only. Nothing further can be changed.</div>';
    }
    return '<div class="danger-zone">' +
      '<div class="dz-header">Danger Zone</div>' +
      '<div class="dz-row">' +
      '<div class="dz-text"><b>Retire this Product</b>' +
      '<p class="muted">Retired Products become read-only — no further amendments are accepted. ' +
      "Existing data and audit trail are preserved.</p></div>" +
      '<div class="dz-action"><button class="btn danger small" id="product-retire">Retire Product&hellip;</button></div>' +
      "</div></div>";
  },

  _bindDanger() {
    const self = this;
    if (this._product.retired) return;
    const retire = document.getElementById("product-retire");
    if (retire) retire.onclick = function () {
      App.amend("Retire Product " + self._id + " (it can no longer be edited).", "POST",
        "/api/products/" + self._id + "/retire", {}, function () { Product.render(); });
    };
  },

  _bindEdits() {
    const self = this;
    if (this._product.retired) return;
    document.querySelectorAll("[data-edit]").forEach(function (btn) {
      const key = btn.getAttribute("data-edit");
      btn.onclick = function () { self._editor(self.fieldSpec(key), "field", "/field", "Set"); };
    });
    document.querySelectorAll("[data-rebind]").forEach(function (btn) {
      const key = btn.getAttribute("data-rebind");
      btn.onclick = function () { self._editor(self.fieldSpec(key), "component", "/rebind", "Rebind"); };
    });
  },

  // One inline editor for both scalar fields (POST /field) and bindings (POST /rebind).
  _editor(f, paramKey, endpoint, verb) {
    const row = document.getElementById("row-" + f.key);
    row.innerHTML = '<div class="k">' + esc(f.label) + '</div><div class="editor">' +
      inputControl("ped-input", f) + '<button class="btn small primary" id="ped-save">' + verb +
      '…</button><button class="btn small" id="ped-cancel">Cancel</button></div>';
    const input = document.getElementById("ped-input");
    const current = this._product.data[f.key];
    if (current !== null && current !== undefined) input.value = current;
    document.getElementById("ped-cancel").onclick = () => this.show(this._id, "overview");
    document.getElementById("ped-save").onclick = () => {
      const body = paramKey === "component"
        ? { component: f.key, value: input.value.trim() }
        : { field: f.key, value: input.value.trim() };
      App.amend(verb + " " + f.label + ' to "' + input.value + '" on ' + this._id + ".", "POST",
        "/api/products/" + this._id + endpoint, body,
        () => { this.show(this._id, "overview"); Product.loadList(); });
    };
  },
});
