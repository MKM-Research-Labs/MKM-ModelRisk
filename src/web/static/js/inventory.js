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

const EDITABLE = [
  "name", "short_name", "description", "category", "tier", "materiality",
  "complexity", "status", "lifecycle_stage", "version", "owner",
  "peer_reviewer", "validation_status", "rag_rating", "review_frequency",
];

const Inventory = {
  async render() {
    const el = document.getElementById("tab-inventory");
    el.innerHTML =
      '<div class="card"><h3>Register a model</h3><div class="row">' +
      '<div class="field"><label>Model ID</label><input id="m-id" placeholder="EXAMPLE-001"></div>' +
      '<div class="field"><label>Name</label><input id="m-name" placeholder="Example Model"></div>' +
      '<div class="field"><label>Tier</label><select id="m-tier">' +
      "<option>1</option><option>2</option><option selected>3</option><option>4</option><option>5</option>" +
      "</select></div>" +
      '<div class="field"><label>Owner</label><input id="m-owner" placeholder="owner@firm"></div>' +
      '<button class="btn primary" id="m-register">Register…</button>' +
      "</div></div>" +
      '<div class="card"><h3>Inventory</h3><div id="m-list"></div></div>' +
      '<div id="m-detail"></div>';
    document.getElementById("m-register").onclick = () => this._register();
    await this._loadList();
  },

  async _loadList() {
    const models = await App.get("/api/models");
    const box = document.getElementById("m-list");
    if (!models.length) {
      box.innerHTML = '<div class="empty">No models yet. Register one above.</div>';
      return;
    }
    let rows = "";
    models.forEach(function (m) {
      const d = m.data || {};
      const status = m.retired ? '<span class="pill">retired</span>' : esc(d.status || "—");
      const rag = d.rag_rating
        ? '<span class="badge ' + esc(d.rag_rating) + '">' + esc(d.rag_rating) + "</span>"
        : "—";
      rows +=
        '<tr class="clickable" data-id="' + esc(m.model_id) + '">' +
        "<td>" + esc(m.model_id) + "</td><td>" + esc(d.name || "") + "</td>" +
        "<td>" + esc(d.tier == null ? "" : d.tier) + "</td><td>" + status + "</td>" +
        "<td>" + rag + "</td></tr>";
    });
    box.innerHTML =
      "<table><thead><tr><th>ID</th><th>Name</th><th>Tier</th><th>Status</th><th>RAG</th></tr></thead><tbody>" +
      rows + "</tbody></table>";
    const self = this;
    box.querySelectorAll("tr.clickable").forEach(function (tr) {
      tr.onclick = function () { self._detail(tr.getAttribute("data-id")); };
    });
  },

  _register() {
    const id = val("m-id"), name = val("m-name"), owner = val("m-owner");
    const tier = parseInt(val("m-tier"), 10);
    if (!id || !name) { App.toast("Model ID and name are required", "error"); return; }
    const fields = { tier: tier };
    if (owner) fields.owner = owner;
    App.amend('Register model "' + id + '" (' + name + ").", "POST", "/api/models",
      { model_id: id, name: name, fields: fields }, () => this.render());
  },

  async _detail(id) {
    const m = await App.get("/api/models/" + id);
    const d = m.data || {};
    let kv = "";
    Object.keys(d).sort().forEach(function (k) {
      kv += '<div class="k">' + esc(k) + '</div><div>' + esc(d[k]) + "</div>";
    });
    let opts = "";
    EDITABLE.forEach(function (f) { opts += "<option>" + f + "</option>"; });
    const retireBtn = m.retired
      ? '<span class="pill">retired — read only</span>'
      : '<button class="btn danger small" id="m-retire">Retire model…</button>';
    document.getElementById("m-detail").innerHTML =
      '<div class="card"><h3>' + esc(id) + "</h3>" +
      '<div class="kv">' + kv + "</div>" +
      '<div class="subhead">Update a field</div>' +
      '<div class="row"><div class="field"><label>Field</label><select id="f-name">' + opts + "</select></div>" +
      '<div class="field"><label>Value</label><input id="f-value"></div>' +
      '<button class="btn small" id="f-apply">Update…</button>' +
      '<span style="flex:1"></span>' + retireBtn + "</div></div>";
    const self = this;
    document.getElementById("f-apply").onclick = function () {
      const field = val("f-name"), value = val("f-value");
      App.amend("Set " + field + ' = "' + value + '" on ' + id + ".", "POST",
        "/api/models/" + id + "/field", { field: field, value: value },
        function () { self._detail(id); self._loadList(); });
    };
    if (!m.retired) {
      document.getElementById("m-retire").onclick = function () {
        App.amend("Retire model " + id + " (it can no longer be edited).", "POST",
          "/api/models/" + id + "/retire", {},
          function () { self.render(); });
      };
    }
  },
};
