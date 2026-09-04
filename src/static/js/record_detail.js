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

    close() {
      document.getElementById(this._cfg.detailEl).innerHTML = "";
      document.getElementById(this._cfg.listEl).style.display = "";
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

    // Save one field, then redraw from the server rather than from what was typed.
    // The record may have been changed by the write (a rating recomputed, a status
    // moved), and a screen that trusted the input would show a stale record that
    // looks authoritative.
    saveField(key, value, reason) {
      return App.amend(reason || ("Update " + key + "."), "POST",
        this._url(this.recordId(), "/field"), {field: key, value: value},
        () => this.refresh());
    },

    // One field row, drawn through the spec so a status vocabulary shows its label
    // rather than the word the record stores, and through DetailShell's shared value
    // cell so a risk dimension shows the band its division defined rather than the
    // score behind it.
    fieldRow(key) {
      const d = this._record.data || {};
      const spec = this._cfg.fieldSpec(key);
      if (!spec) return "";
      const shared = DetailShell.fieldValue(key, spec, d);
      return DetailShell.row(key, riskFieldLabel(spec, d.division),
                             shared === null ? optionLabel(spec, d[key]) : shared,
                             !this._record.retired);
    },

    fieldRows(keys) { return keys.map((k) => this.fieldRow(k)).join(""); },

    editLink(key) {
      return this._record.retired
        ? "" : '<span class="edit-btn" data-edit="' + key + '">edit</span>';
    },

    // The committee responsible for this record, derived from its Division and Line
    // of Business. Flags red where none covers it: a record no committee sees is
    // invisible to the governance meant to hold it, and that is worth shouting about
    // on the record itself rather than leaving to a report nobody runs.
    mrcRow(noun) {
      const m = this._mrc || {};
      if (m.mrc) {
        const c = m.mrc;
        return '<div class="inforow"><div class="k">MRC</div><div class="v">' +
          esc(c.name || c.value) + ' <span class="pill">' + esc(c.value) + "</span> " +
          '<span class="muted" style="font-size:var(--size-xs)">' + esc(m.level || "") +
          "-level</span></div></div>";
      }
      const d = this._record.data || {};
      const org = [d.division, d.line_of_business].filter(Boolean).join(" / ") ||
        "no division / line of business set";
      return '<div class="inforow"><div class="k">MRC</div>' +
        '<div class="v" style="color:var(--red)">&#9888; No committee covers this ' +
        noun + " (" + esc(org) + "). Set one up under Admin &rarr; MRC.</div></div>";
    },

    // The committee's latest word on this record.
    mrcStatusRow() {
      const d = this._record.data || {};
      const hist = d.signoff_history || [];
      const latest = hist.length ? hist[hist.length - 1] : null;
      let value = '<span class="muted">Not yet before a committee</span>';
      if (latest) {
        const outcome = latest.outcome || "Approved";
        const colour = outcome === "Rejected" ? "var(--red)" : Theme.value("green");
        value = '<span style="color:' + colour + ';font-weight:600">' + esc(outcome) +
          "</span> at " + '<span class="code">' + esc(latest.meeting_id) + "</span>" +
          (latest.date ? " (" + esc(latest.date) + ")" : "");
      }
      return '<div class="inforow"><div class="k">MRC status</div><div class="v">' +
        value + "</div></div>";
    },

    // The three dimensions on their heatmap, through the one engine a model, a
    // Product, an ML Application and an AI System all rate by.
    riskTable() {
      const d = this._record.data || {};
      const rag = (this._risk.heatmap || {}).rag;
      return riskAssessmentTable({
        data: d, division: d.division,
        spec: (key) => this._cfg.fieldSpec(key),
        editLink: (key) => this.editLink(key),
        ratingBadge: rag ? ragBadge(rag, d.division) : "",
      });
    },

    // A collection tab: render its section and wire its controls.
    //
    // Both arguments Collections expects are easy to get wrong and fail quietly.
    // It wants {collections: [spec]}, not a bare array -- given an array it reads
    // `specs.collections.map` on undefined and throws, and the caller has already
    // been left with an empty tab. And bind() wants a base URL ending in
    // "/collections/". The ML Application screen got both wrong and its Review tab
    // threw on every open; that is why this is written once here.
    renderCollection(key, opts) {
      const d = this._record.data || {};
      const spec = this.collSpec(key);
      const box = document.getElementById(this._cfg.contentEl);
      box.innerHTML = Collections.render(d, {collections: [spec]}, this._record.retired,
                                         false, (opts || {}).autosave || false);
      this.bindCollections([key]);
    },

    bindCollections(keys) {
      Collections.bind(
        this._cfg.api + "/" + encodeURIComponent(this.recordId()) + "/collections/",
        {collections: keys.map((k) => this.collSpec(k))},
        this._record.retired, () => this.refresh(), this._record.data);
    },

    // Retiring is not here, and that absence is the design: it is the committee's
    // decision, so a screen asks for it through DangerZone rather than posting a
    // retire of its own.
  },
};
