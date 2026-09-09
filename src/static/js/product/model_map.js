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
    return '<div style="margin-bottom:var(--space-5)"><b>' + esc(m.product_name) + "</b> " +
      '<span class="muted" style="font-size:var(--size-sm)">references ' + comps + " model" +
      (comps === 1 ? "" : "s") + " directly" +
      (feeds > 0 ? ", drawing in " + feeds + " more up the chain" : "") + ".</span></div>";
  },

  _legend() {
    return '<div class="row" style="gap:var(--space-9);align-items:center;margin-bottom:var(--space-5);font-size:var(--size-sm)">' +
      '<span><span class="chain-swatch" style="background:var(--product-bg);border-color:var(--product);border-width:2px"></span> product</span>' +
      '<span><span class="chain-swatch" style="background:var(--warn-bg-alt);border-color:var(--warn-line)"></span> data source</span>' +
      '<span><span class="chain-swatch" style="background:var(--accent-border);border-color:var(--accent);border-width:2px"></span> component (in this product)</span>' +
      '<span><span class="chain-swatch" style="background:var(--accent-soft);border-color:var(--accent)"></span> upstream model</span>' +
      '<span><span class="chain-swatch" style="background:var(--teal-bg);border-color:var(--teal)"></span> terminal (chain end)</span>' +
      '<span><svg width="26" height="10"><line x1="0" y1="5" x2="26" y2="5" stroke="' + Theme.value("slate") + '" stroke-width="1.5" ' +
      'marker-end="url(#pmap-arrow)"/></svg> feeds</span>' +
      '<span><svg width="26" height="10"><line x1="0" y1="5" x2="26" y2="5" stroke="' + Theme.value("warn-line") + '" stroke-width="1.5" ' +
      'marker-end="url(#pmap-src-arrow)"/></svg> supplies data</span></div>';
  },

  _body(m) {
    if (!m.nodes.length) {
      return '<div class="empty">This product has no component models yet. Add them on the ' +
        "Components tab to map the chain it depends on.</div>";
    }
    return '<div class="chain-canvas" style="overflow:auto">' + this._svg(m) + "</div>";
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
