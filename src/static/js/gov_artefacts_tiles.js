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

// An artefact drawn as a tile: the institution's own shelf, the platform's, and the
// note under each saying what it is for.
//
// Split from gov_artefacts.js, which owns the panel around them — the shelf picker, the
// upload, and the blurb. A tile rather than a table row because what the
// institution ISSUES is a thing you pick up: a Terms of Reference or a presentation is
// opened, not scanned down a column.
//
// The platform tiles are the ones that are not the institution's. They are what ships
// with the console, and they are shown beside an adopter's own so that an empty shelf
// reads as "you have not filed yours yet" rather than as "there is nothing here".
//
// Assigns onto GovArtefacts; loads after gov_artefacts.js.

Object.assign(GovArtefacts, {

  _tiles() {
    const own = (this._artefacts[this._shelf] || []).map((a) => this._tile({
      title: a.original_name, kind: a.category || "Other",
      note: a.description,
      links: [["Open", "/api/artefacts/" + encodeURIComponent(this._shelf) + "/" +
               esc(a.item_id) + "/download?inline=1"],
              ["Download", "/api/artefacts/" + encodeURIComponent(this._shelf) + "/" +
               esc(a.item_id) + "/download"]],
      remove: a.item_id,
    })).join("");
    const platform = this._platformTiles();
    return (platform + own) ||
      '<div class="empty">Nothing filed on this shelf yet.</div>';
  },

  // Artefacts the platform produces rather than an adopter uploading them: the user
  // guide (company-wide) and each division's risk policy document.
  _platformTiles() {
    if (this._shelf === (this._shelves[0] || "")) {
      return this._tile({
        title: "User Guide", kind: "Guide",
        note: "Generated from the platform's own documentation. Published in both forms " +
              "so it can be read as issued or marked up by your own people.",
        links: [["PDF", "/api/audit-reports/user_guide.pdf"],
                ["Word", "/api/audit-reports/user_guide.docx"]],
      });
    }
    return this._tile({
      title: this._shelf + " Risk Policy",
      kind: "Policy",
      note: "The division's formal written risk policy, sent to its MRC alongside the " +
            "categorisation. Uploaded here; the categorisation itself stays in Admin.",
      links: [["Open", "/api/risk-policy/" + encodeURIComponent(this._shelf) + "/document"]],
      upload: "policy",
    });
  },

  _tile(t) {
    const links = t.links.map(([label, href]) =>
      '<a class="btn small" href="' + href + '" target="_blank" rel="noopener">' +
      esc(label) + "</a>").join(" ");
    const remove = t.remove
      ? ' <button class="btn small danger" data-ga-rm="' + esc(t.remove) + '">Remove</button>'
      : "";
    const upload = t.upload === "policy"
      ? '<div class="row" style="margin-top:var(--space-4)"><input type="file" id="gp-file">' +
        '<button class="btn small" id="gp-upload">Replace</button></div>'
      : "";
    return '<div class="tile"><div class="tile-kind">' + esc(t.kind) + "</div>" +
      '<div class="tile-title">' + esc(t.title) + "</div>" +
      (t.note ? '<div class="tile-note">' + esc(t.note) + "</div>" : "") +
      '<div class="row" style="margin-top:var(--space-4)">' + links + remove + "</div>" +
      upload + "</div>";
  },
});
