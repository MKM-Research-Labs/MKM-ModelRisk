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
// Shared scaffolding for the aggregate detail views (model, product, ML Application).
//
// These screens are the same shape -- a header, a tab bar, a content box -- and were
// three copies of that shape before this module. What differs between them is which
// tabs they carry and what each tab draws, which is what each screen still says for
// itself; what does not differ is the markup, so it is written once here.
//
// Kept deliberately small. A utility that tries to own the whole screen ends up with a
// parameter for every difference, and that is harder to read than the duplication was.
const DetailShell = {
  // The tab strip. ``tabs`` is [key, label, badge] triples -- a null badge renders no
  // count, which is how a tab with nothing to count (Overview, Risk) stays clean.
  // ``attr`` is the data attribute the screen binds its clicks to, so each detail view
  // keeps its own event namespace.
  tabBar(tabs, active, attr) {
    return '<div class="dtabs">' + tabs.map((t) => {
      const danger = t[0] === "danger" ? " dtab-danger" : "";
      return '<button class="dtab' + (t[0] === active ? " active" : "") + danger +
        '" ' + attr + '="' + t[0] + '">' +
        esc(t[1]) + (t[2] !== null && t[2] !== undefined ? " (" + t[2] + ")" : "") +
        "</button>";
    }).join("") + "</div>";
  },

  // A titled block of field rows. ``row`` is the screen's own row renderer, because
  // how a field is drawn (and whether it is editable in place) is the one thing these
  // screens genuinely disagree about.
  section(title, keys, row) {
    return '<div class="section-header">' + title + "</div>" + keys.map(row).join("");
  },

  // One inline field row: label, value, and an edit affordance where the record is
  // still editable. The markup is shared so every detail screen's rows are the same
  // shape -- which is what makes the editor below able to open on any of them.
  row(key, label, value, editable) {
    return '<div class="inforow" id="row-' + key + '"><div class="k">' + esc(label) +
      '</div><div class="v">' + value +
      (editable ? ' <span class="edit-btn" data-edit="' + key + '">edit</span>' : "") +
      "</div></div>";
  },

  // The value cell for the fields every detail screen renders the same way: the three
  // risk dimensions, and the MRC sign-off that shows its granting meeting. Returns null
  // where it has nothing particular to say, so a screen falls through to its own
  // handling — a product's status badge, a model's Owner-vs-Table RAG.
  //
  // A dimension is shown AS THE ADMIN DEFINED THE BAND (its colour, name and
  // explanation), never as the stored score: "Criticality 4" tells a reader nothing,
  // and the band it stands for is the whole point of the policy.
  fieldValue(key, spec, d) {
    if (key === "tier" && (d[key] || d[key] === 0)) {
      return tierBadge(d[key], d.division) + ' <span class="muted">' +
        esc(tierFullLabel(d[key], d.division)) + "</span>";
    }
    if ((key === "materiality" || key === "complexity") && d[key]) {
      return bandDisplay(spec, d[key], d.division);
    }
    if (key === "mrc_signoff_date" && d.mrc_signoff_meeting) {
      return '<span class="code">' + esc(d.mrc_signoff_meeting) + "</span>";
    }
    return null;
  },

  // The inline field editor, opened in place of a row.
  //
  // Three screens had their own copy of this and they differed in four things: which
  // panel to scope the row lookup to, an id prefix, whether there is a Save button or
  // the control saves on change, and what to do with the value. Those are the options;
  // everything else -- the band picker for risk dimensions, the tier score, the
  // heading suppression inside a risk-table cell -- is the same everywhere and is
  // written once here.
  //
  // ``scope`` matters: a model detail left rendered in a hidden panel carries rows
  // under the same ids, and a bare getElementById would hand back whichever the
  // document happens to hold first.
  fieldEditor(opts) {
    const f = opts.spec;
    if (!f) return null;
    const row = document.querySelector(opts.scope + " #row-" + f.key) ||
      document.getElementById("row-" + f.key);
    if (!row) return null;
    const inputId = opts.prefix + "-input";
    const picker = bandPicker(inputId, f, opts.division, opts.current);
    // In a risk table the target is a cell, which carries its own Dimension heading;
    // only an inforow needs the label repeated inside the editor.
    const heading = row.tagName === "TD"
      ? "" : '<div class="k">' + esc(riskFieldLabel(f, opts.division)) + "</div>";
    row.innerHTML = heading + '<div class="editor">' +
      (picker || inputControl(inputId, f, opts.division)) +
      (opts.withSave
        ? '<button class="btn small primary" id="' + opts.prefix + '-save">Save&hellip;</button>'
        : "") +
      '<button class="btn small" id="' + opts.prefix + '-cancel">Cancel</button></div>';
    const input = document.getElementById(inputId);
    if (picker) bindBandPicker(inputId);
    else if (opts.current !== null && opts.current !== undefined) input.value = opts.current;
    document.getElementById(opts.prefix + "-cancel").onclick = opts.onCancel;
    const commit = function () {
      // Tier stores the Mission-Criticality band SCORE (an integer), though the owner
      // picks it by band name.
      const value = f.type === "tier" ? parseInt(input.value, 10) : input.value.trim();
      opts.onSave(value, input.value);
    };
    if (opts.withSave) document.getElementById(opts.prefix + "-save").onclick = commit;
    else { input.onchange = commit; input.focus(); }
    return input;
  },

  // "retired — read only", shown on a record that can no longer be edited. Retirement
  // itself lives on the Danger tab; this is only the flag.
  retiredFlag(retired) {
    return retired
      ? '<div style="margin-top:var(--space-7)"><span class="pill">retired — read only</span></div>' : "";
  },
};
