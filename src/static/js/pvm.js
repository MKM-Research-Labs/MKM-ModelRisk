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

// A coloured status pill (shared with the PVM detail view).
function pvmStatusBadge(status, retired) {
  if (retired) return '<span class="pill">retired</span>';
  const colors = { Active: "#388e3c", Proposed: "#0288d1", Suspended: "#f57c00", Retired: "#9e9e9e" };
  const c = colors[status] || "#9e9e9e";
  return '<span style="display:inline-block;padding:2px 9px;border-radius:10px;color:#fff;' +
    'font-size:12px;background:' + c + '">' + esc(status || "—") + "</span>";
}

// PVMs (Product Valuation Models): one Analytics Model can underpin many PVMs.
const PVM = {
  _specs: null,

  async specs() {
    // Re-fetch so new inventory models / reference values populate the dropdowns.
    this._specs = await App.get("/api/pvms/fields");
    return this._specs;
  },

  fieldSpec(key) {
    let found = null;
    this._specs.groups.forEach((g) => g.fields.forEach((f) => { if (f.key === key) found = f; }));
    return found;
  },

  async render() {
    await this.specs();
    // List and detail are siblings; opening a PVM hides the list view (master-detail).
    document.getElementById("tab-pvm").innerHTML =
      '<div id="pvm-listview"><div id="pvm-summary"></div>' +
      '<div class="card"><div class="row" style="align-items:center">' +
      '<h3 style="margin:0">Product Valuation Models</h3><span style="flex:1"></span>' +
      '<button class="btn small primary" id="pvm-register">+ Register PVM</button></div>' +
      '<div id="pvm-list" style="margin-top:12px"></div></div></div>' +
      '<div id="pvm-detail"></div>';
    document.getElementById("pvm-register").onclick = () => this.openRegister();
    await this.loadList();
  },

  // Register with the PVM ID, product and three component bindings.
  openRegister() {
    const idField = '<div class="field"><label for="preg-pvm_id">PVM ID *</label>' +
      '<input id="preg-pvm_id" placeholder="PVM-0001"></div>';
    const body = this._specs.register.map((k) => {
      const f = this.fieldSpec(k);
      return '<div class="field"><label for="preg-' + k + '">' + esc(f.label) + " *</label>" +
        inputControl("preg-" + k, f) + "</div>";
    }).join("");
    document.getElementById("pvm-reg-body").innerHTML = idField + body;
    document.getElementById("pvm-register-overlay").classList.remove("hidden");
    document.getElementById("preg-pvm_id").focus();
  },

  closeRegister() {
    document.getElementById("pvm-register-overlay").classList.add("hidden");
  },

  submitRegister() {
    const id = val("preg-pvm_id"), product = val("preg-product");
    if (!id || !product || !val("preg-analytics_model")) {
      App.toast("PVM ID, Product and Analytics Model are required", "error"); return;
    }
    const fields = {};
    this._specs.bindings.forEach((k) => { const v = val("preg-" + k); if (v !== "") fields[k] = v; });
    this.closeRegister();
    App.amend('Register PVM "' + id + '" for ' + product + ".", "POST", "/api/pvms",
      { pvm_id: id, product: product, fields: fields }, () => this.render());
  },

  _summary(pvms) {
    const n = (s) => pvms.filter((p) => (p.data || {}).status === s && !p.retired).length;
    const card = (lbl, v, color) =>
      '<div class="scard" style="border-left-color:' + color + '"><div class="lbl">' +
      lbl + '</div><div class="val">' + v + "</div></div>";
    return '<div class="summary">' +
      card("Total", pvms.length, "#1976d2") +
      card("Active", n("Active"), "#388e3c") +
      card("Proposed", n("Proposed"), "#0288d1") +
      card("Suspended", n("Suspended"), "#f57c00") +
      card("Retired", pvms.filter((p) => p.retired).length, "#9e9e9e") +
      "</div>";
  },

  async loadList() {
    const pvms = await App.get("/api/pvms");
    document.getElementById("pvm-summary").innerHTML = this._summary(pvms);
    const box = document.getElementById("pvm-list");
    if (!pvms.length) {
      box.innerHTML = '<div class="empty">No PVMs yet. Register one above.</div>';
      return;
    }
    let rows = "";
    pvms.forEach(function (p) {
      const d = p.data || {};
      rows +=
        '<tr class="clickable" data-id="' + esc(p.pvm_id) + '">' +
        '<td class="modelid">' + esc(p.pvm_id) + "</td>" +
        '<td><span class="code">' + fieldDisplay(d.identifier) + "</span></td>" +
        "<td>" + fieldDisplay(d.product) + "</td>" +
        "<td>" + fieldDisplay(d.analytics_model) + "</td>" +
        "<td>" + pvmStatusBadge(d.status, p.retired) + "</td></tr>";
    });
    box.innerHTML =
      "<table><thead><tr><th>ID</th><th>Identifier</th><th>Product</th>" +
      "<th>Analytics Model</th><th>Status</th></tr></thead><tbody>" + rows + "</tbody></table>";
    box.querySelectorAll("tr.clickable").forEach(function (tr) {
      tr.onclick = function () { PvmDetail.show(tr.getAttribute("data-id")); };
    });
  },
};
