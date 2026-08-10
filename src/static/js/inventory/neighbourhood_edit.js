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

// Making the neighbourhood canvas something you declare on, rather than only look
// at. Two gestures, both GraphWire's (the Model Chain screen uses the same ones);
// what lives here is the tray, the hit-tests and the declarations they produce:
//
//   tray -> band   drag a model or a data source from the tray onto one of the
//                  three bands. Dropping on "feeds in" declares that model feeds
//                  the focus; "feeds out" declares the focus feeds it; the top
//                  band declares a data source supplies the focus.
//   handle -> node drag from a node's handle onto another node to declare the
//                  first feeds the second — the two need not involve the focus.
//
// Every write goes through App.amend, so a declaration the server considers
// critical still raises the confirm-with-a-reason dialog. Withdrawing is left to
// the registers below the canvas: they name which model holds the declaration,
// which a gesture cannot, and an edge declared from the far end has to be removed
// there. Geometry is never re-derived here — Neighbourhood._layout is the one
// measurement, and hit-testing goes through elementFromPoint against what was drawn.
const NeighbourhoodEdit = {
  _nbhd: null, _hostId: null,

  attach(nbhd, hostId) {
    this._nbhd = nbhd;
    this._hostId = hostId;
    const host = document.getElementById(hostId);
    const canvas = host && host.querySelector(".nbhd-canvas");
    if (!canvas) return;
    canvas.insertAdjacentHTML("beforebegin", this._tray(nbhd._n));
    this._bind(host);
  },

  // What is left to connect: every registered model bar the focus and the ones
  // already drawn, and every data source the focus does not already declare.
  _candidates(n) {
    const spec = (key, field) => {
      const c = typeof Detail !== "undefined" && Detail.collSpec ? Detail.collSpec(key) : null;
      const f = c && c.fields.find((x) => x.key === field);
      return (f && f.options) || [];
    };
    const drawn = {};
    drawn[n.focus.model_id] = true;
    n.feeds.upstream.concat(n.feeds.downstream).forEach((m) => { drawn[m.model_id] = true; });
    const haveSrc = {};
    (n.focus.data_sources || []).forEach((s) => { haveSrc[s] = true; });
    return {
      models: spec("dependencies", "model_id").filter((id) => !drawn[id]),
      sources: spec("data_sources", "data_source").filter((s) => !haveSrc[s]),
    };
  },

  _chips(kind, values) {
    if (!values.length) {
      return '<span class="muted" style="font-size:11.5px">nothing left to add</span>';
    }
    return values.map((v) =>
      '<span class="nbhd-chip nbhd-chip-' + kind + '" data-kind="' + kind + '" data-value="' +
      esc(v) + '">' + esc(v) + "</span>").join("");
  },

  _tray(n) {
    const c = this._candidates(n);
    return '<div class="nbhd-tray">' +
      '<div class="nbhd-tray-head"><b>Connect</b> ' +
      '<span class="muted" style="font-size:11.5px">drag onto the canvas below</span>' +
      '<input id="nbhd-filter" class="nbhd-filter" placeholder="filter…"></div>' +
      '<div class="nbhd-tray-row"><span class="nbhd-tray-label">Models</span>' +
      '<div class="nbhd-chips">' + this._chips("model", c.models) + "</div></div>" +
      '<div class="nbhd-tray-row"><span class="nbhd-tray-label">Data sources</span>' +
      '<div class="nbhd-chips">' + this._chips("source", c.sources) + "</div></div></div>";
  },

  _bind(host) {
    const filter = host.querySelector("#nbhd-filter");
    if (filter) {
      filter.oninput = () => {
        const q = filter.value.trim().toLowerCase();
        host.querySelectorAll(".nbhd-chip").forEach((chip) => {
          const hit = !q || chip.getAttribute("data-value").toLowerCase().indexOf(q) >= 0;
          chip.style.display = hit ? "" : "none";
        });
      };
    }
    host.querySelectorAll(".nbhd-chip").forEach((chip) => {
      chip.onpointerdown = (ev) => this._startChip(ev, chip, host);
    });
    host.querySelectorAll(".graph-handle").forEach((handle) => {
      handle.onpointerdown = (ev) => this._startWire(ev, handle, host);
    });
  },

  _canvas(host) { return host.querySelector(".nbhd-canvas"); },

  // --- dragging a tray chip onto a band -----------------------------------

  // The chip gesture is GraphWire's; what is local is the hit-test, because here a
  // drop only counts on a band the chip's kind is allowed on — that band is what
  // fixes the direction of the declaration.
  _startChip(ev, chip, host) {
    const kind = chip.getAttribute("data-kind");
    const allow = kind === "source" ? ["sources"] : ["upstream", "downstream"];
    GraphWire.startChip(ev, {
      chip: chip, host: host, canvas: this._canvas(host), dropClass: "nbhd-drop",
      target: (e) => {
        const el = document.elementFromPoint(e.clientX, e.clientY);
        const band = el && el.closest ? el.closest("[data-band]") : null;
        return band && allow.indexOf(band.getAttribute("data-band")) >= 0 ? band : null;
      },
      onDrop: (value, band) =>
        this._declareFromChip({ kind: kind, value: value }, band.getAttribute("data-band")),
    });
  },

  // --- dragging a wire from one node to another ---------------------------

  // The gesture itself is GraphWire's — the Model Chain screen wires nodes the
  // same way, and one copy of it is what keeps the two consistent.
  _startWire(ev, handle, host) {
    const node = handle.closest("[data-node]");
    GraphWire.start(ev, {
      host: host, svg: host.querySelector(".nbhd-svg"), canvas: this._canvas(host),
      from: handle.getAttribute("data-handle"),
      x0: parseFloat(node.getAttribute("data-x")) + this._nbhd._W,
      y0: parseFloat(node.getAttribute("data-y")) + this._nbhd._H / 2,
      onConnect: (from, to) => this._declareFeed(from, to),
    });
  },

  // --- the declarations themselves ----------------------------------------

  _refresh() {
    // Re-render the whole tab: the registers under the canvas and the tab's own
    // count are showing the same declaration, so redrawing only the graph would
    // leave them stale.
    if (typeof Detail !== "undefined") Detail.show(Detail._id, "connections", { scroll: false });
  },

  _declareFromChip(d, band) {
    const focus = this._nbhd._n.focus.model_id;
    if (d.kind === "source") {
      this._post(focus, "data_sources",
        { data_source: d.value },
        "Declare " + d.value + " as a data source of " + focus + ".");
      return;
    }
    // The declaration is recorded on the focus either way; the direction is what
    // the band means. "upstream" = the dropped model feeds the focus.
    const direction = band === "upstream" ? "upstream" : "downstream";
    const arrow = direction === "upstream" ? d.value + " → " + focus : focus + " → " + d.value;
    this._post(focus, "dependencies", { direction: direction, model_id: d.value },
      "Declare the dependency " + arrow + ".");
  },

  // Wiring A onto B is recorded on A as a downstream dependency, which is the
  // same edge the chain derives either way — the graph dedupes reciprocals.
  _declareFeed(from, to) {
    this._post(from, "dependencies", { direction: "downstream", model_id: to },
      "Declare the dependency " + from + " → " + to + ".");
  },

  _post(modelId, collection, fields, summary) {
    App.amend(summary, "POST",
      "/api/models/" + encodeURIComponent(modelId) + "/collections/" + collection,
      { fields: fields }, () => this._refresh());
  },
};
