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
// What a host screen must provide to run a review.
//
// Split out of review_panel.js so that the panel's own workings and the seam every
// host screen implements are read separately: a screen author needs this file and
// none of the other three.
//
// The defaults suit a RecordDetail-based screen (the ML Application and AI System
// details), so those two supply nothing at all; the model's Detail predates
// RecordDetail and overrides the six that differ.
//
// Loads before review_panel.js and before any screen that mixes them in.
const ReviewPanelContract = {
  // --- The review's shape, from the record type's own /fields payload -------
  _rvSpecs() { return this._specs || {}; },
  _rvStages() {
    // Numbered here rather than served numbered: the number is a position in the rail,
    // which is a fact about the screen, not about the workflow. Sign-off closes the
    // rail and is not a stage the server approves, so it is appended here.
    const stages = (this._rvSpecs().review_stages || []).map((s, i) =>
      ({ key: s.key, label: s.label, n: i }));
    return stages.concat([{ key: "signoff", label: "Sign-off", n: stages.length }]);
  },
  _rvQuestionsKey() { return this._rvSpecs().review_questions_collection; },
  _rvVerdicts() { return this._rvSpecs().reviewer_verdicts || []; },
  _rvTriggers() { return this._rvSpecs().review_triggers || []; },
  _rvBriefFields() { return this._rvSpecs().review_brief_fields || []; },
  _rvChecklist() { return this._rvSpecs().new_version_checklist || []; },
  _rvNewVersionTrigger() { return this._rvSpecs().new_version_trigger; },

  // --- The record the panel is reviewing -----------------------------------
  _rvRecord() { return this._record; },
  _rvSet(record) { this._record = record; },
  _rvData() { return (this._rvRecord() || {}).data || {}; },
  _rvRetired() { return !!(this._rvRecord() || {}).retired; },
  _rvId() { return this.recordId(); },
  _rvApi() { return this._cfg.api + "/"; },

  // --- Element scoping -----------------------------------------------------
  // Every id this panel emits is prefixed with the host's content element, and every
  // lookup is scoped to it. Without that they are global: switching main tabs leaves
  // the previous screen's detail in the DOM, so a second screen rendering its review
  // found the FIRST screen's "review-stage" and wrote into a hidden container. The
  // ML Application's review body vanished that way while the model's stale detail
  // silently absorbed it.
  _rvPfx() { return this._cfg.contentEl + "-"; },
  _rvScope() { return document.getElementById(this._cfg.contentEl) || document; },
  _rvEl(id) { return this._rvScope().querySelector("#" + CSS.escape(this._rvPfx() + id)); },
  _rvVal(id) {
    const el = this._rvEl(id);
    if (!el) return "";
    if (el.multiple) return [...el.selectedOptions].map((o) => o.value);
    return el.value.trim();
  },
  _rvAll(selector) { return this._rvScope().querySelectorAll(selector); },

  // --- Redrawing ------------------------------------------------------------
  _rvRerender() { this._render(); },
  // Refetch and redraw in place. Deliberately not the screen's own show(), which
  // resets the open tab to the overview — reloading after posting a note would throw
  // the reviewer out of the review they are in the middle of.
  async _rvReload() {
    try {
      this._rvSet(await App.get(this._rvApi() + this._rvId()));
      this._rvRerender();
    } catch (e) { App.toast(e.message, "error"); }
  },
  // Run after an interim approval, for screens whose list shows review status.
  _rvAfterApprove() {},

  // --- Fields and collections ----------------------------------------------
  _rvRow(key) { return this.fieldRow(key); },
  _rvBindEdits() { if (this._bindEdits) this._bindEdits(); },
  _rvColl(key, d) {
    return Collections.render(d, { collections: [this.collSpec(key)] }, this._rvRetired());
  },
  _rvBindColls(keys) { this.bindCollections(keys); },

  // The owner's half of the questions stage: status and rationale, saved as they are
  // typed. The reviewer's half posts to its own endpoint, which stamps who and when —
  // see _bindVerdictSaves. Updating a question is a non-critical edit, so it applies
  // without a confirmation dialog.
  // Which questions the questions stage shows, and anything to say above them. The
  // ML Application filters by its division's review policy — a question switched off
  // is hidden, never removed — so the stage has to ask rather than read the
  // collection directly.
  _rvQuestions(d) { return d[this._rvQuestionsKey()] || []; },
  _rvQuestionsLead() { return ""; },

  // What the statistics say about this record. A measure that could not be computed
  // prints WHY: an absent stability index and an index of zero are different claims,
  // and a monitoring pack that cannot tell them apart is worse than one reporting
  // nothing.
  async _loadMeasured() {
    const box = this._rvEl("measured");
    if (!box) return;
    try {
      const position = await App.get(this._rvApi() + this._rvId() + "/monitoring");
      if (!position.results.length) {
        box.className = "empty";
        box.textContent = position.why;
        return;
      }
      const rows = position.results.map((r) => {
        const value = r.value === null ? "&mdash;"
          : String(Math.round(r.value * 10000) / 10000);
        const basis = typeof r.detail === "string" ? r.detail
          : (r.status === "ok" ? "" : r.status);
        return "<tr><td>" + esc(r.field || "") + "</td><td>" + esc(r.measure) +
          "</td><td>" + value + "</td><td>" +
          (r.rag ? '<span class="badge" style="background:' +
            (Theme.colour("rag", r.rag) || Theme.value("grey")) + '">' + esc(r.rag) +
            "</span>" : "&mdash;") + "</td><td>" + esc(basis) + "</td></tr>";
      }).join("");
      box.className = "";
      box.innerHTML = '<table style="table-layout:fixed;width:100%"><thead><tr>' +
        "<th>Field</th><th>Measure</th><th>Value</th><th>Rating</th><th>Basis</th>" +
        "</tr></thead><tbody>" + rows + "</tbody></table>";
    } catch (e) {
      box.className = "empty";
      box.textContent = e.message;
    }
  },

  _rvBindOwnerAnswers() {
    if (this._rvRetired()) return;
    const self = this;
    const save = async function (itemId) {
      try {
        const updated = await App.send(
          "POST", self._rvApi() + self._rvId() + "/collections/" +
          self._rvQuestionsKey() + "/" + itemId,
          { fields: { status: self._rvVal("vq-" + itemId + "-status"),
                      rationale: self._rvVal("vq-" + itemId + "-rationale") } });
        self._rvSet(updated);
        if (typeof MrcNav !== "undefined") MrcNav.invalidate();
        if (typeof Nav !== "undefined") Nav.markAllDirty();
        App.toast("Change recorded in the audit trail", "ok");
        self._rvRerender();
      } catch (e) {
        App.toast(e.message, "error");
      }
    };
    self._rvAll("select[data-vq-item], input[data-vq-item], textarea[data-vq-item]")
      .forEach(function (el) { el.onchange = () => save(el.getAttribute("data-vq-item")); });
  },
};
