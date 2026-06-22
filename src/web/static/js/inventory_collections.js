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

// Structured collections (assumptions, limitations, validation questions, …)
// rendered as tables with an add form, inline remove, and inline choice edits.
const Collections = {
  render(data, specs, retired) {
    return specs.collections.map((c) => this._section(c, data[c.key] || [], retired)).join("");
  },

  _cell(c, item, f, retired) {
    if (f.type === "choice" && !retired) {
      const opts = ["", ...f.options]
        .map((o) => "<option" + (o === item[f.key] ? " selected" : "") + ">" + esc(o) + "</option>")
        .join("");
      return '<td><select data-upd="' + c.key + "|" + esc(item.item_id) + "|" + f.key +
        '">' + opts + "</select></td>";
    }
    return "<td>" + fieldDisplay(item[f.key]) + "</td>";
  },

  _row(c, item, retired) {
    const cells = c.fields.map((f) => this._cell(c, item, f, retired)).join("");
    const remove = retired ? "" :
      '<td><span class="edit-btn" data-rm="' + c.key + "|" + esc(item.item_id) + '">remove</span></td>';
    return "<tr>" + cells + remove + "</tr>";
  },

  _section(c, items, retired) {
    const head = c.fields.map((f) => "<th>" + esc(f.label) + "</th>").join("") +
      (retired ? "" : "<th></th>");
    const span = c.fields.length + (retired ? 0 : 1);
    const body = items.length
      ? items.map((it) => this._row(c, it, retired)).join("")
      : '<tr><td colspan="' + span + '" class="empty">None.</td></tr>';
    return '<div class="section-header">' + esc(c.label) + "</div>" +
      "<table><thead><tr>" + head + "</tr></thead><tbody>" + body + "</tbody></table>" +
      (retired ? "" : this._addForm(c));
  },

  _addForm(c) {
    const inputs = c.fields.map((f) =>
      '<div class="field"><label>' + esc(f.label) + (f.required ? " *" : "") + "</label>" +
      inputControl("add-" + c.key + "-" + f.key, f) + "</div>").join("");
    return '<div class="row" style="margin-top:8px">' + inputs +
      '<button class="btn small" data-add="' + c.key + '">Add…</button></div>';
  },

  bind(modelId, specs, retired) {
    if (retired) return;
    const base = "/api/models/" + modelId + "/collections/";
    const refresh = () => { Detail.show(modelId); Inventory.loadList(); };
    const byKey = {};
    specs.collections.forEach((c) => { byKey[c.key] = c; });

    document.querySelectorAll("[data-add]").forEach(function (btn) {
      const c = byKey[btn.getAttribute("data-add")];
      btn.onclick = function () {
        const fields = {};
        c.fields.forEach(function (f) {
          const v = val("add-" + c.key + "-" + f.key);
          if (v !== "") fields[f.key] = v;
        });
        App.amend("Add a " + c.label + " item to " + modelId + ".", "POST",
          base + c.key, { fields: fields }, refresh);
      };
    });

    document.querySelectorAll("[data-rm]").forEach(function (el) {
      const parts = el.getAttribute("data-rm").split("|");
      el.onclick = function () {
        App.amend("Remove " + parts[1] + " from " + modelId + ".", "POST",
          base + parts[0] + "/" + parts[1] + "/delete", {}, refresh);
      };
    });

    document.querySelectorAll("[data-upd]").forEach(function (sel) {
      const parts = sel.getAttribute("data-upd").split("|");
      sel.onchange = function () {
        const fields = {};
        fields[parts[2]] = sel.value;
        App.amend("Set " + parts[2] + ' = "' + sel.value + '" on ' + parts[1] + ".",
          "POST", base + parts[0] + "/" + parts[1], { fields: fields }, refresh);
      };
    });
  },
};
