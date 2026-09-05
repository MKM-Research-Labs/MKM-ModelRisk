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
  _sub: "dimensions",   // active sub-tab: dimensions | ratings | grids | audit

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
                     colour: Theme.value("grey"), explanation: "", score: this._nextScore(bands) });
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
        const bg = (colour[rag] || Theme.value("grey")) + "22";
        return '<td class="hcell" style="background:' + bg + '"><select data-mc="' + esc(mc) +
          '" data-cell="' + esc(a + "|" + c) + '">' + opts(rag) + "</select></td>";
      }).join("") + "</tr>").join("");
    const mcLabel = this._dimName("mission_criticality");
    const bands = p.dimensions.mission_criticality.bands;
    document.getElementById("rp-grids").innerHTML =
      '<p class="muted" style="font-size:var(--size-xs);margin:0 0 var(--space-6)">' + bands.length +
      " tables — one per " + esc(mcLabel) + " band (rows = " +
      esc(this._dimName("materiality")) + ", columns = " +
      esc(this._dimName("complexity")) + ").</p>" +
      '<div style="display:flex;flex-wrap:wrap;gap:22px">' +
      bands.map((b) =>
        '<div><div class="grid-cap" style="display:flex;align-items:center;gap:var(--space-4);margin-bottom:var(--space-3)">' +
        '<span style="display:inline-block;width:12px;height:12px;border-radius:var(--radius-sm);background:' +
        esc(b.colour || Theme.value("grey")) + '"></span>' +
        '<span style="font-size:var(--size-xxs);text-transform:uppercase;color:var(--muted);letter-spacing:.04em">' +
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
