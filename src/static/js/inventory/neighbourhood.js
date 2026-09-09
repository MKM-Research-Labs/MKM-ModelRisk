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
// declarations are made on. Data sources sit on the top row as amber nodes arrowed
// down at the focus — but only where the focus is the top of its stack, nothing
// feeding it. A model another model feeds takes its inputs from that model; a source
// arrow beside it would read as a second origin (the server decides this — see
// ``model_inventory/sources.py``), so mid-chain the row is empty.
// Below it the dependency chain: the models that feed the focus (solid
// arrows point at the focus), the focus in the middle, and the models it feeds
// beneath. A terminal focus (nothing consumes it — the end of a chain) is drawn
// teal, the same coverage cue the Model Chain screen uses.
//
// The feed rows are always drawn, empty or not, because they are drop targets:
// NeighbourhoodEdit (loaded after this) drags models and sources onto them to
// declare a feed (the source row is there only where one can land — see
// ``_measure``), and hit-tests against the layout this module records in
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
    // Counted off the focus's own declarations, not off the drawn source row: a
    // mid-chain model's source is a fact about it even where the picture leaves the
    // arrow off, and a count that disagreed with its register would read as loss.
    const f = n.focus, up = n.feeds.upstream.length, down = n.feeds.downstream.length,
      src = (f.data_sources || []).length;
    let position;
    if (f.terminal && f.is_source) position = "Isolated — nothing feeds it and nothing consumes it.";
    else if (f.terminal) position = "Terminal — the end of a chain; no model consumes its output.";
    else if (f.is_source) position = "Source — nothing feeds it; it starts a chain.";
    else position = "Mid-chain.";
    const counts = src + " data source" + (src === 1 ? "" : "s") + " · " +
      up + " feeding in · " + down + " fed";
    const metaLine = f.vendor
      ? '<div class="muted" style="font-size:var(--size-sm);margin-top:var(--space-1)">Vendor: ' + esc(f.vendor) + "</div>" : "";
    return '<div style="margin-bottom:var(--space-5)"><b>' + esc(position) + "</b> " +
      '<span class="muted" style="font-size:var(--size-sm)">(' + counts + ")</span>" + metaLine + "</div>";
  },

  _legend() {
    return '<div class="row" style="gap:var(--space-9);align-items:center;margin-bottom:var(--space-5);font-size:var(--size-sm)">' +
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
    // Mid-chain the source row is not merely empty, it is not applicable — the
    // server draws no source against a model another model feeds — so the row and
    // its band collapse rather than reserving a blank strip above the chain that
    // reads as something missing. Where the focus does start a chain the row is kept
    // even with nothing on it: there it is an empty drop target, an invitation.
    const hasSrcRow = !!n.focus.is_source;
    const srcRowW = this._rowW(sources.length, SW);
    const maxW = Math.max(W, this._MINW - 2 * PAD,
      this._rowW(up.length), this._rowW(down.length), srcRowW);
    const Xc = PAD + maxW / 2;
    const ySrc = PAD;
    const yUp = hasSrcRow ? ySrc + SH + this._SRCGAP : PAD;
    const yFocus = yUp + H + this._ROW;
    const yDown = yFocus + H + this._ROW;
    const row = (nodes, y, w) => {
      const x0 = Xc - this._rowW(nodes.length, w) / 2;
      return nodes.map((m, i) => ({ m, x: x0 + i * (w + this._COL), y, w, h: w === SW ? SH : H }));
    };
    const bands = {
      upstream: { y: yUp - this._BANDPAD, h: H + 2 * this._BANDPAD },
      downstream: { y: yDown - this._BANDPAD, h: H + 2 * this._BANDPAD },
    };
    if (hasSrcRow) bands.sources = { y: ySrc - this._BANDPAD, h: SH + 2 * this._BANDPAD };
    return {
      W, H, SW, SH, Xc, width: PAD + maxW + PAD, height: yDown + H + PAD,
      focus: { x: Xc - W / 2, y: yFocus, w: W, h: H, m: n.focus },
      up: row(up, yUp, W), down: row(down, yDown, W),
      src: row(hasSrcRow ? sources : [], ySrc, SW),
      bands: bands,
    };
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
