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
  // What a lineage node IS. The vocabulary is config (config/governance/_lineage.py)
  // and travels with the node; an estate chain built from the inventory declares
  // nothing and every node in it is a model, which is what it was before kinds
  // existed.
  nodeKind(n) {
    const declared = String((n || {}).kind || "").trim().toUpperCase();
    return Chain.NODE_KINDS.indexOf(declared) >= 0 ? declared : "MODEL";
  },

  // Whether this kind is a record the platform holds. A foundation model and an MCP
  // server are dependencies the firm cannot review, so there is nothing to open.
  isGoverned(kind) { return Chain.EXTERNAL_KINDS.indexOf(kind) < 0; },

  // Served with the theme (/api/theme), not written here: a kind list compiled into
  // this file is a second definition of config's, and it drifts the first time a kind
  // is added. The fallbacks cover a theme payload that has not loaded yet, and say
  // only "everything is a model", which is what this screen drew before kinds existed.
  _vocab() { return (Theme._lineage || {}); },
  get NODE_KINDS() { return Chain._vocab().kinds || ["MODEL"]; },
  get EXTERNAL_KINDS() { return Chain._vocab().external || []; },

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
};
