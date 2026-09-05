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
// Drawing the model chain: ranking, edges, and the SVG itself.
//
// Split from chain.js so that what the chain IS -- which models feed which, and which
// nodes are external to the firm -- is read apart from how it is painted.
//
// Assigns onto Chain; loads after chain.js.

Object.assign(Chain, {

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
    return '<div class="section-header" style="margin-top:var(--space-8)">Handoffs</div>' +
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
        '" marker-end="url(#chain-arrow)"/>' +
        // What crosses this edge, worded by GraphWire so the per-model canvas and
        // this one cannot say it differently.
        '<text class="nbhd-edge-label" x="' + ((x1 + x2) / 2 + 6) + '" y="' + ((y1 + y2) / 2) +
        '" font-size="9.5">' + esc(GraphWire.label(l.handoff)) + "</text></g>";
    }).join("");
    const boxes = nodes.map((n) => {
      const p = pos[n.model_id];
      let fill = Theme.value("accent-soft"), stroke = Theme.value("accent");
      if (!hasDownstream[n.model_id]) { fill = Theme.value("teal-bg"); stroke = Theme.value("teal"); }
      // A node the institution does not own — a foundation model somebody else
      // versions, an MCP server outside the firm — is drawn in its own colour and
      // outlined rather than filled. What a chain diagram is FOR is showing where the
      // firm's perimeter ends, and a supply chain drawn all one colour does not.
      // Colour from the theme only (R10); a model keeps exactly the styling it had.
      const kind = Chain.nodeKind(n);
      if (kind !== "MODEL") {
        stroke = Theme.colour("lineage_node", kind) || stroke;
        fill = Chain.isGoverned(kind) ? Theme.value("panel") : Theme.value("sunken");
      }
      // A staged model is on the canvas but in no chain yet — drawn hollow so it
      // never reads as a declaration that has already been made.
      if (this._staged[n.model_id]) { fill = Theme.value("panel"); stroke = Theme.value("indigo"); }
      if (n.retired) { fill = Theme.value("sunken"); stroke = Theme.value("node-retired"); }
      // The whole node is a click target onto that model's Overview; the title
      // gives the same affordance on hover for anyone using a pointer.
      return '<g class="chain-node" data-open="' + esc(n.model_id) + '" data-node="' +
        esc(n.model_id) + '" data-x="' + p.x + '" data-y="' + p.y + '">' +
        "<title>" + esc(n.model_id) + " — open this model, or drag the handle onto " +
        "another model to declare a feed</title>" +
        '<rect x="' + p.x + '" y="' + p.y + '" width="' + BOX_W + '" height="' + BOX_H +
        '" rx="7" fill="' + fill + '" stroke="' + stroke + '" stroke-width="1.5"' +
        (n.retired || !Chain.isGoverned(kind) ? ' stroke-dasharray="4 3"' : "") + "/>" +
        '<text x="' + (p.x + BOX_W / 2) + '" y="' + (p.y + 17) +
        '" text-anchor="middle" font-size="11" font-weight="700" fill="' + Theme.value("node-ink") + '">' + esc(n.model_id) + "</text>" +
        '<text x="' + (p.x + BOX_W / 2) + '" y="' + (p.y + 31) +
        '" text-anchor="middle" font-size="9.5" fill="' + Theme.value("node-sub") + '">' + esc(this._short(n.name)) + "</text>" +
        '<circle class="graph-handle" data-handle="' + esc(n.model_id) + '" cx="' + (p.x + BOX_W) +
        '" cy="' + (p.y + BOX_H / 2) + '" r="5"><title>Drag onto another model to ' +
        "declare that this one feeds it</title></circle></g>";
    }).join("");
    return '<svg width="' + width + '" height="' + height + '" viewBox="0 0 ' + width + " " + height +
      '" xmlns="http://www.w3.org/2000/svg"><defs>' +
      '<marker id="chain-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" ' +
      'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10" fill="none" stroke="' + Theme.value("slate") + '" ' +
      'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker></defs>' +
      edges + boxes + '<g class="graph-rubber"></g></svg>';
  },

  _short(name) {
    const s = String(name || "");
    return s.length > 18 ? s.slice(0, 17) + "…" : s;
  },
});
