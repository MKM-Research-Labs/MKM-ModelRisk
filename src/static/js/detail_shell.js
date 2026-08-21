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

  // "retired — read only", shown on a record that can no longer be edited. Retirement
  // itself lives on the Danger tab; this is only the flag.
  retiredFlag(retired) {
    return retired
      ? '<div style="margin-top:14px"><span class="pill">retired — read only</span></div>' : "";
  },
};
