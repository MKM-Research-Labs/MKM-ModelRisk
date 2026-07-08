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
// When ``bulk`` is true, the single add row is replaced by five rows so the
// user can capture multiple items (e.g. MRC minutes) in one submission.
const BULK_ROWS = 5;
const Collections = {
  render(data, specs, retired, bulk) {
    return specs.collections.map((c) =>
      this._section(c, data[c.key] || [], retired, bulk)).join("");
  },

  // Fields shown in tables / add forms: internal (hidden) fields — e.g. the
  // agenda escalation back-pointers — are never surfaced to the user.
  _visible(c) { return c.fields.filter((f) => !f.hidden); },

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
    const cells = this._visible(c).map((f) => this._cell(c, item, f, retired)).join("");
    const actions = retired ? "" :
      '<td class="rowact"><span class="edit-btn" data-ed="' + c.key + "|" + esc(item.item_id) +
      '">edit</span><span class="edit-btn" data-rm="' + c.key + "|" + esc(item.item_id) +
      '">remove</span></td>';
    return "<tr>" + cells + actions + "</tr>";
  },

  _section(c, items, retired, bulk) {
    const head = this._visible(c).map((f) => "<th>" + esc(f.label) + "</th>").join("") +
      (retired ? "" : "<th></th>");
    const span = this._visible(c).length + (retired ? 0 : 1);
    const body = items.length
      ? items.map((it) => this._row(c, it, retired)).join("")
      : '<tr><td colspan="' + span + '" class="empty">None.</td></tr>';
    const form = retired ? "" : (bulk ? this._bulkAddForm(c) : this._addForm(c));
    return '<div class="section-header">' + esc(c.label) + "</div>" +
      "<table><thead><tr>" + head + "</tr></thead><tbody>" + body + "</tbody></table>" + form;
  },

  _addForm(c) {
    const inputs = this._visible(c).map((f) =>
      '<div class="field"><label>' + esc(f.label) + (f.required ? " *" : "") + "</label>" +
      inputControl("add-" + c.key + "-" + f.key, f) + "</div>").join("");
    return '<div class="row" style="margin-top:8px">' + inputs +
      '<button class="btn small" data-add="' + c.key + '">Add…</button></div>';
  },

  _bulkAddForm(c) {
    const head = this._visible(c).map((f) =>
      "<th>" + esc(f.label) + (f.required ? " *" : "") + "</th>").join("");
    const rows = [];
    for (let r = 0; r < BULK_ROWS; r++) {
      const cells = this._visible(c).map((f) =>
        "<td>" + inputControl("badd-" + c.key + "-" + r + "-" + f.key, f) + "</td>").join("");
      rows.push("<tr>" + cells + "</tr>");
    }
    return '<div class="section-header" style="margin-top:14px">Add up to ' + BULK_ROWS +
      " at once</div>" +
      "<table><thead><tr>" + head + "</tr></thead><tbody>" + rows.join("") + "</tbody></table>" +
      '<div class="row" style="margin-top:8px">' +
      '<button class="btn small primary" data-bulk-add="' + c.key + '">Save&hellip;</button></div>';
  },

  bind(base, specs, retired, refresh, data, bulk) {
    if (retired) return;
    const byKey = {};
    specs.collections.forEach((c) => { byKey[c.key] = c; });
    const self = this;

    document.querySelectorAll("[data-ed]").forEach(function (el) {
      const parts = el.getAttribute("data-ed").split("|");
      el.onclick = function () {
        const items = (data || {})[parts[0]] || [];
        self._editItem(base, byKey[parts[0]], parts[1], items, refresh);
      };
    });

    if (bulk) {
      document.querySelectorAll("[data-bulk-add]").forEach(function (btn) {
        const c = byKey[btn.getAttribute("data-bulk-add")];
        btn.onclick = function () { self._submitBulk(base, c, refresh); };
      });
    } else {
      document.querySelectorAll("[data-add]").forEach(function (btn) {
        const c = byKey[btn.getAttribute("data-add")];
        btn.onclick = function () {
          const fields = {};
          self._visible(c).forEach(function (f) {
            const v = val("add-" + c.key + "-" + f.key);
            if (v !== "") fields[f.key] = v;
          });
          App.amend("Add an item to " + c.label + ".", "POST",
            base + c.key, { fields: fields }, refresh);
        };
      });
    }

    document.querySelectorAll("[data-rm]").forEach(function (el) {
      const parts = el.getAttribute("data-rm").split("|");
      el.onclick = function () {
        App.amend("Remove " + parts[1] + ".", "POST",
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

  _submitBulk(base, c, refresh) {
    const items = [];
    for (let r = 0; r < BULK_ROWS; r++) {
      const fields = {};
      let any = false;
      this._visible(c).forEach(function (f) {
        const v = val("badd-" + c.key + "-" + r + "-" + f.key);
        if (v !== "") { fields[f.key] = v; any = true; }
      });
      if (any) items.push({ fields: fields });
    }
    if (!items.length) { App.toast("Fill at least one row", "error"); return; }
    App.amend("Add " + items.length + " items to " + c.label + ".", "POST",
      base + c.key + "/bulk", { items: items }, refresh);
  },

  // Replace a row in place with an editor for all of the item's fields.
  _editItem(base, c, itemId, items, refresh) {
    const item = items.find((i) => i.item_id === itemId) || {};
    const row = document.querySelector('[data-ed="' + c.key + "|" + itemId + '"]').closest("tr");
    const visible = this._visible(c);
    const inputs = visible.map((f) =>
      '<div class="field"><label>' + esc(f.label) + "</label>" +
      inputControl("ce-" + f.key, f) + "</div>").join("");
    row.innerHTML = '<td colspan="' + (visible.length + 1) + '"><div class="row">' + inputs +
      '<button class="btn small primary" id="ce-save">Save…</button>' +
      '<button class="btn small" id="ce-cancel">Cancel</button></div></td>';
    visible.forEach(function (f) {
      const el = document.getElementById("ce-" + f.key);
      if (item[f.key] !== null && item[f.key] !== undefined) el.value = item[f.key];
    });
    document.getElementById("ce-cancel").onclick = refresh;
    document.getElementById("ce-save").onclick = function () {
      const fields = {};
      visible.forEach(function (f) {
        const v = val("ce-" + f.key);
        if (v !== "") fields[f.key] = v;
      });
      App.amend("Update " + itemId + ".", "POST", base + c.key + "/" + itemId,
        { fields: fields }, refresh);
    };
  },
};
