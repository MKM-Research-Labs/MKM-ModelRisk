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

// The per-model neighbourhood on a model's Connections tab. Data sources sit on
// the top row as amber nodes, each with an arrow down to the focus model and to
// any of its upstream models that draw on it. Below them the dependency chain:
// the models that feed the focus (solid arrows point at the focus), the focus in
// the middle, and the models it feeds beneath. A terminal focus (nothing consumes
// it — the end of a chain) is drawn teal, the same coverage cue the Model Chain
// screen uses. Clicking any model re-centres the neighbourhood on it.
const Neighbourhood = {
  _W: 140, _H: 44, _COL: 30, _ROW: 64, _PAD: 24,

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
    host.innerHTML = this._status(n) + this._legend() + this._body(n);
    this._bind(hostId);
  },

  _SW: 120, _SH: 34, _SRCGAP: 52,

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
      '<span><span class="chain-swatch" style="background:#fef3c7;border-color:#d97706"></span> data source</span>' +
      '<span><span class="chain-swatch" style="background:#e3f2fd;border-color:#1976d2"></span> model</span>' +
      '<span><span class="chain-swatch" style="background:#e0f2f1;border-color:#00897b"></span> terminal (chain end)</span>' +
      '<span><svg width="26" height="10"><line x1="0" y1="5" x2="26" y2="5" stroke="#94a3b8" stroke-width="1.5" ' +
      'marker-end="url(#nbhd-arrow)"/></svg> feeds</span>' +
      '<span><svg width="26" height="10"><line x1="0" y1="5" x2="26" y2="5" stroke="#d97706" stroke-width="1.5" ' +
      'marker-end="url(#nbhd-src-arrow)"/></svg> supplies data</span>' +
      "</div>";
  },

  _body(n) {
    const up = n.feeds.upstream, down = n.feeds.downstream, sources = n.sources || [];
    if (!up.length && !down.length && !sources.length) {
      return '<div class="empty">No declared feeds or data sources yet. Record model ' +
        "dependencies and data sources to map this model's neighbourhood.</div>";
    }
    return '<div class="chain-canvas" style="overflow:auto">' + this._svg(n) + "</div>";
  },

  _svg(n) {
    const W = this._W, H = this._H, PAD = this._PAD, ROW = this._ROW, COL = this._COL;
    const SW = this._SW, SH = this._SH;
    const up = n.feeds.upstream, down = n.feeds.downstream, sources = n.sources || [];
    const hasUp = up.length > 0, hasDown = down.length > 0, hasSrc = sources.length > 0;
    const srcRowW = this._rowW(sources.length, SW);
    const maxW = Math.max(W, this._rowW(up.length), this._rowW(down.length), srcRowW);
    const Xc = PAD + maxW / 2;
    const ySrc = PAD;
    const yUp = PAD + (hasSrc ? SH + this._SRCGAP : 0);
    const yFocus = yUp + (hasUp ? H + ROW : 0);
    const yDown = yFocus + H + ROW;
    const height = (hasDown ? yDown + H : yFocus + H) + PAD;
    const width = PAD + maxW + PAD;

    const modelRow = (nodes, y) => {
      const x0 = Xc - this._rowW(nodes.length) / 2;
      return nodes.map((m, i) => ({ m, x: x0 + i * (W + COL), y }));
    };
    const upP = modelRow(up, yUp), downP = modelRow(down, yDown);
    const focusP = { x: Xc - W / 2, y: yFocus };
    const x0s = Xc - srcRowW / 2;
    const srcP = sources.map((s, i) => ({ s, x: x0s + i * (SW + COL), y: ySrc }));
    // Where each model that a source can point at lives (focus + its upstream).
    const posById = { [n.focus.model_id]: focusP };
    upP.forEach((u) => { posById[u.m.model_id] = u; });

    const feed = (from, to) =>
      '<line x1="' + (from.x + W / 2) + '" y1="' + (from.y + H) + '" x2="' + (to.x + W / 2) +
      '" y2="' + to.y + '" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#nbhd-arrow)"/>';
    const supply = (s, to) =>
      '<line x1="' + (s.x + SW / 2) + '" y1="' + (s.y + SH) + '" x2="' + (to.x + W / 2) +
      '" y2="' + to.y + '" stroke="#d97706" stroke-width="1.5" marker-end="url(#nbhd-src-arrow)"/>';
    const edges =
      srcP.map((sp) => (sp.s.models || []).map((id) =>
        posById[id] ? supply(sp, posById[id]) : "").join("")).join("") +
      upP.map((u) => feed(u, focusP)).join("") +
      downP.map((d) => feed(focusP, d)).join("");

    const modelNodes = [focusP].concat(upP, downP).map((p) => {
      const isFocus = p === focusP;
      const m = isFocus ? n.focus : p.m;
      let fill = "#e3f2fd", stroke = "#1976d2";
      if (isFocus && n.focus.terminal) { fill = "#e0f2f1"; stroke = "#00897b"; }
      if (m.retired) { fill = "#f5f5f5"; stroke = "#bbb"; }
      const sw = isFocus ? 2.5 : 1.5;
      return '<g class="chain-node" data-open="' + esc(m.model_id) + '">' +
        "<title>" + esc(m.model_id) + " — open this model</title>" +
        '<rect x="' + p.x + '" y="' + p.y + '" width="' + W + '" height="' + H + '" rx="7" fill="' + fill +
        '" stroke="' + stroke + '" stroke-width="' + sw + '"' + (m.retired ? ' stroke-dasharray="4 3"' : "") + "/>" +
        '<text x="' + (p.x + W / 2) + '" y="' + (p.y + 18) + '" text-anchor="middle" font-size="11" ' +
        'font-weight="700" fill="#1f2937">' + esc(m.model_id) + "</text>" +
        '<text x="' + (p.x + W / 2) + '" y="' + (p.y + 33) + '" text-anchor="middle" font-size="9.5" ' +
        'fill="#4b5563">' + esc(this._short(m.name)) + "</text></g>";
    }).join("");
    const srcNodes = srcP.map((sp) =>
      '<g><title>Data source — ' + esc(sp.s.name) + "</title>" +
      '<rect x="' + sp.x + '" y="' + sp.y + '" width="' + SW + '" height="' + SH + '" rx="16" ' +
      'fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>' +
      '<text x="' + (sp.x + SW / 2) + '" y="' + (sp.y + SH / 2 + 4) + '" text-anchor="middle" ' +
      'font-size="11" font-weight="600" fill="#92400e">' + esc(sp.s.name) + "</text></g>").join("");

    return '<svg width="' + width + '" height="' + height + '" viewBox="0 0 ' + width + " " + height +
      '" xmlns="http://www.w3.org/2000/svg"><defs>' +
      '<marker id="nbhd-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" ' +
      'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10" fill="none" stroke="#94a3b8" ' +
      'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker>' +
      '<marker id="nbhd-src-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" ' +
      'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10" fill="none" stroke="#d97706" ' +
      'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker></defs>' +
      edges + srcNodes + modelNodes + "</svg>";
  },

  _bind(hostId) {
    document.querySelectorAll("#" + hostId + " [data-open]").forEach((g) => {
      g.onclick = () => {
        const id = g.getAttribute("data-open");
        if (typeof Detail !== "undefined") Detail.show(id, "connections");
      };
    });
  },

  _short(name) {
    const s = String(name || "");
    return s.length > 18 ? s.slice(0, 17) + "…" : s;
  },
};
