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
  _tab: "chain",

  async render() {
    const [chain, handoffs] = await Promise.all([
      App.get("/api/models/chain"), App.get("/api/handoffs"),
    ]);
    this._chain = chain;
    this._byId = {};
    handoffs.forEach((h) => { this._byId[h.handoff_id] = h; });
    // Split the models into the three views. A model is *in a chain* only if it
    // takes part in at least one edge; a model with no declared dependency at all
    // is isolated and shows in none of these views (it is not part of any chain).
    // Of the in-chain models, one with no consumer is a terminal output; a retired
    // model is hibernated (retirement wins, mirroring how the graph greys it out).
    const nodes = chain.nodes || [], links = chain.links || [];
    const hasDownstream = {}, inChain = new Set();
    links.forEach((l) => { hasDownstream[l.from] = true; inChain.add(l.from); inChain.add(l.to); });
    this._chainNodes = nodes.filter((n) => inChain.has(n.model_id));
    this._terminal = this._chainNodes.filter((n) => !n.retired && !hasDownstream[n.model_id]);
    this._hibernated = nodes.filter((n) => n.retired);
    this._draw();
  },

  _draw() {
    const tabs = [["chain", "Chain", this._chainNodes.length],
                  ["terminal", "Terminal", this._terminal.length],
                  ["hibernated", "Hibernated", this._hibernated.length]];
    const bar = '<div class="dtabs">' + tabs.map((t) =>
      '<button class="dtab' + (t[0] === this._tab ? " active" : "") +
      '" data-ctab="' + t[0] + '">' + t[1] + " (" + t[2] + ")</button>").join("") + "</div>";
    let body;
    if (this._tab === "terminal") {
      body = this._list(this._terminal, "Terminal outputs — models with no downstream " +
        "consumer. These are the ends of the string of pearls.");
    } else if (this._tab === "hibernated") {
      body = this._list(this._hibernated, "Hibernated (retired) models, kept for history. " +
        "They stay in the chain, greyed out.");
    } else {
      body = this._chainBody();
    }
    document.getElementById("tab-chain").innerHTML =
      '<div class="card"><h3>Model Chain</h3>' +
      '<p class="muted">The string of pearls, derived from every model\'s declared ' +
      "dependencies. Arrows run producer &rarr; consumer. Declare links on a model\'s " +
      "Dependencies tab.</p>" + bar + body + "</div>" +
      '<div id="chain-handoff"></div>';
    this._bind();
  },

  _chainBody() {
    const legend =
      '<div class="row" style="gap:18px;align-items:center;margin-bottom:10px;font-size:12px">' +
      '<span><span class="chain-swatch" style="background:#e3f2fd;border-color:#1976d2"></span> model in the chain</span>' +
      '<span><span class="chain-swatch" style="background:#e0f2f1;border-color:#00897b"></span> terminal output (no downstream)</span>' +
      '<span><span class="chain-swatch" style="background:#f5f5f5;border-color:#bbb"></span> hibernated</span>' +
      "</div>";
    // The graph shows only models that are in a chain (in at least one edge).
    const graph = { nodes: this._chainNodes, links: this._chain.links || [] };
    return legend + '<div class="chain-canvas" style="overflow:auto">' + this._svg(graph) + "</div>" +
      this._edges(this._chain, this._byId);
  },

  // A plain vertical list of models (Terminal / Hibernated tabs). Each row opens
  // the model on the Models tab.
  _list(models, blurb) {
    const intro = '<p class="muted">' + blurb + "</p>";
    if (!models.length) return intro + '<div class="empty">None.</div>';
    const rows = models.map((m) =>
      '<div class="chain-item" data-open="' + esc(m.model_id) + '">' +
      '<span class="chain-item-id">' + esc(m.model_id) + "</span>" +
      '<span class="chain-item-name">' + esc(m.name || "") + "</span></div>").join("");
    return intro + '<div class="chain-list">' + rows + "</div>";
  },

  _bind() {
    document.querySelectorAll("[data-ctab]").forEach((b) => {
      b.onclick = () => { this._tab = b.getAttribute("data-ctab"); this._draw(); };
    });
    document.querySelectorAll("[data-open]").forEach((row) => {
      row.onclick = async () => {
        const id = row.getAttribute("data-open");
        await Nav.show("inventory");
        // Always land on Overview: Detail remembers the last tab it showed.
        if (typeof Detail !== "undefined") Detail.show(id, "overview");
      };
    });
    this._bindEdges();
  },

  // Each edge, with its handoff's field-lineage count, and a button to open the
  // handoff editor (field lineage + compatibility note).
  _edges(chain, byId) {
    const links = chain.links || [];
    if (!links.length) return "";
    const rows = links.map((l) => {
      const h = byId[l.from + "~" + l.to];
      const count = h ? (h.data.field_lineage || []).length : 0;
      const status = h ? esc(h.data.status || "Draft") : "not defined";
      return "<tr><td><b>" + esc(l.from) + "</b> &rarr; <b>" + esc(l.to) + "</b></td>" +
        "<td>" + status + "</td><td>" + count + " field" + (count === 1 ? "" : "s") + "</td>" +
        '<td><button class="btn small" data-edge="' + esc(l.from) + "|" + esc(l.to) +
        '">' + (h ? "Edit handoff" : "Define handoff") + "</button></td></tr>";
    }).join("");
    return '<div class="section-header" style="margin-top:16px">Handoffs</div>' +
      '<p class="muted">Each edge can carry the field lineage that crosses it and a ' +
      "compatibility note the MRC reviews.</p>" +
      "<table><thead><tr><th>Edge</th><th>Status</th><th>Field lineage</th><th></th></tr></thead>" +
      "<tbody>" + rows + "</tbody></table>";
  },

  _bindEdges() {
    document.querySelectorAll("[data-edge]").forEach((btn) => {
      btn.onclick = () => {
        const parts = btn.getAttribute("data-edge").split("|");
        Handoffs.open(parts[0], parts[1], () => this.render());
      };
    });
    // Clicking an arrow in the diagram opens that edge's handoff editor — the
    // same action as its "Edit handoff" button in the table below.
    document.querySelectorAll("[data-edge-line]").forEach((g) => {
      g.onclick = () => {
        const parts = g.getAttribute("data-edge-line").split("|");
        Handoffs.open(parts[0], parts[1], () => this.render());
      };
    });
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
    // Each edge is drawn twice: a wide, invisible line that gives a comfortable
    // click target, and the visible arrow on top. Clicking either jumps to (and
    // flashes) that edge's row in the Handoffs table below.
    const edges = links.map((l) => {
      const a = pos[l.from], b = pos[l.to];
      if (!a || !b) return "";
      const x1 = a.x + BOX_W / 2, y1 = a.y + BOX_H, x2 = b.x + BOX_W / 2, y2 = b.y;
      return '<g class="chain-edge" data-edge-line="' + esc(l.from) + "|" + esc(l.to) + '">' +
        "<title>" + esc(l.from) + " → " + esc(l.to) + " — open handoff</title>" +
        '<line class="chain-edge-hit" x1="' + x1 + '" y1="' + y1 + '" x2="' + x2 + '" y2="' + y2 + '"/>' +
        '<line class="chain-edge-line" x1="' + x1 + '" y1="' + y1 + '" x2="' + x2 + '" y2="' + y2 +
        '" marker-end="url(#chain-arrow)"/></g>';
    }).join("");
    const boxes = nodes.map((n) => {
      const p = pos[n.model_id];
      let fill = "#e3f2fd", stroke = "#1976d2";
      if (!hasDownstream[n.model_id]) { fill = "#e0f2f1"; stroke = "#00897b"; }
      if (n.retired) { fill = "#f5f5f5"; stroke = "#bbb"; }
      // The whole node is a click target onto that model's Overview; the title
      // gives the same affordance on hover for anyone using a pointer.
      return '<g class="chain-node" data-open="' + esc(n.model_id) + '">' +
        "<title>" + esc(n.model_id) + " — open this model</title>" +
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
