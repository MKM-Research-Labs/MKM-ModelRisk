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

// Model detail view: a PhysicalRisk-style header card + grouped, editable fields.
const Detail = {
  async show(modelId) {
    const specs = await Inventory.specs();
    const m = await App.get("/api/models/" + modelId);
    const d = m.data || {};
    let sections = "";
    specs.groups.forEach(function (g) {
      sections += '<div class="section-header">' + esc(g.group) + "</div>";
      g.fields.forEach(function (f) {
        sections += Detail._row(f, d[f.key], m.retired);
      });
    });
    const retire = m.retired
      ? '<span class="pill">retired — read only</span>'
      : '<button class="btn danger small" id="d-retire">Retire model…</button>';
    document.getElementById("m-detail").innerHTML =
      '<div class="card">' + this._header(m, d) + sections +
      Collections.render(d, specs, m.retired) +
      '<div style="margin-top:14px">' + retire + "</div></div>";

    this._bind(modelId, m, d);
    Collections.bind(
      "/api/models/" + modelId + "/collections/", specs, m.retired,
      () => { this.show(modelId); Inventory.loadList(); },
    );
    document.getElementById("m-detail").scrollIntoView({ behavior: "smooth", block: "start" });
  },

  _header(m, d) {
    const sub = esc(m.model_id) +
      (d.version ? " · v" + esc(d.version) : "") +
      (d.category ? " · " + esc(d.category) : "");
    return '<div class="detail-header"><div>' +
      '<div class="name">' + esc(d.name || m.model_id) + "</div>" +
      '<div class="sub">' + sub + "</div>" +
      '<div style="margin-top:8px">' + tierBadge(d.tier) + " &nbsp; " + ragBadge(d.rag_rating) + "</div>" +
      '</div><div class="right"><div class="olabel">Owner</div>' +
      '<div class="oname">' + fieldDisplay(d.owner) + "</div>" +
      '<div class="pill">' + fieldDisplay(d.model_owner_role) + "</div></div></div>";
  },

  _row(f, value, retired) {
    const editBtn = retired ? "" : '<span class="edit-btn" data-edit="' + f.key + '">edit</span>';
    return '<div class="inforow" id="row-' + f.key + '">' +
      '<div class="k">' + esc(f.label) + '</div>' +
      '<div class="v">' + fieldDisplay(value) + "</div>" + editBtn + "</div>";
  },

  _bind(modelId, m, d) {
    const self = this;
    if (!m.retired) {
      document.getElementById("d-retire").onclick = function () {
        App.amend("Retire model " + modelId + " (it can no longer be edited).", "POST",
          "/api/models/" + modelId + "/retire", {}, function () { Inventory.render(); });
      };
      document.querySelectorAll(".edit-btn").forEach(function (btn) {
        const key = btn.getAttribute("data-edit");
        btn.onclick = function () { self._edit(modelId, Inventory.specByKey(key), d[key]); };
      });
    }
  },

  _edit(modelId, f, current) {
    const row = document.getElementById("row-" + f.key);
    const editorId = "ed-" + f.key;
    row.innerHTML =
      '<div class="k">' + esc(f.label) + '</div>' +
      '<div class="editor">' + inputControl(editorId, f) +
      '<button class="btn small primary" id="ed-save">Save…</button>' +
      '<button class="btn small" id="ed-cancel">Cancel</button></div>';
    const input = document.getElementById(editorId);
    if (current !== null && current !== undefined) input.value = current;
    document.getElementById("ed-cancel").onclick = () => this.show(modelId);
    document.getElementById("ed-save").onclick = () => {
      let value = input.value.trim();
      if (f.type === "tier") value = parseInt(value, 10);
      App.amend("Set " + f.label + ' = "' + input.value + '" on ' + modelId + ".", "POST",
        "/api/models/" + modelId + "/field", { field: f.key, value: value },
        () => { this.show(modelId); Inventory.loadList(); });
    };
  },
};
