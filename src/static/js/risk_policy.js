// Copyright (c) 2022-2026 MKM Research Labs. Licensed under the MIT License; see LICENSE.

// The Admin -> Risk policy editor. Per division, the user defines the three risk
// dimensions (Materiality, Complexity, Mission Criticality), the overall risk ratings,
// and — generated from those — one Materiality x Complexity grid per Mission-Criticality
// band whose cells map to a rating. Every band is {name, colour, explanation, score}.
// Edits auto-save as a DRAFT proposed to the division's MRC; a division's models keep
// using its last approved (or the firm-wide seed) policy until the MRC signs the draft off.
const RiskEditor = {
  _division: null, _divisions: [], _policy: null, _state: "seed", _box: null,

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
    this._box.innerHTML =
      '<div class="row" style="justify-content:space-between;align-items:center">' +
      '<div class="row" style="align-items:center;gap:8px"><label class="muted" style="font-size:11px">Division</label>' +
      divSel + '</div><div id="rp-status"></div></div>' +
      '<p class="lead muted" style="font-size:12px;max-width:74ch">Define this division\'s risk ' +
      "vocabulary. Edits save as a draft and are proposed to the division's MRC — models keep " +
      "using the last approved (or firm-wide seed) policy until the committee signs it off.</p>" +
      '<div id="rp-dims"></div>' +
      '<div class="section-header" style="margin-top:18px">Overall risk ratings</div>' +
      '<p class="muted" style="font-size:11px">The ratings a model can carry. The score is the ' +
      "completeness-audit escalation multiplier.</p><div id=\"rp-ratings\"></div>" +
      '<div class="section-header" style="margin-top:18px">Risk tables</div>' +
      '<p class="muted" style="font-size:11px">Generated from the dimensions — one ' +
      "Materiality × Complexity table per Mission-Criticality band. Pick each cell's rating.</p>" +
      '<div id="rp-grids"></div>' +
      '<div class="section-header" style="margin-top:18px">Policy document</div>' +
      '<p class="muted" style="font-size:11px">The formal written risk policy for this ' +
      "division (PDF or Word), sent to the MRC alongside the configuration above.</p>" +
      '<div class="row" style="align-items:center;gap:10px"><span id="rp-doc-current"></span>' +
      '<input type="file" id="rp-doc-file" accept=".pdf,.doc,.docx">' +
      '<button class="btn small" id="rp-doc-upload">Upload</button></div>';
    document.getElementById("rp-div").onchange = (e) => {
      this._division = e.target.value; this._load();
    };
    this._drawStatus();
    this._drawDims();
    this._drawRatings();
    this._drawGrids();
    this._drawDocument();
  },

  _drawDocument() {
    const el = document.getElementById("rp-doc-current");
    if (el) {
      el.innerHTML = this._document
        ? '<a href="/api/risk-policy/' + encodeURIComponent(this._division) +
          '/document" target="_blank">↓ ' + esc(this._document.original_name) + "</a>"
        : '<span class="muted">None uploaded.</span>';
    }
    const btn = document.getElementById("rp-doc-upload");
    if (btn) btn.onclick = () => this._uploadDocument();
  },

  _uploadDocument() {
    const file = document.getElementById("rp-doc-file");
    if (!file.files.length) { App.toast("Choose a file first", "error"); return; }
    const form = new FormData();
    form.append("file", file.files[0]);
    fetch("/api/risk-policy/" + encodeURIComponent(this._division) + "/document", {
      method: "POST", headers: { "X-Auth-Request-User": App.actor() }, body: form,
    }).then(async (res) => {
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || "upload failed"); }
      App.toast("Policy document uploaded", "ok");
      this._load();
    }).catch((e) => App.toast(e.message, "error"));
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

  _dimKeys() {
    return [["mission_criticality", "Mission Criticality"], ["materiality", "Materiality"],
            ["complexity", "Complexity"]];
  },

  _drawDims() {
    const host = document.getElementById("rp-dims");
    host.innerHTML = this._dimKeys().map(([key]) => {
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
      '<td style="text-align:center"><button class="edit-btn" data-remove="' + i +
      '" data-rscope="' + scope + '">✕</button></td></tr>').join("");
    const label = isRating ? "rating" : "band";
    return '<table><thead><tr><th style="width:160px">Name</th><th style="width:60px">Colour</th>' +
      "<th>Explanation</th><th style=\"width:90px;text-align:right\">" + scoreHead +
      '</th><th style="width:40px"></th></tr></thead><tbody>' + rows + "</tbody></table>" +
      '<div style="margin-top:6px"><button class="btn small" data-add="' + scope + '">+ Add ' +
      label + "</button></div>";
  },

  // Bind a scale's inputs. group is "dim" (all dimension tables) or "rating".
  _bindScale(group) {
    const host = document.getElementById(group === "rating" ? "rp-ratings" : "rp-dims");
    host.querySelectorAll("tr[data-scope]").forEach((tr) => {
      const bands = this._bandsFor(tr.getAttribute("data-scope"));
      const band = bands[Number(tr.getAttribute("data-i"))];
      tr.querySelectorAll("[data-f]").forEach((inp) => {
        inp.onchange = () => {
          const f = inp.getAttribute("data-f");
          band[f] = f === "score" ? this._num(inp.value) : inp.value;
          // A name change reshapes the grid; colour/score/explanation do not.
          if (f === "name") { this._save(); this._drawGrids(); } else { this._save(); }
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
    document.getElementById("rp-grids").innerHTML =
      '<div style="display:flex;flex-wrap:wrap;gap:22px">' +
      p.dimensions.mission_criticality.bands.map((b) =>
        '<div><div class="grid-cap" style="font-size:11px;font-weight:700;text-transform:uppercase;' +
        'color:var(--muted);margin-bottom:6px">' + esc(b.name) + "</div>" +
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
