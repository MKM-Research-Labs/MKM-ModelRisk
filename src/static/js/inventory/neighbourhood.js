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

// The per-model neighbourhood on a model's Connections tab, and the canvas the
// declarations are made on. Data sources sit on the top row as amber nodes, each
// with an arrow down to the focus model and to any of its upstream models that draw
// on it. Below them the dependency chain: the models that feed the focus (solid
// arrows point at the focus), the focus in the middle, and the models it feeds
// beneath. A terminal focus (nothing consumes it — the end of a chain) is drawn
// teal, the same coverage cue the Model Chain screen uses.
//
// The three rows are always drawn, empty or not, because they are drop targets:
// NeighbourhoodEdit (loaded after this) drags models and sources onto them to
// declare a feed, and hit-tests against the layout this module records in
// ``_layout``. Clicking a model re-centres; clicking an arrow opens the handoff —
// what actually crosses that edge, field by field.
const Neighbourhood = {
  _W: 140, _H: 44, _COL: 30, _ROW: 64, _PAD: 24,
  _SW: 120, _SH: 34, _SRCGAP: 52,
  // A band has to stay droppable when it holds nothing, so the canvas never
  // narrows below this and each row keeps a margin of slack around it.
  _MINW: 520, _BANDPAD: 12,
  _layout: null,
  _n: null,

  async render(modelId, hostId) {
    const host = document.getElementById(hostId);
    if (!host) return;
    let n;
    try {
      n = await App.get("/api/models/" + modelId + "/neighbourhood");
    } catch (_) {
      host.innerHTML = '<div class="empty">Could not load connections.</div>';
      return;
    }
    this._n = n;
    host.innerHTML = this._status(n) + this._legend() + this._body(n);
    this._bind(hostId);
    if (typeof NeighbourhoodEdit !== "undefined") NeighbourhoodEdit.attach(this, hostId);
  },

  // Re-read and redraw in place, keeping the tab and its editors as they are —
  // used after a declaration so the picture catches up without a page-level
  // refresh that would shut an open handoff panel.
  async refresh() {
    if (this._n) await this.render(this._n.focus.model_id, this._hostId);
  },

  _rowW(k, w) { const u = w || this._W; return k > 0 ? k * u + (k - 1) * this._COL : 0; },

  _status(n) {
    const f = n.focus, up = n.feeds.upstream.length, down = n.feeds.downstream.length,
      src = (n.sources || []).length;
    let position;
    if (f.terminal && f.is_source) position = "Isolated — nothing feeds it and nothing consumes it.";
    else if (f.terminal) position = "Terminal — the end of a chain; no model consumes its output.";
    else if (f.is_source) position = "Source — nothing feeds it; it starts a chain.";
    else position = "Mid-chain.";
    const counts = src + " data source" + (src === 1 ? "" : "s") + " · " +
      up + " feeding in · " + down + " fed";
    const metaLine = f.vendor
      ? '<div class="muted" style="font-size:12px;margin-top:2px">Vendor: ' + esc(f.vendor) + "</div>" : "";
    return '<div style="margin-bottom:10px"><b>' + esc(position) + "</b> " +
      '<span class="muted" style="font-size:12px">(' + counts + ")</span>" + metaLine + "</div>";
  },

  _legend() {
    return '<div class="row" style="gap:18px;align-items:center;margin-bottom:10px;font-size:12px">' +
      '<span><span class="chain-swatch" style="background:var(--warn-bg-alt);border-color:var(--warn-line)"></span> data source</span>' +
      '<span><span class="chain-swatch" style="background:var(--accent-soft);border-color:var(--accent)"></span> model</span>' +
      '<span><span class="chain-swatch" style="background:var(--teal-bg);border-color:var(--teal)"></span> terminal (chain end)</span>' +
      '<span><svg width="26" height="10"><line x1="0" y1="5" x2="26" y2="5" stroke="' + Theme.value("slate") + '" stroke-width="1.5" ' +
      'marker-end="url(#nbhd-arrow)"/></svg> feeds</span>' +
      '<span><svg width="26" height="10"><line x1="0" y1="5" x2="26" y2="5" stroke="' + Theme.value("warn-line") + '" stroke-width="1.5" ' +
      'marker-end="url(#nbhd-src-arrow)"/></svg> supplies data</span>' +
      "</div>";
  },

  _body(n) {
    return '<div class="chain-canvas nbhd-canvas" style="overflow:auto">' + this._svg(n) + "</div>";
  },

  // Where everything sits. Kept as data (rather than only as drawn output) so the
  // drag layer can hit-test a drop against a band and a node without re-deriving
  // the geometry — two derivations of the same layout would drift.
  _measure(n) {
    const W = this._W, H = this._H, PAD = this._PAD, SW = this._SW, SH = this._SH;
    const up = n.feeds.upstream, down = n.feeds.downstream, sources = n.sources || [];
    const srcRowW = this._rowW(sources.length, SW);
    const maxW = Math.max(W, this._MINW - 2 * PAD,
      this._rowW(up.length), this._rowW(down.length), srcRowW);
    const Xc = PAD + maxW / 2;
    const ySrc = PAD;
    const yUp = ySrc + SH + this._SRCGAP;
    const yFocus = yUp + H + this._ROW;
    const yDown = yFocus + H + this._ROW;
    const row = (nodes, y, w) => {
      const x0 = Xc - this._rowW(nodes.length, w) / 2;
      return nodes.map((m, i) => ({ m, x: x0 + i * (w + this._COL), y, w, h: w === SW ? SH : H }));
    };
    return {
      W, H, SW, SH, Xc, width: PAD + maxW + PAD, height: yDown + H + PAD,
      focus: { x: Xc - W / 2, y: yFocus, w: W, h: H, m: n.focus },
      up: row(up, yUp, W), down: row(down, yDown, W), src: row(sources, ySrc, SW),
      bands: {
        upstream: { y: yUp - this._BANDPAD, h: H + 2 * this._BANDPAD },
        downstream: { y: yDown - this._BANDPAD, h: H + 2 * this._BANDPAD },
        sources: { y: ySrc - this._BANDPAD, h: SH + 2 * this._BANDPAD },
      },
    };
  },

  // A band is invisible until a drag starts (the canvas gains .nbhd-dragging),
  // so the resting picture is unchanged by the fact that it is also editable.
  _bandRects(L) {
    const label = {
      sources: "drop a data source here — it supplies this model",
      upstream: "drop a model here — it feeds this model",
      downstream: "drop a model here — this model feeds it",
    };
    return Object.keys(L.bands).map((key) => {
      const b = L.bands[key];
      return '<g class="nbhd-band" data-band="' + key + '">' +
        '<rect x="' + this._PAD / 2 + '" y="' + b.y + '" width="' + (L.width - this._PAD) +
        '" height="' + b.h + '" rx="8"/>' +
        // Left-aligned: the nodes are centred, so a centred caption would land on
        // top of their names for exactly the rows that already hold something.
        '<text x="' + (this._PAD / 2 + 12) + '" y="' + (b.y + b.h / 2 + 4) + '" ' +
        'font-size="10.5">' + esc(label[key]) + "</text></g>";
    }).join("");
  },

  // The arrow, a fat invisible line to click it by, and what the handoff says
  // crosses it. An undeclared edge reads "state what crosses" so the gap is an
  // invitation rather than a silence.
  _feedEdge(from, to, node) {
    const e = (node && node.edge) || {};
    const h = e.handoff || {};
    const x1 = from.x + from.w / 2, y1 = from.y + from.h, x2 = to.x + to.w / 2, y2 = to.y;
    const label = !h.declared || !h.field_count
      ? "state what crosses"
      : h.field_count + " field" + (h.field_count === 1 ? "" : "s") +
        (h.status && h.status !== "Draft" ? " · " + h.status : "");
    const mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
    return '<g class="nbhd-edge" data-edge="' + esc(e.from || "") + "|" + esc(e.to || "") + '">' +
      "<title>" + esc(e.from || "") + " → " + esc(e.to || "") + " — open the handoff</title>" +
      '<line x1="' + x1 + '" y1="' + y1 + '" x2="' + x2 + '" y2="' + y2 +
      '" stroke="' + Theme.value("slate") + '" stroke-width="1.5" marker-end="url(#nbhd-arrow)"/>' +
      '<line class="nbhd-hit" x1="' + x1 + '" y1="' + y1 + '" x2="' + x2 + '" y2="' + y2 + '"/>' +
      '<text class="nbhd-edge-label" x="' + (mx + 6) + '" y="' + my + '" font-size="9.5">' +
      esc(label) + "</text></g>";
  },

  _supplyEdge(s, to) {
    return '<line x1="' + (s.x + s.w / 2) + '" y1="' + (s.y + s.h) + '" x2="' + (to.x + to.w / 2) +
      '" y2="' + to.y + '" stroke="' + Theme.value("warn-line") + '" stroke-width="1.5" marker-end="url(#nbhd-src-arrow)"/>';
  },

  _modelNode(p, n, isFocus) {
    const m = isFocus ? n.focus : p.m;
    let fill = Theme.value("accent-soft"), stroke = Theme.value("accent");
    if (isFocus && n.focus.terminal) { fill = Theme.value("teal-bg"); stroke = Theme.value("teal"); }
    if (m.retired) { fill = Theme.value("sunken"); stroke = Theme.value("node-retired"); }
    const W = p.w, H = p.h;
    return '<g class="chain-node nbhd-node" data-open="' + esc(m.model_id) + '" data-node="' +
      esc(m.model_id) + '" data-x="' + p.x + '" data-y="' + p.y + '">' +
      "<title>" + esc(m.model_id) + " — open this model, or drag the handle to connect it</title>" +
      '<rect x="' + p.x + '" y="' + p.y + '" width="' + W + '" height="' + H + '" rx="7" fill="' + fill +
      '" stroke="' + stroke + '" stroke-width="' + (isFocus ? 2.5 : 1.5) + '"' +
      (m.retired ? ' stroke-dasharray="4 3"' : "") + "/>" +
      '<text x="' + (p.x + W / 2) + '" y="' + (p.y + 18) + '" text-anchor="middle" font-size="11" ' +
      'font-weight="700" fill="' + Theme.value("node-ink") + '">' + esc(m.model_id) + "</text>" +
      '<text x="' + (p.x + W / 2) + '" y="' + (p.y + 33) + '" text-anchor="middle" font-size="9.5" ' +
      'fill="' + Theme.value("node-sub") + '">' + esc(this._short(m.name)) + "</text>" +
      '<circle class="graph-handle" data-handle="' + esc(m.model_id) + '" cx="' + (p.x + W) +
      '" cy="' + (p.y + H / 2) + '" r="5"><title>Drag onto another model to connect them</title>' +
      "</circle></g>";
  },

  _svg(n) {
    const L = this._measure(n);
    this._layout = L;
    const posById = { [n.focus.model_id]: L.focus };
    L.up.forEach((u) => { posById[u.m.model_id] = u; });

    const edges =
      L.src.map((sp) => (sp.m.models || []).map((id) =>
        posById[id] ? this._supplyEdge(sp, posById[id]) : "").join("")).join("") +
      L.up.map((u) => this._feedEdge(u, L.focus, u.m)).join("") +
      L.down.map((d) => this._feedEdge(L.focus, d, d.m)).join("");

    const modelNodes = this._modelNode(L.focus, n, true) +
      L.up.concat(L.down).map((p) => this._modelNode(p, n, false)).join("");
    const srcNodes = L.src.map((sp) =>
      '<g class="nbhd-src" data-source="' + esc(sp.m.name) + '"><title>Data source — ' +
      esc(sp.m.name) + "</title>" +
      '<rect x="' + sp.x + '" y="' + sp.y + '" width="' + sp.w + '" height="' + sp.h + '" rx="16" ' +
      'fill="' + Theme.value("warn-bg-alt") + '" stroke="' + Theme.value("warn-line") + '" stroke-width="1.5"/>' +
      '<text x="' + (sp.x + sp.w / 2) + '" y="' + (sp.y + sp.h / 2 + 4) + '" text-anchor="middle" ' +
      'font-size="11" font-weight="600" fill="' + Theme.value("warn-ink") + '">' + esc(sp.m.name) + "</text></g>").join("");

    return '<svg class="nbhd-svg" width="' + L.width + '" height="' + L.height + '" viewBox="0 0 ' +
      L.width + " " + L.height + '" xmlns="http://www.w3.org/2000/svg"><defs>' +
      '<marker id="nbhd-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" ' +
      'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10" fill="none" stroke="' + Theme.value("slate") + '" ' +
      'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker>' +
      '<marker id="nbhd-src-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" ' +
      'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10" fill="none" stroke="' + Theme.value("warn-line") + '" ' +
      'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker></defs>' +
      // Bands last, so that while a chip is being dragged they sit above the nodes
      // and a drop lands on the band rather than on whatever it happens to cover.
      edges + srcNodes + modelNodes + this._bandRects(L) +
      '<g class="graph-rubber"></g></svg>';
  },

  _bind(hostId) {
    this._hostId = hostId;
    const root = document.getElementById(hostId);
    if (!root) return;
    // The handle is a drag affordance, not a link — the drag layer claims it, so a
    // click that started there must not also re-centre the page.
    root.querySelectorAll("[data-open]").forEach((g) => {
      g.onclick = (ev) => {
        if (ev.target.closest(".graph-handle")) return;
        const id = g.getAttribute("data-open");
        if (typeof Detail !== "undefined") Detail.show(id, "connections");
      };
    });
    root.querySelectorAll("[data-edge]").forEach((g) => {
      g.onclick = () => {
        const [from, to] = g.getAttribute("data-edge").split("|");
        if (from && to && typeof Handoffs !== "undefined") {
          Handoffs.open(from, to, () => this.refresh(), "nbhd-handoff");
        }
      };
    });
  },

  _short(name) {
    const s = String(name || "");
    return s.length > 18 ? s.slice(0, 17) + "…" : s;
  },
};
