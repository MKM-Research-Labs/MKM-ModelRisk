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

// The Admin -> Risk policy editor. Per division, the user defines the three risk
// dimensions (Materiality, Complexity, Mission Criticality), the overall risk ratings,
// and — generated from those — one Materiality x Complexity grid per Mission-Criticality
// band whose cells map to a rating. Every band is {name, colour, explanation, score}.
// Edits auto-save as a DRAFT proposed to the division's MRC; a division's models keep
// using its last approved (or the firm-wide seed) policy until the MRC signs the draft off.
const RiskEditor = {
  _division: null, _divisions: [], _policy: null, _state: "seed", _box: null,
  _sub: "dimensions",   // active sub-tab: dimensions | ratings | grids

  async render(container) {
    this._box = container;
    const reg = await App.get("/api/risk-policy");
    this._divisions = Object.keys(reg.divisions || {});
    if (!this._division || this._divisions.indexOf(this._division) < 0) {
      this._division = this._divisions[0] || null;
    }
    await this._load();
  },

  async _load() {
    if (!this._division) {
      this._box.innerHTML = '<div class="empty">No divisions defined yet — add one under the ' +
        "Division tab, then define its risk policy here.</div>";
      return;
    }
    const detail = await App.get("/api/risk-policy/" + encodeURIComponent(this._division));
    this._state = detail.state;
    this._document = detail.document || null;
    // Edit the pending draft if there is one, otherwise start from the live policy.
    this._policy = JSON.parse(JSON.stringify(detail.draft || detail.live));
    this._draw();
  },

  async _save() {
    this._rebuildGrid();
    const status = document.getElementById("rp-status");
    if (status) status.innerHTML = '<span class="muted">Saving…</span>';
    try {
      const res = await App.send("POST",
        "/api/risk-policy/" + encodeURIComponent(this._division) + "/propose",
        { policy: this._policy, confirmed: true });
      this._state = res.state;
      this._drawStatus();
    } catch (e) {
      if (status) status.innerHTML = '<span style="color:var(--red)">Not saved: ' +
        esc(e.message || String(e)) + "</span>";
    }
  },

  // One Materiality x Complexity grid per Mission-Criticality band, covering every cell,
  // keeping existing assignments and defaulting new cells to the first rating.
  _rebuildGrid() {
    const p = this._policy;
    const names = (k) => p.dimensions[k].bands.map((b) => b.name);
    const def = (p.risk_ratings[0] || {}).name || "";
    const valid = p.risk_ratings.map((r) => r.name);
    const old = p.grid || {};
    const grid = {};
    names("mission_criticality").forEach((m) => {
      grid[m] = {};
      names("materiality").forEach((a) => names("complexity").forEach((c) => {
        const key = a + "|" + c;
        const prev = old[m] && old[m][key];
        grid[m][key] = (prev && valid.indexOf(prev) >= 0) ? prev : def;
      }));
    });
    p.grid = grid;
  },

  _nextScore(bands) {
    return bands.reduce((mx, b) => Math.max(mx, Number(b.score) || 0), 0) + 1;
  },

  // ---- rendering -----------------------------------------------------------
  _draw() {
    const divSel = '<select id="rp-div">' + this._divisions.map((d) =>
      '<option' + (d === this._division ? " selected" : "") + ">" + esc(d) + "</option>").join("") +
      "</select>";
    const sub = (k, label) => '<button class="dtab' + (this._sub === k ? " active" : "") +
      '" data-rp-sub="' + k + '">' + label + "</button>";
    this._box.innerHTML =
      '<div class="row" style="justify-content:space-between;align-items:center">' +
      '<div class="row" style="align-items:center;gap:8px"><label class="muted" style="font-size:11px">Division</label>' +
      divSel + '<a href="/api/risk-policy/' + encodeURIComponent(this._division) +
      '/categorisation.pdf" target="_blank" style="font-size:12px">↓ Categorisation PDF</a></div>' +
      '<div id="rp-status"></div></div>' +
      '<p class="lead muted" style="font-size:12px;max-width:74ch">Define this division\'s risk ' +
      "vocabulary. Edits save as a draft and are proposed to the division's MRC — models keep " +
      "using the last approved (or firm-wide seed) policy until the committee signs it off.</p>" +
      // Three sub-tabs, matching the Admin mockup: Dimensions | Risk Ratings | Risk Tables.
      '<div class="dtabs" id="rp-subtabs">' + sub("dimensions", "Dimensions") +
      sub("ratings", "Risk Ratings") + sub("grids", "Risk Tables") + "</div>" +
      '<section data-rp="dimensions"><p class="muted" style="font-size:11px">Each dimension ' +
      "is an ordered set of bands — set each band's name, colour, explanation and score, and " +
      'add or remove bands as the division needs.</p><div id="rp-dims"></div></section>' +
      '<section data-rp="ratings"><p class="muted" style="font-size:11px">The ratings a model ' +
      "can carry. The score is the completeness-audit escalation multiplier.</p>" +
      '<div id="rp-ratings"></div></section>' +
      '<section data-rp="grids"><p class="muted" style="font-size:11px">Generated from the ' +
      "dimensions — one " + esc(this._dimName("materiality")) + " × " +
      esc(this._dimName("complexity")) + " table per " +
      esc(this._dimName("mission_criticality")) + " band. Pick each cell\'s rating." +
      '</p><div id="rp-grids"></div></section>' +
      // The written policy document now lives on Documents -> Artefacts, filed on its
      // division's shelf with the rest of what that division issues. This tab configures
      // the categorisation; it is no longer also a filing cabinet.
      '<p class="muted" style="font-size:11px;margin-top:18px">The division\'s formal ' +
      "written Risk Policy document is filed under Documents &rarr; Artefacts, on the " +
      esc(this._division) + " shelf.</p>";
    document.getElementById("rp-div").onchange = (e) => {
      this._division = e.target.value; this._load();
    };
    this._box.querySelectorAll("[data-rp-sub]").forEach((b) => {
      b.onclick = () => { this._sub = b.getAttribute("data-rp-sub"); this._showSub(); };
    });
    this._drawStatus();
    this._drawDims();
    this._drawRatings();
    this._drawGrids();
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
    const el = document.getElementById("rp-status");
    if (!el) return;
    const map = {
      seed: ['<span class="muted">On the firm-wide seed — edits start a draft.</span>'],
      draft: ['<span class="badge" style="background:var(--amber)">Draft — awaiting MRC sign-off</span>'],
      approved: ['<span class="badge" style="background:var(--green)">Approved</span>' +
        '<span class="muted" style="margin-left:6px">edits start a new draft</span>'],
    };
    el.innerHTML = (map[this._state] || [""])[0];
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
        'border-radius:8px;padding:12px 14px;margin-bottom:12px">' +
        '<div class="row" style="align-items:center;gap:10px;margin-bottom:6px">' +
        '<label class="muted" style="font-size:10px;text-transform:uppercase">Dimension name</label>' +
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
      '<td><input data-f="colour" type="color" value="' + esc(b.colour || "#9e9e9e") +
      '" style="width:44px;height:28px;padding:2px"></td>' +
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
      '<div style="margin-top:6px"><button class="btn small" data-add="' + scope + '">+ Add ' +
      label + "</button></div>";
  },

  // Bind a scale's inputs. group is "dim" (all dimension tables) or "rating".
  _bindScale(group) {
    const host = document.getElementById(group === "rating" ? "rp-ratings" : "rp-dims");
    host.querySelectorAll("tr[data-scope]").forEach((tr) => {
      const bands = this._bandsFor(tr.getAttribute("data-scope"));
      const band = bands[Number(tr.getAttribute("data-i"))];
      const scope = tr.getAttribute("data-scope");
      tr.querySelectorAll("[data-f]").forEach((inp) => {
        inp.onchange = () => {
          const f = inp.getAttribute("data-f");
          if (f === "name") {
            // Carry the assignments onto the new name FIRST. The grid is keyed by band
            // name, so a rename otherwise reads as "old band deleted, new band added" and
            // _rebuildGrid fills the new one with the default rating — silently discarding
            // the table the division had built, under a name change nobody expects to
            // touch it.
            this._renameInGrid(scope, band.name, inp.value);
            band.name = inp.value;
            this._save();
            this._drawGrids();
            return;
          }
          band[f] = f === "score" ? this._num(inp.value) : inp.value;
          this._save();
        };
      });
    });
    host.querySelectorAll("[data-add]").forEach((btn) => {
      btn.onclick = () => {
        const bands = this._bandsFor(btn.getAttribute("data-add"));
        bands.push({ name: "New " + (group === "rating" ? "rating" : "band"),
                     colour: "#9e9e9e", explanation: "", score: this._nextScore(bands) });
        this._save();
        this._draw();
      };
    });
    host.querySelectorAll("[data-remove]").forEach((btn) => {
      btn.onclick = () => {
        const bands = this._bandsFor(btn.getAttribute("data-rscope"));
        if (bands.length <= 1) return;
        bands.splice(Number(btn.getAttribute("data-remove")), 1);
        this._save();
        this._draw();
      };
    });
    // Reorder a band within its scale — this is the axis order in the generated
    // grids and the badge sort order, independent of the score value.
    host.querySelectorAll("[data-move]").forEach((btn) => {
      btn.onclick = () => {
        const bands = this._bandsFor(btn.getAttribute("data-mscope"));
        const i = Number(btn.getAttribute("data-mi"));
        const j = btn.getAttribute("data-move") === "up" ? i - 1 : i + 1;
        if (j < 0 || j >= bands.length) return;
        const t = bands[i]; bands[i] = bands[j]; bands[j] = t;
        this._save();
        this._draw();
      };
    });
  },

  // Move a scale's assignments onto its new name. Each scale keys the grid differently: a
  // Mission-Criticality band names a whole table, Materiality and Complexity name the two
  // halves of every cell key, and a rating is the cell's VALUE.
  _renameInGrid(scope, from, to) {
    const grid = this._policy.grid || {};
    if (!from || !to || from === to) return;
    if (scope === "mission_criticality") {
      if (grid[from]) { grid[to] = grid[from]; delete grid[from]; }
      return;
    }
    if (scope === "risk_ratings") {
      Object.keys(grid).forEach((band) => Object.keys(grid[band]).forEach((cell) => {
        if (grid[band][cell] === from) grid[band][cell] = to;
      }));
      return;
    }
    // Cell key is "materiality|complexity" — rewrite the half this scale owns.
    const half = scope === "materiality" ? 0 : 1;
    Object.keys(grid).forEach((band) => {
      const renamed = {};
      Object.keys(grid[band]).forEach((cell) => {
        const parts = cell.split("|");
        if (parts[half] === from) parts[half] = to;
        renamed[parts.join("|")] = grid[band][cell];
      });
      grid[band] = renamed;
    });
  },

  _bandsFor(scope) {
    return scope === "risk_ratings" ? this._policy.risk_ratings
      : this._policy.dimensions[scope].bands;
  },

  _num(v) { const n = Number(v); return isNaN(n) ? v : n; },

  _drawGrids() {
    this._rebuildGrid();
    const p = this._policy;
    const mat = p.dimensions.materiality.bands.map((b) => b.name);
    const comp = p.dimensions.complexity.bands.map((b) => b.name);
    const colour = {}; p.risk_ratings.forEach((r) => { colour[r.name] = r.colour; });
    const opts = (sel) => p.risk_ratings.map((r) =>
      '<option' + (r.name === sel ? " selected" : "") + ">" + esc(r.name) + "</option>").join("");
    const rowsFor = (mc) => mat.slice().reverse().map((a) =>
      "<tr><th>" + esc(a) + "</th>" + comp.map((c) => {
        const rag = (p.grid[mc] || {})[a + "|" + c] || "";
        const bg = (colour[rag] || "#9e9e9e") + "22";
        return '<td class="hcell" style="background:' + bg + '"><select data-mc="' + esc(mc) +
          '" data-cell="' + esc(a + "|" + c) + '">' + opts(rag) + "</select></td>";
      }).join("") + "</tr>").join("");
    const mcLabel = this._dimName("mission_criticality");
    const bands = p.dimensions.mission_criticality.bands;
    document.getElementById("rp-grids").innerHTML =
      '<p class="muted" style="font-size:11px;margin:0 0 12px">' + bands.length +
      " tables — one per " + esc(mcLabel) + " band (rows = " +
      esc(this._dimName("materiality")) + ", columns = " +
      esc(this._dimName("complexity")) + ").</p>" +
      '<div style="display:flex;flex-wrap:wrap;gap:22px">' +
      bands.map((b) =>
        '<div><div class="grid-cap" style="display:flex;align-items:center;gap:8px;margin-bottom:6px">' +
        '<span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:' +
        esc(b.colour || "#9e9e9e") + '"></span>' +
        '<span style="font-size:10px;text-transform:uppercase;color:var(--muted);letter-spacing:.04em">' +
        esc(mcLabel) + "</span>" +
        '<span style="font-size:14px;font-weight:700;color:var(--text)">' + esc(b.name) + "</span></div>" +
        '<table class="heatmap"><thead><tr><th></th>' +
        comp.map((c) => "<th>" + esc(c) + "</th>").join("") + "</tr></thead><tbody>" +
        rowsFor(b.name) + "</tbody></table></div>").join("") + "</div>";
    this._box.querySelectorAll("#rp-grids select").forEach((sel) => {
      sel.onchange = () => {
        this._policy.grid[sel.getAttribute("data-mc")][sel.getAttribute("data-cell")] = sel.value;
        this._save();
        this._drawGrids();
      };
    });
  },
};
