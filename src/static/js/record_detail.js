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

// The lifecycle every aggregate detail screen repeats: fetch the record with its
// audit trail, risk rating and responsible committee; swap the list view for the
// detail; draw a header, a tab bar and a body; and put the list back on close.
//
// DetailShell owns the MARKUP these screens share (the tab strip, a field row, the
// inline editor). This owns the SEQUENCE. They were separated on purpose and stay
// separated: a screen can want one without the other.
//
// What differs between screens is small and enumerable -- which endpoint, which id
// field, which DOM nodes, which data attribute the tab clicks carry -- so those are
// config. What genuinely differs in kind is the header, the tab bar and the body, so
// those stay with the screen as hooks. Five values and three hooks; the moment this
// needs a sixth flag to express a difference, the difference belongs in the screen.
//
// Extracted when the AI System screen arrived and would otherwise have been the
// fourth copy of this sequence.
const RecordDetail = {
  // Mixed into a screen object. ``cfg`` is {api, idKey, listEl, detailEl, contentEl,
  // tabAttr, specs}; ``specs`` is a function returning the field specs, because a
  // screen fetches those its own way and may cache them.
  attach(screen, cfg) {
    screen._cfg = cfg;
    screen._record = null;
    screen._tab = "overview";
    screen._specs = null;
    screen._audit = [];
    screen._risk = null;
    screen._mrc = null;
    Object.keys(RecordDetail.methods).forEach((name) => {
      if (screen[name] === undefined) screen[name] = RecordDetail.methods[name];
    });
    return screen;
  },

  methods: {
    collSpec(key) { return this._specs.collections.find((c) => c.key === key); },

    recordId() { return (this._record || {})[this._cfg.idKey]; },

    _url(id, suffix) {
      return this._cfg.api + "/" + encodeURIComponent(id) + (suffix || "");
    },

    // ``tab`` reopens on a named tab rather than the Overview. A write raised from
    // a tab redraws from the server, and landing back on the Overview loses the place
    // of whoever pressed the button.
    async show(id, tab) {
      this._specs = this._specs || await this._cfg.specs();
      // One round trip for the four things every detail screen opens with. Sequential
      // fetches here are four times the latency for no benefit -- nothing among them
      // depends on another.
      const [record, audit, risk, mrc] = await Promise.all([
        App.get(this._url(id)),
        App.get("/api/audit"),
        App.get(this._url(id, "/risk-rating")),
        App.get(this._url(id, "/mrc")),
      ]);
      this._record = record;
      this._mrc = mrc;
      this._audit = audit.filter((e) => e.aggregate_id === id);
      this._risk = risk;
      this._tab = tab || "overview";
      // style.display, not a "hidden" class. There is no generic `.hidden` rule in
      // the stylesheet -- only `.overlay.hidden` and `.toast.hidden` -- so adding the
      // class to a plain div does nothing at all, and the list stayed on screen
      // underneath the detail. The ML Application screen shipped with exactly that
      // bug and it is fixed by this line rather than in three places.
      document.getElementById(this._cfg.listEl).style.display = "none";
      this._render();
    },

    // Back to the list, without telling the screen to reload. Separate from
    // ``close`` because returning to a TAB is not the same act as closing a record:
    // one is navigation and the other is the user finishing with something, and only
    // the second should refetch.
    // Null-safe: this runs on every visit to the tab, including the first, when the
    // panel has not been rendered yet and neither element exists. Throwing there
    // aborted the render that was about to create them, and the tab came up blank.
    resetToList() {
      const detail = document.getElementById(this._cfg.detailEl);
      if (detail) detail.innerHTML = "";
      const list = document.getElementById(this._cfg.listEl);
      if (list) list.style.display = "";
    },

    close() {
      this.resetToList();
      this._cfg.onClose();
    },

    async refresh() { await this.show(this.recordId()); },

    _render() {
      const d = this._record.data || {};
      document.getElementById(this._cfg.detailEl).innerHTML =
        '<div class="card">' + this._header(d) + this._tabbar(d) +
        '<div id="' + this._cfg.contentEl + '" style="margin-top:var(--space-7)"></div></div>';
      document.getElementById(this._cfg.contentEl + "-close").onclick = () => this.close();
      // _render, not _renderContent: the tab bar carries the active marker, so drawing
      // only the body leaves the underline on whichever tab was open before.
      const attr = this._cfg.tabAttr;
      document.querySelectorAll("[" + attr + "]").forEach((b) => {
        b.onclick = () => { this._tab = b.getAttribute(attr); this._render(); };
      });
      this._renderContent();
    },

    // Retiring is not here, and that absence is the design: it is the committee's
    // decision, so a screen asks for it through DangerZone rather than posting a
    // retire of its own.
  },
};
