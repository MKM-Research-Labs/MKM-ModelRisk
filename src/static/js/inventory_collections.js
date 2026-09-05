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

// Structured collections (assumptions, limitations, validation questions, …)
// rendered as tables with an add form, inline remove, and inline choice edits.
const Collections = {
  // ``autosave`` (opt-in, used by the Product register tabs) makes every editable
  // field an inline control that saves on change — text fields included — so a row
  // needs no Edit/Save step. Callers that omit it keep the Edit-in-place behaviour.
  // ``rowClass(item, collectionKey)`` is optional: return a class name to mark a row.
  // Added for the ML review tab, where the division's ratified policy makes some
  // questions mandatory and those carry the red rule. Callers that pass nothing --
  // every model screen -- render exactly as before.
  render(data, specs, retired, bulk, autosave, rowClass) {
    return specs.collections.map((c) =>
      this._section(c, data[c.key] || [], retired, bulk, autosave, rowClass)).join("");
  },

  // Fields shown in tables / add forms: internal (hidden) fields — e.g. the
  // agenda escalation back-pointers — are never surfaced to the user.
  _visible(c) { return c.fields.filter((f) => !f.hidden); },

  // Columns, not fields: a field marked ``stacked`` shares the previous field's column
  // and sits beneath it. A date is narrow and a verdict is not, so giving each its own
  // column squeezed both — and they read together anyway ("within tolerance, as at
  // August"). One column each would be right if the table had room, and it does not.
  _columns(c) {
    const cols = [];
    this._visible(c).forEach((f) => {
      if (f.stacked && cols.length) cols[cols.length - 1].push(f);
      else cols.push([f]);
    });
    return cols;
  },

  // Remediation is edited entirely in place — every field is an inline control
  // (owner/priority/status as selects, due date as a date input), so there is
  // no row-level edit/remove.
  _noActions(c) { return c.key === "remediation_steps"; },
  _hasActions(c, retired) { return !retired && !this._noActions(c); },

  // One table cell: the column's first field, then anything stacked beneath it under
  // its own small label, so a value in a shared column still says what it is.
  _column(c, item, group, retired, autosave) {
    const parts = group.map((f, i) => {
      const inner = this._cell(c, item, f, retired, autosave)
        .replace(/^<td>/, "").replace(/<\/td>$/, "");
      return i === 0 ? inner
        : '<div class="stacked"><span class="stacked-label">' + esc(f.label) +
          "</span>" + inner + "</div>";
    });
    return "<td>" + parts.join("") + "</td>";
  },

  _cell(c, item, f, retired, autosave) {
    if (f.type === "choice" && !retired) {
      const opts = ["", ...f.options]
        .map((o) => "<option" + (o === item[f.key] ? " selected" : "") + ">" + esc(o) + "</option>")
        .join("");
      return '<td><select style="width:100%" data-upd="' + c.key + "|" +
        esc(item.item_id) + "|" + f.key + '">' + opts + "</select></td>";
    }
    if (f.type === "date" && !retired) {
      return '<td><input type="date" style="width:100%" data-upd="' + c.key + "|" +
        esc(item.item_id) + "|" + f.key + '" value="' + esc(item[f.key] || "") + '"></td>';
    }
    // Auto-save mode: a plain text field is an inline input that saves on change
    // (its change event fires on blur) through the same data-upd binding.
    if (autosave && !retired) {
      return '<td><input data-upd="' + c.key + "|" + esc(item.item_id) + "|" + f.key +
        '" value="' + esc(item[f.key] || "") + '" style="width:100%"></td>';
    }
    // Prose goes in a fixed-height box that scrolls. A register is read by running
    // down it, and a single long finding that stretches its row to half the screen
    // pushes everything else out of view — the rows have to stay comparable in height
    // for the table to be scannable at all.
    if (f.type === "textarea") {
      return '<td><div class="cellbox">' + esc(item[f.key] || "") + "</div></td>";
    }
    // Through the spec, so a status vocabulary shows its label rather than the
    // word the row stores.
    return "<td>" + optionLabel(f, item[f.key]) + "</td>";
  },

  _row(c, item, retired, autosave, rowClass) {
    const cells = this._columns(c).map((group) =>
      this._column(c, item, group, retired, autosave)).join("");
    let actions = "";
    if (this._hasActions(c, retired)) {
      // In auto-save mode every field is already inline-editable, so the row needs
      // no Edit step — only Remove.
      const edit = autosave ? "" : '<button class="btn small" data-ed="' + c.key + "|" +
        esc(item.item_id) + '">Edit</button> ';
      actions = '<td class="rowact">' + edit + '<button class="btn small danger" data-rm="' +
        c.key + "|" + esc(item.item_id) + '">Remove</button></td>';
    }
    const cls = rowClass ? (rowClass(item, c.key) || "") : "";
    return "<tr" + (cls ? ' class="' + cls + '"' : "") + ">" + cells + actions + "</tr>";
  },

  // How much width a column deserves, from what it holds. Registers are mostly prose
  // — an assumption, what a fairness test showed — and an even split gave a paragraph
  // the same room as a date, so the prose columns collapsed into slivers a word wide
  // and the register became unreadable exactly as it filled up. A spec can override
  // with ``weight`` where the default reads wrong.
  _WEIGHTS: { textarea: 3, text: 2, choice: 2, tier: 2, date: 1.6, number: 1 },

  _weight(f) { return f.weight || this._WEIGHTS[f.type] || 2; },

  _colgroup(c, retired) {
    // A stacked column takes the widest of what it holds, not the sum: stacking is
    // what frees the width for the field above to expand into.
    const weights = this._columns(c).map((group) =>
      Math.max(...group.map((f) => this._weight(f))));
    if (this._hasActions(c, retired)) weights.push(1.8);
    const total = weights.reduce((a, b) => a + b, 0) || 1;
    return "<colgroup>" + weights.map((w) =>
      '<col style="width:' + ((w / total) * 100).toFixed(1) + '%">').join("") +
      "</colgroup>";
  },

  _section(c, items, retired, bulk, autosave, rowClass) {
    const head = this._columns(c).map((group) => "<th>" + esc(group[0].label) + "</th>")
      .join("") + (this._hasActions(c, retired) ? "<th></th>" : "");
    const span = this._columns(c).length + (this._hasActions(c, retired) ? 1 : 0);
    const body = items.length
      ? items.map((it) => this._row(c, it, retired, autosave, rowClass)).join("")
      : '<tr><td colspan="' + span + '" class="empty">None.</td></tr>';
    const form = retired ? "" : (bulk ? this._bulkAddForm(c) : this._addForm(c));
    return '<div class="section-header">' + esc(c.label) + "</div>" +
      // The table gets a minimum width and the wrapper scrolls. A register with six
      // columns cannot be squeezed into a narrow pane without the selects and dates
      // collapsing to a few pixels; better to scroll sideways than to show a verdict
      // column too narrow to read the verdict in.
      '<div class="table-scroll"><table style="table-layout:fixed">' +
      this._colgroup(c, retired) +
      "<thead><tr>" + head + "</tr></thead><tbody>" + body +
      "</tbody></table></div>" + form;
  },
};
