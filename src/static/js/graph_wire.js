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

// Dragging a connection between two nodes of a hand-drawn SVG graph. Shared by the
// per-model neighbourhood and the whole-estate Model Chain, which draw different
// pictures of the same declarations and should not each grow their own copy of the
// gesture. There is no drag-and-drop library here, and HTML5 dnd does not reach
// into an SVG cleanly, so this is plain pointer events.
//
// The host graph supplies: an <svg> holding a <g class="graph-rubber"> for the
// rubber line, nodes carrying data-node="<id>", and a handle inside each node. It
// gets back onConnect(fromId, toId) once a drag ends on a different node.
const GraphWire = {
  _drag: null,

  // ``opts``: {host, svg, from, x0, y0, onConnect}. x0/y0 are where the line is
  // anchored, in the SVG's own coordinates.
  start(ev, opts) {
    ev.preventDefault();
    ev.stopPropagation();
    this._drag = opts;
    if (opts.canvas) opts.canvas.classList.add("graph-wiring");
    this._onMove = (e) => this._move(e);
    this._onUp = (e) => this._up(e);
    window.addEventListener("pointermove", this._onMove);
    window.addEventListener("pointerup", this._onUp);
  },

  // Screen pixels into the SVG's own coordinates, so the rubber line tracks the
  // pointer however the canvas is scrolled or scaled.
  _point(svg, ev) {
    const ctm = svg.getScreenCTM();
    if (!ctm) return { x: 0, y: 0 };
    const inv = ctm.inverse();
    return { x: ev.clientX * inv.a + ev.clientY * inv.c + inv.e,
             y: ev.clientX * inv.b + ev.clientY * inv.d + inv.f };
  },

  // The rubber line is pointer-events:none in CSS; without that it would end under
  // the pointer and win the hit-test against the very node being dropped on.
  _nodeUnder(ev) {
    const el = document.elementFromPoint(ev.clientX, ev.clientY);
    const node = el && el.closest ? el.closest("[data-node]") : null;
    if (!node) return null;
    return node.getAttribute("data-node") === this._drag.from ? null : node;
  },

  _move(ev) {
    const d = this._drag;
    if (!d) return;
    d.host.querySelectorAll(".wire-target").forEach((el) => el.classList.remove("wire-target"));
    const p = this._point(d.svg, ev);
    const g = d.host.querySelector(".graph-rubber");
    if (g) {
      g.innerHTML = '<line x1="' + d.x0 + '" y1="' + d.y0 + '" x2="' + p.x + '" y2="' + p.y +
        '" stroke="#1976d2" stroke-width="2" stroke-dasharray="5 4"/>';
    }
    const node = this._nodeUnder(ev);
    if (node) node.classList.add("wire-target");
  },

  _up(ev) {
    const d = this._drag;
    if (!d) return;
    const target = this._nodeUnder(ev);
    this._cleanup();
    if (target) d.onConnect(d.from, target.getAttribute("data-node"));
  },

  _cleanup() {
    const d = this._drag;
    window.removeEventListener("pointermove", this._onMove);
    window.removeEventListener("pointerup", this._onUp);
    if (d) {
      if (d.canvas) d.canvas.classList.remove("graph-wiring");
      const rubber = d.host.querySelector(".graph-rubber");
      if (rubber) rubber.innerHTML = "";
      d.host.querySelectorAll(".wire-target").forEach((el) => el.classList.remove("wire-target"));
    }
    this._drag = null;
  },

  // Dragging a chip out of a tray and onto a canvas. The caller supplies the
  // hit-test, because what counts as a drop differs: the per-model canvas drops
  // onto a labelled band (which fixes the direction), the estate chain drops onto
  // the canvas itself (which only stages the model, leaving the direction to a
  // subsequent wire). ``opts``: {chip, host, canvas, dropClass, target(ev), onDrop}.
  startChip(ev, opts) {
    ev.preventDefault();
    this._chip = opts;
    this._chip.value = opts.chip.getAttribute("data-value");
    if (opts.canvas) opts.canvas.classList.add(opts.dropClass || "graph-dropping");
    this._ghost = document.createElement("div");
    this._ghost.className = "nbhd-ghost";
    this._ghost.textContent = this._chip.value;
    document.body.appendChild(this._ghost);
    this._onChipMove = (e) => this._chipMove(e);
    this._onChipUp = (e) => this._chipUp(e);
    window.addEventListener("pointermove", this._onChipMove);
    window.addEventListener("pointerup", this._onChipUp);
    this._chipMove(ev);
  },

  // The ghost follows the pointer, so it has to stand aside for the hit-test or it
  // would be the only thing ever found under it.
  _hit(ev) {
    if (this._ghost) this._ghost.style.display = "none";
    const found = this._chip.target(ev);
    if (this._ghost) this._ghost.style.display = "";
    return found;
  },

  _chipMove(ev) {
    if (!this._chip) return;
    if (this._ghost) {
      this._ghost.style.left = ev.clientX + 12 + "px";
      this._ghost.style.top = ev.clientY + 12 + "px";
    }
    this._chip.host.querySelectorAll(".drop-over").forEach((el) => el.classList.remove("drop-over"));
    const found = this._hit(ev);
    if (found && found.classList) found.classList.add("drop-over");
  },

  _chipUp(ev) {
    const c = this._chip;
    if (!c) return;
    const found = this._hit(ev);
    window.removeEventListener("pointermove", this._onChipMove);
    window.removeEventListener("pointerup", this._onChipUp);
    if (this._ghost) { this._ghost.remove(); this._ghost = null; }
    if (c.canvas) c.canvas.classList.remove(c.dropClass || "graph-dropping");
    c.host.querySelectorAll(".drop-over").forEach((el) => el.classList.remove("drop-over"));
    this._chip = null;
    if (found) c.onDrop(c.value, found);
  },

  // The arrow label both canvases use: what the handoff says crosses this edge, or
  // an invitation to say so. Kept here so the two graphs cannot word it differently.
  label(handoff) {
    const h = handoff || {};
    if (!h.declared || !h.field_count) return "state what crosses";
    return h.field_count + " field" + (h.field_count === 1 ? "" : "s") +
      (h.status && h.status !== "Draft" ? " · " + h.status : "");
  },
};
