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
      '<span><span class="chain-swatch" style="background:#ede7f6;border-color:#5e35b1;border-width:2px"></span> product</span>' +
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
    const SW = this._SW, SH = this._SH, PW = 160, PGAP = 60;
    const nodes = m.nodes, links = m.links || [], sources = m.sources || [];
    const components = new Set(m.components || []);
    const hasSrc = sources.length > 0;
    const srcOffset = hasSrc ? SH + this._SRCGAP : 0;

    // Longest-path layering of the model feed graph, then break multi-rank edges
    // with virtual waypoints so a skip-level feed routes between rows, not across.
    const rank = this._rank(nodes, links);
    const info = {}, layers = [];
    nodes.forEach((n) => {
      const r = rank[n.model_id];
      (layers[r] = layers[r] || []).push(n.model_id);
      info[n.model_id] = { real: true, node: n };
    });
    const routes = []; let vc = 0;
    links.forEach((l) => {
      const r1 = rank[l.from], r2 = rank[l.to];
      if (r2 - r1 <= 1) { routes.push([l.from, l.to]); return; }
      const chain = [l.from];
      for (let r = r1 + 1; r < r2; r++) {
        const vid = "__v" + (vc++);
        (layers[r] = layers[r] || []).push(vid);
        info[vid] = { real: false };
        chain.push(vid);
      }
      chain.push(l.to);
      routes.push(chain);
    });
    // Crossing reduction: barycenter (mean-of-neighbours) sweeps, down then up.
    const pos = {}, up = {}, down = {};
    Object.keys(info).forEach((id) => { up[id] = []; down[id] = []; });
    layers.forEach((L) => (L || []).forEach((id, i) => { pos[id] = i; }));
    routes.forEach((ch) => {
      for (let i = 0; i < ch.length - 1; i++) { down[ch[i]].push(ch[i + 1]); up[ch[i + 1]].push(ch[i]); }
    });
    const bary = (id, nb) => (nb[id].length ? nb[id].reduce((s, x) => s + pos[x], 0) / nb[id].length : pos[id]);
    for (let it = 0; it < 4; it++) {
      for (let r = 1; r < layers.length; r++) {
        if (layers[r]) { layers[r].sort((a, b) => bary(a, up) - bary(b, up)); layers[r].forEach((id, i) => { pos[id] = i; }); }
      }
      for (let r = layers.length - 2; r >= 0; r--) {
        if (layers[r]) { layers[r].sort((a, b) => bary(a, down) - bary(b, down)); layers[r].forEach((id, i) => { pos[id] = i; }); }
      }
    }
    // Coordinates. Virtual nodes get a thin cell so edges route through a gap.
    const cellW = (id) => (info[id].real ? W : 26);
    const layerW = layers.map((L) => (L || []).reduce((w, id, i) => w + cellW(id) + (i ? COL : 0), 0));
    const srcRowW = hasSrc ? sources.length * SW + (sources.length - 1) * COL : 0;
    const leftW = Math.max(W, srcRowW, ...layerW.filter((x) => x !== undefined));
    const Xc = PAD + leftW / 2;
    const nRows = layers.length;
    const modelTop = PAD + srcOffset;
    const modelBottom = modelTop + nRows * H + (nRows - 1) * ROW;
    const width = PAD + leftW + PGAP + PW + PAD;
    const height = modelBottom + PAD;

    const coord = {};
    layers.forEach((L, r) => {
      if (!L) return;
      const y = modelTop + r * (H + ROW);
      let x = Xc - layerW[r] / 2;
      L.forEach((id) => { const cw = cellW(id); coord[id] = { cx: x + cw / 2, top: y, bottom: y + H, cy: y + H / 2 }; x += cw + COL; });
    });
    const srcP = sources.map((s, i) => ({ s, x: (Xc - srcRowW / 2) + i * (SW + COL), y: PAD }));
    // The product itself: a distinct node to the right, vertically centred, that
    // its component models feed into.
    const pX = PAD + leftW + PGAP, pY = (modelTop + modelBottom) / 2 - H / 2;

    // Smooth path (vertical tangents) through waypoints; and a horizontal variant.
    const vPath = (pts) => {
      let d = "M" + pts[0].x + " " + pts[0].y;
      for (let i = 1; i < pts.length; i++) { const a = pts[i - 1], b = pts[i], my = (a.y + b.y) / 2; d += " C" + a.x + " " + my + " " + b.x + " " + my + " " + b.x + " " + b.y; }
      return d;
    };
    const hPath = (a, b) => { const mx = (a.x + b.x) / 2; return "M" + a.x + " " + a.y + " C" + mx + " " + a.y + " " + mx + " " + b.y + " " + b.x + " " + b.y; };

    const feedEdges = routes.map((ch) => {
      const pts = ch.map((id, i) => {
        const c = coord[id];
        return i === 0 ? { x: c.cx, y: c.bottom } : i === ch.length - 1 ? { x: c.cx, y: c.top } : { x: c.cx, y: c.cy };
      });
      return '<path d="' + vPath(pts) + '" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#pmap-arrow)"/>';
    }).join("");
    const supplyEdges = srcP.map((sp) => (sp.s.models || []).map((id) => {
      const c = coord[id]; if (!c) return "";
      return '<path d="' + vPath([{ x: sp.x + SW / 2, y: sp.y + SH }, { x: c.cx, y: c.top }]) +
        '" fill="none" stroke="#d97706" stroke-width="1.5" marker-end="url(#pmap-src-arrow)"/>';
    }).join("")).join("");
    const productEdges = (m.components || []).map((id) => {
      const c = coord[id]; if (!c) return "";
      return '<path d="' + hPath({ x: c.cx + W / 2, y: c.cy }, { x: pX, y: pY + H / 2 }) +
        '" fill="none" stroke="#7e57c2" stroke-width="1.5" marker-end="url(#pmap-prod-arrow)"/>';
    }).join("");

    const boxes = nodes.map((n) => {
      const c = coord[n.model_id];
      let fill = "#e3f2fd", stroke = "#1976d2", sw = 1.5;
      if (n.terminal) { fill = "#e0f2f1"; stroke = "#00897b"; }
      if (components.has(n.model_id)) { fill = "#bbdefb"; stroke = "#1565c0"; sw = 2.5; }
      if (n.retired) { fill = "#f5f5f5"; stroke = "#bbb"; }
      const x = c.cx - W / 2;
      return '<g class="chain-node" data-open="' + esc(n.model_id) + '">' +
        "<title>" + esc(n.model_id) + (components.has(n.model_id) ? " — product component" : "") + " — open this model</title>" +
        '<rect x="' + x + '" y="' + c.top + '" width="' + W + '" height="' + H + '" rx="7" fill="' + fill +
        '" stroke="' + stroke + '" stroke-width="' + sw + '"' + (n.retired ? ' stroke-dasharray="4 3"' : "") + "/>" +
        '<text x="' + c.cx + '" y="' + (c.top + 18) + '" text-anchor="middle" font-size="11" font-weight="700" fill="#1f2937">' + esc(n.model_id) + "</text>" +
        '<text x="' + c.cx + '" y="' + (c.top + 33) + '" text-anchor="middle" font-size="9.5" fill="#4b5563">' + esc(this._short(n.name)) + "</text></g>";
    }).join("");
    const srcNodes = srcP.map((sp) =>
      '<g><title>Data source — ' + esc(sp.s.name) + "</title>" +
      '<rect x="' + sp.x + '" y="' + sp.y + '" width="' + SW + '" height="' + SH + '" rx="16" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>' +
      '<text x="' + (sp.x + SW / 2) + '" y="' + (sp.y + SH / 2 + 4) + '" text-anchor="middle" font-size="11" font-weight="600" fill="#92400e">' + esc(sp.s.name) + "</text></g>").join("");
    const productNode =
      '<g><title>' + esc(m.product_name) + " — this product</title>" +
      '<rect x="' + pX + '" y="' + pY + '" width="' + PW + '" height="' + H + '" rx="7" fill="#ede7f6" stroke="#5e35b1" stroke-width="2.5"/>' +
      '<text x="' + (pX + PW / 2) + '" y="' + (pY + 18) + '" text-anchor="middle" font-size="10" font-weight="700" fill="#4527a0">PRODUCT</text>' +
      '<text x="' + (pX + PW / 2) + '" y="' + (pY + 33) + '" text-anchor="middle" font-size="10" fill="#4527a0">' + esc(this._short(m.product_name)) + "</text></g>";

    return '<svg width="' + width + '" height="' + height + '" viewBox="0 0 ' + width + " " + height +
      '" xmlns="http://www.w3.org/2000/svg"><defs>' +
      '<marker id="pmap-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" ' +
      'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10" fill="none" stroke="#94a3b8" ' +
      'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker>' +
      '<marker id="pmap-src-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" ' +
      'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10" fill="none" stroke="#d97706" ' +
      'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker>' +
      '<marker id="pmap-prod-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" ' +
      'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10" fill="none" stroke="#7e57c2" ' +
      'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker></defs>' +
      supplyEdges + feedEdges + productEdges + srcNodes + boxes + productNode + "</svg>";
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
