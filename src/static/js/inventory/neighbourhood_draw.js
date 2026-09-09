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

// How the neighbourhood is drawn, once neighbourhood.js has worked out where
// everything goes.
//
// The division is between the two questions the picture answers separately: that
// file measures — how wide each band is, what the canvas has to be to hold it — and
// this one renders the result as SVG. Keeping them apart matters because the drop
// bands are geometry that is also a control: NeighbourhoodEdit hit-tests against the
// measured layout, and the rectangles here only make that geometry visible.
//
// Nothing outside the neighbourhood uses these; the Model Chain screen and a
// product's model map each draw their own.
//
// Assigns onto Neighbourhood; loads after neighbourhood.js.

Object.assign(Neighbourhood, {

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

});
