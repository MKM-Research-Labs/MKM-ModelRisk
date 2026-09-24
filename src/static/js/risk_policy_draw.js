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
// Drawing the risk policy: the grid, the dimensions and the band tables.
//
// What the division's policy currently says, rendered. Editing it -- rebuilding the
// grid, renaming a band, rescaling a dimension -- stays in risk_policy.js, because
// drawing must keep working when an edit is refused, and the two are read separately.
//
// Every band table reads in one direction: a value BELOW the bound. Writing one
// good-first is how 95% stability once came out red.
//
// Assigns onto RiskEditor; loads after risk_policy.js.

Object.assign(RiskEditor, {

  // ---- rendering -----------------------------------------------------------
  _draw() {
    const sub = (k, label) => '<button class="dtab' + (this._sub === k ? " active" : "") +
      '" data-rp-sub="' + k + '">' + label + "</button>";
    this._box.innerHTML =
      PolicyEditor.header("rp", this._divisions, this._division,
        '<a href="/api/risk-policy/' + encodeURIComponent(this._division) +
        '/categorisation.pdf" target="_blank" style="font-size:var(--size-sm)">' +
        "↓ Categorisation PDF</a>") +
      '<p class="lead muted" style="font-size:var(--size-sm);max-width:74ch">Define this division\'s risk ' +
      "vocabulary. Edits save as a draft and are proposed to the division's MRC — models keep " +
      "using the last approved (or firm-wide seed) policy until the committee signs it off.</p>" +
      // Three sub-tabs, matching the Admin mockup: Dimensions | Risk Ratings | Risk Tables.
      '<div class="dtabs" id="rp-subtabs">' + sub("dimensions", "Dimensions") +
      sub("ratings", "Risk Ratings") + sub("grids", "Risk Tables") +
      sub("audit", "Audit") + "</div>" +
      '<section data-rp="dimensions"><p class="muted" style="font-size:var(--size-xs)">Each dimension ' +
      "is an ordered set of bands — set each band's name, colour, explanation and score, and " +
      'add or remove bands as the division needs.</p><div id="rp-dims"></div></section>' +
      '<section data-rp="ratings"><p class="muted" style="font-size:var(--size-xs)">The ratings a model ' +
      "can carry. The score is the completeness-audit escalation multiplier.</p>" +
      '<div id="rp-ratings"></div></section>' +
      '<section data-rp="grids"><p class="muted" style="font-size:var(--size-xs)">Generated from the ' +
      "dimensions — one " + esc(this._dimName("materiality")) + " × " +
      esc(this._dimName("complexity")) + " table per " +
      esc(this._dimName("mission_criticality")) + " band. Pick each cell\'s rating." +
      '</p><div id="rp-grids"></div></section>' +
      '<section data-rp="audit"><div id="rp-audit"></div><div id="rp-weights"></div></section>' +
      // The written policy document now lives on Documents -> Artefacts, filed on its
      // division's shelf with the rest of what that division issues. This tab configures
      // the categorisation; it is no longer also a filing cabinet.
      '<p class="muted" style="font-size:var(--size-xs);margin-top:var(--space-9)">The division\'s formal ' +
      "written Risk Policy document is filed under Documents &rarr; Artefacts, on the " +
      esc(this._division) + " shelf.</p>";
    PolicyEditor.bindDivision("rp", (d) => { this._division = d; this._load(); });
    this._box.querySelectorAll("[data-rp-sub]").forEach((b) => {
      b.onclick = () => { this._sub = b.getAttribute("data-rp-sub"); this._showSub(); };
    });
    this._drawStatus();
    this._drawDims();
    this._drawRatings();
    this._drawGrids();
    // The audit panel edits the same draft and saves through the same path, so it
    // reaches the MRC with the rest of the policy rather than as a setting of its own.
    RiskPolicyAudit.render(document.getElementById("rp-audit"), this._policy,
                           () => this._save());
    RiskPolicyWeights.render(document.getElementById("rp-weights"), this._policy,
                             this._weights, () => this._save());
    this._showSub();
  },

  // Show the active sub-tab's section, hide the others. `this._sub` survives the
  // full re-renders triggered by adding/removing bands, so the tab stays put.
  _showSub() {
    const active = this._sub || "dimensions";
    this._box.querySelectorAll("[data-rp-sub]").forEach((b) => {
      b.classList.toggle("active", b.getAttribute("data-rp-sub") === active);
    });
    this._box.querySelectorAll("[data-rp]").forEach((s) => {
      s.hidden = s.getAttribute("data-rp") !== active;
    });
  },

  _drawStatus() {
    PolicyEditor.status("rp", this._state,
      "On the firm-wide seed — edits start a draft.");
  },

  // The three dimensions are structural — the heatmap is one grid per band of the
  // first, across the other two — but what they are CALLED is the division's, and is
  // read from the policy being edited. Nothing here spells a dimension out.
  _dimKeys() {
    return ["mission_criticality", "materiality", "complexity"];
  },

  _dimName(key) {
    const dim = (this._policy.dimensions || {})[key] || {};
    return dim.label || key.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
  },

  _drawDims() {
    const host = document.getElementById("rp-dims");
    host.innerHTML = this._dimKeys().map((key) => {
      const dim = this._policy.dimensions[key];
      return '<div class="dim" data-dim="' + key + '" style="border:1px solid var(--line);' +
        'border-radius:var(--radius-lg);padding:var(--space-6) var(--space-7);margin-bottom:var(--space-6)">' +
        '<div class="row" style="align-items:center;gap:var(--space-5);margin-bottom:var(--space-3)">' +
        '<label class="muted" style="font-size:var(--size-xxs);text-transform:uppercase">Dimension name</label>' +
        '<input data-dimname="' + key + '" value="' + esc(dim.label) +
        '" style="font-weight:700;width:220px"></div>' +
        this._bandTable(key, dim.bands, false) + "</div>";
    }).join("");
    this._bindScale("dim");
    this._box.querySelectorAll("[data-dimname]").forEach((inp) => {
      inp.onchange = () => {
        this._policy.dimensions[inp.getAttribute("data-dimname")].label = inp.value.trim();
        this._save();
      };
    });
  },

  _drawRatings() {
    document.getElementById("rp-ratings").innerHTML =
      this._bandTable("risk_ratings", this._policy.risk_ratings, true);
    this._bindScale("rating");
  },

  _bandTable(scope, bands, isRating) {
    const scoreHead = isRating ? "Score / multiplier" : "Score";
    const rows = bands.map((b, i) =>
      '<tr data-scope="' + scope + '" data-i="' + i + '">' +
      '<td><input data-f="name" value="' + esc(b.name) + '" style="font-weight:600;width:150px"></td>' +
      '<td><input data-f="colour" type="color" value="' + esc(b.colour || Theme.value("grey")) +
      '" style="width:44px;height:28px;padding:var(--space-1)"></td>' +
      '<td><textarea data-f="explanation" rows="3" style="width:100%;resize:vertical;overflow-y:auto">' +
      esc(b.explanation || "") + "</textarea></td>" +
      '<td><input data-f="score" value="' + esc(b.score) +
      '" style="width:80px;text-align:right"></td>' +
      '<td style="text-align:center;white-space:nowrap">' +
      '<button class="edit-btn" data-move="up" data-mi="' + i + '" data-mscope="' + scope +
      '" title="Move up"' + (i === 0 ? " disabled" : "") + ">↑</button>" +
      '<button class="edit-btn" data-move="down" data-mi="' + i + '" data-mscope="' + scope +
      '" title="Move down"' + (i === bands.length - 1 ? " disabled" : "") + ">↓</button>" +
      '<button class="edit-btn" data-remove="' + i +
      '" data-rscope="' + scope + '" title="Remove">✕</button></td></tr>').join("");
    const label = isRating ? "rating" : "band";
    return '<table><thead><tr><th style="width:160px">Name</th><th style="width:60px">Colour</th>' +
      "<th>Explanation</th><th style=\"width:90px;text-align:right\">" + scoreHead +
      '</th><th style="width:76px"></th></tr></thead><tbody>' + rows + "</tbody></table>" +
      '<div style="margin-top:var(--space-3)"><button class="btn small" data-add="' + scope + '">+ Add ' +
      label + "</button></div>";
  },
});
