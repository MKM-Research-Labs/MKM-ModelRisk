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

// The pieces every aggregate detail screen builds its body out of: a field row and its
// edit affordance, the responsible-committee rows, the risk table, and a collection
// rendered and bound.
//
// record_detail.js owns the SEQUENCE — fetch the record, swap the list for the detail,
// draw, put the list back. These are what the drawing step has to hand. They drifted
// into that file one at a time until it owned both, which is how a file that describes
// itself as one thing ends up being two.
//
// The line between this and DetailShell is not "shared markup" — DetailShell owns
// markup that needs no record (a tab strip, a field row, an inline editor), and these
// need the record: they read this._record, this._specs and this._cfg, and saveField
// redraws from the server rather than from what was typed, because the write may have
// moved something the screen did not touch.
//
// Retiring is not here either, and that absence is the same design record_detail.js
// notes: it is the committee's decision, so a screen asks through DangerZone.
//
// Assigns onto RecordDetail.methods, so it must load after record_detail.js and before
// the first RecordDetail.attach() caller.

Object.assign(RecordDetail.methods, {

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
      // An immutable field is shown and never offered for editing: the domain refuses
      // the edit, and an "edit" link that can only fail is worse than none.
      return DetailShell.row(key, riskFieldLabel(spec, d.division),
                             shared === null ? optionLabel(spec, d[key]) : shared,
                             !this._record.retired && !spec.immutable);
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
        // Every record is signed off by the committee it is assigned to, so there is
        // nothing to explain beyond which one that is.
        const why = "";
        return '<div class="inforow"><div class="k">MRC</div><div class="v">' +
          esc(c.name || c.value) + ' <span class="pill">' + esc(c.value) + "</span> " +
          '<span class="muted" style="font-size:var(--size-xs)">' + esc(m.level || "") +
          "-level</span>" + why + "</div></div>";
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
});
