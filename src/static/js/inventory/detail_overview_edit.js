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

// Changing what a model's Overview says, and the two requests that are not a change at
// all.
//
// Split from detail_overview.js, which draws the two columns. Everything here is a
// write, and the three kinds are deliberately not alike: a field edit is the owner
// correcting the record, a RAG proposal is the owner ASKING the MRC to move the
// rating, and retiring is the committee's decision reached through DangerZone.
//
// The middle one is the reason this is worth separating. A model's rating is not the
// owner's to set — proposing one queues a sign-off request against a meeting, and the
// rating on the record does not move until that meeting agrees it. An inline editor
// that quietly wrote the new value would look identical to the owner and would be a
// governance failure.
//
// Assigns onto Detail; loads after detail_overview.js.

Object.assign(Detail, {

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
    // Review status is set by the workflow, so the row opens it rather than
    // offering an edit that would put the record and the work out of step.
    const review = document.querySelector("[data-goreview]");
    if (review) {
      review.onclick = function (e) { e.preventDefault(); self._tab = "review"; self._render(); };
    }
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
    const self = this;
    DangerZone.bind({
      api: "/api/models", id: this._id,
      onDone: function () { Detail.show(self._id, "danger"); Inventory.loadList(); },
    });
  },

  _edit(f, current) {
    DetailShell.fieldEditor({
      scope: "#dt-content", prefix: "ed", spec: f, current: current,
      division: (this._model.data || {}).division, withSave: true,
      onCancel: () => this.show(this._id, this._tab),
      onSave: (value, shown) => {
        // Changing the RAG rating isn't applied directly — it is proposed to the MRC
        // for sign-off, and only takes effect once approved.
        if (f.key === "rag_rating") { this._proposeRag(value, current); return; }
        App.amend("Set " + f.label + ' = "' + shown + '" on ' + this._id + ".", "POST",
          "/api/models/" + this._id + "/field", { field: f.key, value: value },
          () => { this.show(this._id, this._tab); Inventory.loadList(); });
      },
    });
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
