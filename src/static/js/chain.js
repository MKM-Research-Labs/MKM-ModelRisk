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

// The Model Chain ("string of pearls"): the whole estate's dependency graph,
// derived from what each model declares on its Connections tab. Edges point in the
// direction data flows (producer -> consumer). The graph is guaranteed acyclic by
// the declaration-time guard, so longest-path layering always terminates.
//
// Every registered model is already a node here, so there is no tray to drag from
// as there is on a model's own canvas: connecting two models means dragging from
// one node's handle onto another (GraphWire). Each arrow carries what the handoff
// says crosses it, and opens that handoff when clicked.
const BOX_W = 130, BOX_H = 42, COL_GAP = 34, ROW_GAP = 52, PAD = 20;

const Chain = {
  _tab: "chain",
  // Models pulled onto the canvas from the tray but not yet wired to anything.
  // View state only — nothing is recorded until an edge is declared, and a model
  // drops out of here the moment it has one.
  _staged: {},

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
    // A staged model that has since been wired is now in the chain on its own
    // merit, so it stops being staged rather than being drawn twice.
    inChain.forEach((id) => { delete this._staged[id]; });
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
      "dependencies. Arrows run producer &rarr; consumer. Hover an arrow to see what " +
      "crosses it; click it to open the handoff. Drag a model&rsquo;s handle onto another " +
      "to declare a feed.</p>" + bar + body + "</div>" +
      '<div id="chain-handoff"></div>';
    this._bind();
  },

  // Models with no declared dependency are in no chain, so the graph does not draw
  // them — which would leave no way to wire one in from here. The tray brings one
  // onto the canvas; that is a view-only staging, not a declaration. Wiring its
  // handle to another model is what declares something, and the direction is then
  // unambiguous because you chose which end you dragged from.
  _unconnected() {
    const drawn = {};
    this._chainNodes.forEach((n) => { drawn[n.model_id] = true; });
    return (this._chain.nodes || []).filter((n) => !drawn[n.model_id] && !n.retired);
  },

  _tray() {
    const spare = this._unconnected();
    if (!spare.length) return "";
    const chips = spare.map((n) =>
      '<span class="nbhd-chip nbhd-chip-model" data-value="' + esc(n.model_id) + '">' +
      esc(n.model_id) + "</span>").join("");
    return '<div class="nbhd-tray"><div class="nbhd-tray-head"><b>Not in any chain</b> ' +
      '<span class="muted" style="font-size:11.5px">drag one onto the canvas, then drag ' +
      "its handle onto the model it feeds</span></div>" +
      '<div class="nbhd-chips">' + chips + "</div></div>";
  },

  _chainBody() {
    const legend =
      '<div class="row" style="gap:var(--space-9);align-items:center;margin-bottom:var(--space-5);font-size:var(--size-sm)">' +
      '<span><span class="chain-swatch" style="background:var(--accent-soft);border-color:var(--accent)"></span> model in the chain</span>' +
      '<span><span class="chain-swatch" style="background:var(--teal-bg);border-color:var(--teal)"></span> terminal output (no downstream)</span>' +
      '<span><span class="chain-swatch" style="background:var(--sunken);border-color:var(--node-retired)"></span> hibernated</span>' +
      '<span><span class="chain-swatch" style="background:var(--panel);border-color:var(--indigo)"></span> staged (not yet connected)</span>' +
      "</div>";
    // The graph shows models in a chain, plus any staged from the tray.
    const staged = (this._chain.nodes || []).filter((n) => this._staged[n.model_id]);
    const graph = { nodes: this._chainNodes.concat(staged), links: this._chain.links || [] };
    return this._tray() + legend +
      '<div class="chain-canvas" style="overflow:auto">' + this._svg(graph) + "</div>" +
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
      row.onclick = async (ev) => {
        // The handle is a drag affordance, not a link — a click that started
        // there must not also navigate away mid-gesture.
        if (ev.target.closest && ev.target.closest(".graph-handle")) return;
        const id = row.getAttribute("data-open");
        await Nav.show("inventory");
        // Always land on Overview: Detail remembers the last tab it showed.
        if (typeof Detail !== "undefined") Detail.show(id, "overview");
      };
    });
    this._bindEdges();
    this._bindHandles();
    this._bindTray();
  },

  // Dropping a chip anywhere on the canvas stages that model. No write happens
  // here — staging only puts it where its handle can be dragged.
  _bindTray() {
    const host = document.getElementById("tab-chain");
    if (!host) return;
    const canvas = host.querySelector(".chain-canvas");
    host.querySelectorAll(".nbhd-tray .nbhd-chip").forEach((chip) => {
      chip.onpointerdown = (ev) => GraphWire.startChip(ev, {
        chip: chip, host: host, canvas: canvas, dropClass: "chain-staging",
        target: (e) => {
          const el = document.elementFromPoint(e.clientX, e.clientY);
          return el && el.closest ? el.closest(".chain-canvas") : null;
        },
        onDrop: (value) => { this._staged[value] = true; this._draw(); },
      });
    });
  },

  // Dragging one node's handle onto another declares that the first feeds the
  // second, recorded on the producer as a downstream dependency — the same edge
  // the chain would derive from the consumer declaring it upstream.
  _bindHandles() {
    const host = document.getElementById("tab-chain");
    if (!host) return;
    const svg = host.querySelector("svg");
    host.querySelectorAll(".graph-handle").forEach((handle) => {
      const node = handle.closest("[data-node]");
      handle.onpointerdown = (ev) => GraphWire.start(ev, {
        host: host, svg: svg, canvas: host.querySelector(".chain-canvas"),
        from: handle.getAttribute("data-handle"),
        x0: parseFloat(node.getAttribute("data-x")) + BOX_W,
        y0: parseFloat(node.getAttribute("data-y")) + BOX_H / 2,
        onConnect: (from, to) => App.amend(
          "Declare the dependency " + from + " → " + to + ".", "POST",
          "/api/models/" + encodeURIComponent(from) + "/collections/dependencies",
          { fields: { direction: "downstream", model_id: to } }, () => this.render()),
      });
    });
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
        (n.retired ? ' stroke-dasharray="4 3"' : "") + "/>" +
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
};
