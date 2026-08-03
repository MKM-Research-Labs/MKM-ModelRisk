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

// The Product Model Map: the models a product is built from (its components,
// drawn with a bold border) and the feed-chain they sit in, laid out top-down by
// longest-path layering so every feed arrow runs producer -> consumer. Terminal
// models (nothing consumes them) are teal; retired ones grey. Dashed amber links
// join any two models that share a data source. Clicking a node opens that model.
const ProductMap = {
  _W: 150, _H: 44, _COL: 28, _ROW: 58, _PAD: 24, _SW: 120, _SH: 34, _SRCGAP: 46,

  async render(productId, hostId) {
    const host = document.getElementById(hostId);
    if (!host) return;
    let m;
    try {
      m = await App.get("/api/products/" + productId + "/model-map");
    } catch (_) {
      host.innerHTML = '<div class="empty">Could not load the model map.</div>';
      return;
    }
    host.innerHTML = this._status(m) + this._legend() + this._body(m);
    this._bind(hostId);
  },

  _status(m) {
    const comps = m.components.length, total = m.nodes.length;
    const feeds = total - comps;
    return '<div style="margin-bottom:10px"><b>' + esc(m.product_name) + "</b> " +
      '<span class="muted" style="font-size:12px">references ' + comps + " model" +
      (comps === 1 ? "" : "s") + " directly" +
      (feeds > 0 ? ", drawing in " + feeds + " more up the chain" : "") + ".</span></div>";
  },

  _legend() {
    return '<div class="row" style="gap:18px;align-items:center;margin-bottom:10px;font-size:12px">' +
      '<span><span class="chain-swatch" style="background:#fef3c7;border-color:#d97706"></span> data source</span>' +
      '<span><span class="chain-swatch" style="background:#bbdefb;border-color:#1565c0;border-width:2px"></span> component (in this product)</span>' +
      '<span><span class="chain-swatch" style="background:#e3f2fd;border-color:#1976d2"></span> upstream model</span>' +
      '<span><span class="chain-swatch" style="background:#e0f2f1;border-color:#00897b"></span> terminal (chain end)</span>' +
      '<span><svg width="26" height="10"><line x1="0" y1="5" x2="26" y2="5" stroke="#94a3b8" stroke-width="1.5" ' +
      'marker-end="url(#pmap-arrow)"/></svg> feeds</span>' +
      '<span><svg width="26" height="10"><line x1="0" y1="5" x2="26" y2="5" stroke="#d97706" stroke-width="1.5" ' +
      'marker-end="url(#pmap-src-arrow)"/></svg> supplies data</span></div>';
  },

  _body(m) {
    if (!m.nodes.length) {
      return '<div class="empty">This product has no component models yet. Add them on the ' +
        "Components tab to map the chain it depends on.</div>";
    }
    return '<div class="chain-canvas" style="overflow:auto">' + this._svg(m) + "</div>";
  },

  // Longest-path layering: a node's rank is the longest chain of producers behind
  // it, so every edge points from a lower rank to a higher one and reads top-down.
  _rank(nodes, links) {
    const succ = {}, indeg = {};
    nodes.forEach((n) => { succ[n.model_id] = []; indeg[n.model_id] = 0; });
    links.forEach((l) => {
      if (succ[l.from] === undefined || indeg[l.to] === undefined) return;
      succ[l.from].push(l.to); indeg[l.to]++;
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
    nodes.forEach((n) => { if (rank[n.model_id] === undefined) rank[n.model_id] = 0; });
    return rank;
  },

  _svg(m) {
    const W = this._W, H = this._H, PAD = this._PAD, COL = this._COL, ROW = this._ROW;
    const SW = this._SW, SH = this._SH;
    const nodes = m.nodes, links = m.links || [], sources = m.sources || [];
    const hasSrc = sources.length > 0;
    const rank = this._rank(nodes, links);
    const rows = [];
    nodes.forEach((n) => { const r = rank[n.model_id]; (rows[r] = rows[r] || []).push(n); });
    const widest = Math.max.apply(null, rows.map((r) => (r || []).length).concat([1]));
    const srcRowW = hasSrc ? sources.length * SW + (sources.length - 1) * COL : 0;
    const contentW = Math.max(widest * W + (widest - 1) * COL, srcRowW);
    const width = PAD * 2 + contentW;
    const Xc = PAD + contentW / 2;
    const srcOffset = hasSrc ? SH + this._SRCGAP : 0;
    const height = PAD * 2 + srcOffset + rows.length * H + (rows.length - 1) * ROW;

    const pos = {};
    rows.forEach((row, r) => {
      if (!row) return;
      const rowW = row.length * W + (row.length - 1) * COL;
      const x0 = Xc - rowW / 2;
      row.forEach((n, i) => { pos[n.model_id] = { x: x0 + i * (W + COL), y: PAD + srcOffset + r * (H + ROW) }; });
    });
    const srcP = sources.map((s, i) => ({ s, x: (Xc - srcRowW / 2) + i * (SW + COL), y: PAD }));

    const feedEdges = links.map((l) => {
      const a = pos[l.from], b = pos[l.to];
      if (!a || !b) return "";
      return '<line x1="' + (a.x + W / 2) + '" y1="' + (a.y + H) + '" x2="' + (b.x + W / 2) +
        '" y2="' + b.y + '" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#pmap-arrow)"/>';
    }).join("");
    const supplyEdges = srcP.map((sp) => (sp.s.models || []).map((id) => {
      const t = pos[id];
      if (!t) return "";
      return '<line x1="' + (sp.x + SW / 2) + '" y1="' + (sp.y + SH) + '" x2="' + (t.x + W / 2) +
        '" y2="' + t.y + '" stroke="#d97706" stroke-width="1.5" marker-end="url(#pmap-src-arrow)"/>';
    }).join("")).join("");

    const boxes = nodes.map((n) => {
      const p = pos[n.model_id];
      let fill = "#e3f2fd", stroke = "#1976d2", sw = 1.5;
      if (n.terminal) { fill = "#e0f2f1"; stroke = "#00897b"; }
      if (n.role === "component") { fill = "#bbdefb"; stroke = "#1565c0"; sw = 2.5; }
      if (n.retired) { fill = "#f5f5f5"; stroke = "#bbb"; }
      return '<g class="chain-node" data-open="' + esc(n.model_id) + '">' +
        "<title>" + esc(n.model_id) + (n.role === "component" ? " — product component" : "") +
        " — open this model</title>" +
        '<rect x="' + p.x + '" y="' + p.y + '" width="' + W + '" height="' + H + '" rx="7" fill="' + fill +
        '" stroke="' + stroke + '" stroke-width="' + sw + '"' + (n.retired ? ' stroke-dasharray="4 3"' : "") + "/>" +
        '<text x="' + (p.x + W / 2) + '" y="' + (p.y + 18) + '" text-anchor="middle" font-size="11" ' +
        'font-weight="700" fill="#1f2937">' + esc(n.model_id) + "</text>" +
        '<text x="' + (p.x + W / 2) + '" y="' + (p.y + 33) + '" text-anchor="middle" font-size="9.5" ' +
        'fill="#4b5563">' + esc(this._short(n.name)) + "</text></g>";
    }).join("");
    const srcNodes = srcP.map((sp) =>
      '<g><title>Data source — ' + esc(sp.s.name) + "</title>" +
      '<rect x="' + sp.x + '" y="' + sp.y + '" width="' + SW + '" height="' + SH + '" rx="16" ' +
      'fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>' +
      '<text x="' + (sp.x + SW / 2) + '" y="' + (sp.y + SH / 2 + 4) + '" text-anchor="middle" ' +
      'font-size="11" font-weight="600" fill="#92400e">' + esc(sp.s.name) + "</text></g>").join("");

    return '<svg width="' + width + '" height="' + height + '" viewBox="0 0 ' + width + " " + height +
      '" xmlns="http://www.w3.org/2000/svg"><defs>' +
      '<marker id="pmap-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" ' +
      'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10" fill="none" stroke="#94a3b8" ' +
      'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker>' +
      '<marker id="pmap-src-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" ' +
      'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10" fill="none" stroke="#d97706" ' +
      'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker></defs>' +
      supplyEdges + feedEdges + srcNodes + boxes + "</svg>";
  },

  _bind(hostId) {
    document.querySelectorAll("#" + hostId + " [data-open]").forEach((g) => {
      g.onclick = async () => {
        const id = g.getAttribute("data-open");
        await Nav.show("inventory");
        if (typeof Detail !== "undefined") Detail.show(id, "connections");
      };
    });
  },

  _short(name) {
    const s = String(name || "");
    return s.length > 20 ? s.slice(0, 19) + "…" : s;
  },
};
