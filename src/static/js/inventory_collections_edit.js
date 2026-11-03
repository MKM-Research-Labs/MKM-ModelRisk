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
// Adding to a collection, and editing a row of one.
//
// The add form (one row, or five when a caller asks for bulk capture -- MRC minutes
// arrive several at a time), the inline edits, and the submit handlers.
//
// Split from inventory_collections.js, which now draws the table and nothing else.
// The two are changed for different reasons: a column added to a register is a change
// to what is shown, and a field made editable in place is a change to what can be
// done, and they were being made in the same file.
//
// ``autosave`` (opt-in, used by the Product register tabs) makes every editable field
// an inline control that saves on change -- text fields included -- so a row needs no
// Edit/Save step. Callers that omit it keep the Edit-in-place behaviour.
//
// Assigns onto Collections; loads after inventory_collections.js.

// When ``bulk`` is true the single add row is replaced by five, so a user can capture
// several items (MRC minutes arrive that way) in one submission.
const BULK_ROWS = 5;

Object.assign(Collections, {

  _addForm(c) {
    const inputs = this._visible(c).map((f) =>
      '<div class="field"><label>' + esc(f.label) + (f.required ? " *" : "") + "</label>" +
      inputControl("add-" + c.key + "-" + f.key, f) + "</div>").join("");
    // A grid, not a flex row. Every field in one wrapping row put short inputs
    // beside four-row textareas with nothing aligning them, so the controls floated
    // at different heights and wrapped raggedly — the same form on every collection
    // tab of every record type. The grid gives even columns, tops that line up, and
    // the button on its own line.
    return '<div class="add-form">' + inputs +
      '<div class="add-form-actions"><button class="btn small" data-add="' +
      c.key + '">Add…</button></div></div>';
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
    return '<div class="section-header" style="margin-top:var(--space-7)">Add up to ' + BULK_ROWS +
      " at once</div>" +
      "<table><thead><tr>" + head + "</tr></thead><tbody>" + rows.join("") + "</tbody></table>" +
      '<div class="row" style="margin-top:var(--space-4)">' +
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
        // A multi-select saves the whole list, not the first of it.
        fields[parts[2]] = sel.multiple
          ? [...sel.selectedOptions].map((o) => o.value) : sel.value;
        App.amend("Set " + parts[2] + ' = "' + fields[parts[2]] + '" on ' + parts[1] + ".",
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
      const held = item[f.key];
      if (held === null || held === undefined) return;
      // A multi-select takes a list, and ``.value`` would select only one of it.
      if (el.multiple) [...el.options].forEach((o) => { o.selected = [].concat(held).includes(o.value); });
      else el.value = held;
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
});
