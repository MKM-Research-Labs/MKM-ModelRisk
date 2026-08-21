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

  // The model components, above the Calculating Agent. Read-only for now: they
  // are added and removed on the Components tab, which is the generic collection
  // editor. Listing them here means the panel answers "what is this product built
  // from?" without a reader having to go looking for the tab.
  _componentRows(d) {
    const items = d[this._specs.components] || [];
    if (!items.length) {
      return '<div class="inforow"><div class="k">Models</div><div class="v">' +
        '<span class="muted">No components bound</span></div></div>';
    }
    return items.map(function (c) {
      const role = c.role ? ' <span class="muted">— ' + esc(c.role) + "</span>" : "";
      return '<div class="inforow"><div class="k">' + esc(c.component_type || "Component") +
        '</div><div class="v"><span class="code">' + esc(c.model_id || "—") +
        "</span>" + role + "</div></div>";
    }).join("");
  },

  _row(key, d) {
    const f = this.fieldSpec(key);
    let value = fieldDisplay(d[key]);
    if (key === "status") value = productStatusBadge(d[key], this._product.retired);
    else if (key === "rag_rating") {
      // Owner's RAG alongside the heatmap ("Table") RAG — any divergence needing
      // MRC sign-off is visible at a glance, exactly as on a model.
      const tableRag = (this._risk.heatmap || {}).rag;
      value = '<span class="muted" style="font-size:11px">Owner</span> ' + ragBadge(d[key], d.division) +
        '<span class="muted" style="font-size:11px;margin-left:12px">Table</span> ' +
        (tableRag ? ragBadge(tableRag, d.division) : '<span class="muted">&mdash;</span>');
    } else if (DetailShell.fieldValue(key, f, d) !== null) {
      // The three risk dimensions, shown as the admin defined the band (colour, name,
      // explanation) rather than as the stored score. Shared with every detail screen.
      value = DetailShell.fieldValue(key, f, d);
    }
    // MRC sign-off shows the granting meeting (not the raw date) once approved.
    else if (key === "mrc_signoff_date" && d.mrc_signoff_meeting) {
      value = '<span class="code">' + esc(d.mrc_signoff_meeting) + "</span>";
    }
    // The sign-off date/meeting are set by the MRC approval, not edited by hand.
    const editLink = key === "mrc_signoff_date" ? "" : this._editLink(key);
    return '<div class="inforow" id="row-' + key + '"><div class="k">' +
      esc(riskFieldLabel(f, d.division)) +
      '</div><div class="v">' + value + "</div>" + editLink + "</div>";
  },

  // The Risk tab's assessment table — the same three columns a model shows, so a product's
  // categorisation is read and challenged the same way.
  _riskTable(d) {
    const rag = (this._risk.heatmap || {}).rag;
    return riskAssessmentTable({
      data: d,
      division: d.division,
      spec: (key) => this.fieldSpec(key),
      editLink: (key) => this._editLink(key),
      ratingBadge: rag ? ragBadge(rag, d.division) : "",
    });
  },

  // Product-level MRC sign-off removed: the RAG rating is set directly and the
  // committee meeting holds the authoritative MRC status. The read-only "MRC
  // status" row (_mrcStatusRow) still surfaces the latest meeting decision.
  _signoffPanel() {
    return "";
  },

  _bindSignoffRequest() {
    const self = this;
    const btn = document.getElementById("preq-signoff");
    if (!btn) return;
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
  // The control saves on change (its change event fires on blur / Enter) rather than
  // via a Save button. Owner and RAG rating are the confirmation-gated product fields,
  // so those still raise the confirm dialog (App.amend turns the server's 409 into it);
  // every other field just applies.
  _editor(f, paramKey, endpoint, verb) {
    DetailShell.fieldEditor({
      scope: "#pt-content", prefix: "ped", spec: f,
      current: this._product.data[f.key],
      division: (this._product.data || {}).division, withSave: false,
      onCancel: () => this.show(this._id, this._tab),
      onSave: (value, shown) => {
        const body = paramKey === "component"
          ? { component: f.key, value: String(shown).trim() }
          : { field: f.key, value: value };
        App.amend(verb + " " + f.label + ' to "' + shown + '" on ' + this._id + ".", "POST",
          "/api/products/" + this._id + endpoint, body,
          () => { this.show(this._id, this._tab); Product.loadList(); });
      },
    });
  },

  // Snag: a product RAG-rating change goes through the MRC. Raise a sign-off
  // request proposing the new rating; it changes only when the MRC approves.
  _proposeRag(value, current) {
    if (!value || value === current) { this.show(this._id, "overview"); return; }
    const mrc = (this._mrc || {}).mrc;
    if (!mrc) {
      App.toast("No MRC covers this product — bind a model / set up an MRC first.", "error");
      return;
    }
    App.amend("Propose RAG " + value + " for " + this._id + " — routed to " +
      (mrc.name || mrc.value) + " for MRC sign-off. The rating changes once approved.",
      "POST", "/api/products/" + this._id + "/request-signoff", { proposed_rag: value },
      () => { this.show(this._id, "overview"); Product.loadList(); });
  },
});
