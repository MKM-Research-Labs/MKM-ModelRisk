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

// Admin > Misc: the settings that are one institution's own words rather than
// platform behaviour — the wording every generated PDF carries (classification
// banner, "prepared by" line, title-page legal notice) and the document tag
// taxonomy. They shipped as constants in config/reporting.py, which meant an
// adopter had to edit code to stop publishing MKM Research Labs' notice on its
// own model documentation; they are edited here instead, through the same
// confirm-to-amend flow as everything else.
const AdminMisc = {
  _container: null,

  // The settings the PDF house style reads, in the order they appear on a page:
  // the banner, then the author line beneath it, then the notice at the foot.
  _REPORT_KEYS: ["report_classification", "report_author", "report_legal_notice"],

  async render(container) {
    this._container = container;
    const s = await App.get("/api/mrc/settings");
    const misc = s.specs.filter((f) => f.group === "misc");
    const report = this._REPORT_KEYS
      .map((k) => misc.find((f) => f.key === k)).filter(Boolean);
    const other = misc.filter((f) => this._REPORT_KEYS.indexOf(f.key) < 0);
    container.innerHTML =
      '<div class="section-header">Report wording</div>' +
      '<p class="muted">Printed on every PDF this platform generates &mdash; the Meeting Pack, ' +
      "Model Risk Report, model and product documents, audit reports and client packs. " +
      "The classification banner heads the title page and repeats in the page footer; " +
      "the legal notice sits at the foot of the title page and covers the contents of " +
      "the document, not the software that produced it &mdash; leave a blank line between " +
      "its paragraphs. Save a field empty to drop that line from your documents.</p>" +
      this._rows(s, report) +
      (other.length
        ? '<div class="section-header" style="margin-top:var(--space-8)">Documents</div>' +
          '<p class="muted">The comma-separated tag taxonomy offered on the Documents tab.</p>' +
          this._rows(s, other)
        : "");
    this._bind(s, misc);
  },

  _rows(s, specs) {
    return specs.map((f) =>
      '<div class="inforow" id="mrow-' + f.key + '"><div class="k">' + esc(f.label) +
      '</div><div class="v" style="white-space:pre-wrap">' + fieldDisplay(s.fields[f.key]) +
      '</div><span class="edit-btn" data-med="' + f.key + '">edit</span></div>').join("");
  },

  _bind(s, specs) {
    const byKey = {};
    specs.forEach((f) => { byKey[f.key] = f; });
    this._container.querySelectorAll("[data-med]").forEach((btn) => {
      const key = btn.getAttribute("data-med");
      btn.onclick = () => this._edit(byKey[key], s.fields[key]);
    });
  },

  _edit(f, current) {
    const row = document.getElementById("mrow-" + f.key);
    row.innerHTML = '<div class="k">' + esc(f.label) + '</div><div class="editor" style="flex:1">' +
      inputControl("misc-input", f) + '<button class="btn small primary" id="misc-save">Save&hellip;</button>' +
      '<button class="btn small" id="misc-cancel">Cancel</button></div>';
    const input = document.getElementById("misc-input");
    if (current !== null && current !== undefined) input.value = current;
    document.getElementById("misc-cancel").onclick = () => this.render(this._container);
    document.getElementById("misc-save").onclick = () => {
      // The legal notice runs to paragraphs, so the summary names the setting
      // rather than quoting a value that would fill the confirm dialog.
      App.amend("Set " + f.label + ".", "POST", "/api/mrc/settings/field",
        { field: f.key, value: input.value.trim() }, () => this.render(this._container));
    };
  },
};
