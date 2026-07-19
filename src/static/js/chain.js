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

// The Model Chain ("string of pearls"): a read-only visualisation of the model
// dependency graph, derived from what each model declares on its Dependencies
// tab. Edges point in the direction data flows (producer -> consumer). The graph
// is guaranteed acyclic by the declaration-time guard, so longest-path layering
// always terminates.
const BOX_W = 130, BOX_H = 42, COL_GAP = 34, ROW_GAP = 52, PAD = 20;

const Chain = {
  async render() {
    const chain = await App.get("/api/models/chain");
    const panel = document.getElementById("tab-chain");
    const legend =
      '<div class="row" style="gap:18px;align-items:center;margin-bottom:10px;font-size:12px">' +
      '<span><span class="chain-swatch" style="background:#e3f2fd;border-color:#1976d2"></span> model in the chain</span>' +
      '<span><span class="chain-swatch" style="background:#e0f2f1;border-color:#00897b"></span> terminal output (no downstream)</span>' +
      '<span><span class="chain-swatch" style="background:#f5f5f5;border-color:#bbb"></span> hibernated</span>' +
      "</div>";
    panel.innerHTML =
      '<div class="card"><h3>Model Chain</h3>' +
      '<p class="muted">The string of pearls, derived from every model\'s declared ' +
      "dependencies. Arrows run producer &rarr; consumer. Declare links on a model\'s " +
      "Dependencies tab.</p>" + legend +
      '<div class="chain-canvas" style="overflow:auto">' + this._svg(chain) + "</div></div>";
  },

  // Longest-path layering: a node's rank is the longest chain of producers behind
  // it, so every edge points from a lower rank to a higher one and reads top-down.
  _rank(nodes, links) {
    const succ = {}, indeg = {};
    nodes.forEach((n) => { succ[n.model_id] = []; indeg[n.model_id] = 0; });
    links.forEach((l) => {
      if (succ[l.from] === undefined || indeg[l.to] === undefined) return;
      succ[l.from].push(l.to);
      indeg[l.to]++;
    });
    const rank = {}, queue = [];
    nodes.forEach((n) => { if (indeg[n.model_id] === 0) { rank[n.model_id] = 0; queue.push(n.model_id); } });
    while (queue.length) {
      const id = queue.shift();
      succ[id].forEach((to) => {
        rank[to] = Math.max(rank[to] || 0, rank[id] + 1);
        if (--indeg[to] === 0) queue.push(to);
      });
    }
    return rank;
  },

  _svg(chain) {
    const nodes = chain.nodes || [], links = chain.links || [];
    if (!nodes.length) return '<div class="empty">No models registered yet.</div>';
    const hasDownstream = {};
    links.forEach((l) => { hasDownstream[l.from] = true; });
    const rank = this._rank(nodes, links);
    // Group nodes by rank (row), preserving id order within a row.
    const rows = [];
    nodes.forEach((n) => {
      const r = rank[n.model_id] || 0;
      (rows[r] = rows[r] || []).push(n);
    });
    const widest = Math.max.apply(null, rows.map((r) => (r || []).length));
    const width = PAD * 2 + widest * BOX_W + (widest - 1) * COL_GAP;
    const height = PAD * 2 + rows.length * BOX_H + (rows.length - 1) * ROW_GAP;
    const pos = {};
    rows.forEach((row, r) => {
      if (!row) return;
      const rowW = row.length * BOX_W + (row.length - 1) * COL_GAP;
      const x0 = (width - rowW) / 2;
      row.forEach((n, i) => {
        pos[n.model_id] = { x: x0 + i * (BOX_W + COL_GAP), y: PAD + r * (BOX_H + ROW_GAP) };
      });
    });
    const edges = links.map((l) => {
      const a = pos[l.from], b = pos[l.to];
      if (!a || !b) return "";
      return '<line x1="' + (a.x + BOX_W / 2) + '" y1="' + (a.y + BOX_H) +
        '" x2="' + (b.x + BOX_W / 2) + '" y2="' + b.y +
        '" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#chain-arrow)"/>';
    }).join("");
    const boxes = nodes.map((n) => {
      const p = pos[n.model_id];
      let fill = "#e3f2fd", stroke = "#1976d2";
      if (!hasDownstream[n.model_id]) { fill = "#e0f2f1"; stroke = "#00897b"; }
      if (n.retired) { fill = "#f5f5f5"; stroke = "#bbb"; }
      return '<g>' +
        '<rect x="' + p.x + '" y="' + p.y + '" width="' + BOX_W + '" height="' + BOX_H +
        '" rx="7" fill="' + fill + '" stroke="' + stroke + '" stroke-width="1.5"' +
        (n.retired ? ' stroke-dasharray="4 3"' : "") + "/>" +
        '<text x="' + (p.x + BOX_W / 2) + '" y="' + (p.y + 17) +
        '" text-anchor="middle" font-size="11" font-weight="700" fill="#1f2937">' + esc(n.model_id) + "</text>" +
        '<text x="' + (p.x + BOX_W / 2) + '" y="' + (p.y + 31) +
        '" text-anchor="middle" font-size="9.5" fill="#4b5563">' + esc(this._short(n.name)) + "</text>" +
        "</g>";
    }).join("");
    return '<svg width="' + width + '" height="' + height + '" viewBox="0 0 ' + width + " " + height +
      '" xmlns="http://www.w3.org/2000/svg"><defs>' +
      '<marker id="chain-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" ' +
      'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10" fill="none" stroke="#94a3b8" ' +
      'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker></defs>' +
      edges + boxes + "</svg>";
  },

  _short(name) {
    const s = String(name || "");
    return s.length > 18 ? s.slice(0, 17) + "…" : s;
  },
};
