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

// What each of an AI System's tabs draws.
//
// Split from detail_core.js, which says which tabs the record carries and how its
// header and fields are edited. This says what is behind each one — a single
// dispatch, because the tab strip is the reviewer's running order and reading it in
// one place is how you check that the order still holds.
//
// The panels themselves mostly come from elsewhere: the shared collection machinery,
// ModelDocs, DangerZone, and the three AI-specific loaders in detail_governance.js.
// What is written here is the framing around them — the section headings and the
// short lead under each, which are the reviewer's question in words.
//
// Assigns onto AISystemDetail; loads after detail_core.js.

Object.assign(AISystemDetail, {

  _overview() {
    const d = this._record.data || {};
    const summary = '<div style="margin-bottom:var(--space-7)">' +
      DetailShell.row("description", "Summary", fieldDisplay(d.description),
                      !this._record.retired) + "</div>";
    return summary +
      '<div class="grid2"><div><div class="section-header">What it is</div>' +
      this.fieldRows(["use_case", "foundation_model", "pinned_version",
                  "deployment_pattern", "hosting", "data_egress"]) + "</div>" +
      '<div><div class="section-header">Governance</div>' +
      this.mrcRow("AI System") + this.fieldRows(this._RIGHT) + this.mrcStatusRow() +
      this.fieldRow("next_review_date") + "</div></div>" +
      '<div class="section-header" style="margin-top:var(--space-8)">' +
      "Classification &amp; AI complexity</div>" +
      this._lead("Which side of the SR 26-2 line this system sits on, and how much of " +
                 "its path it chooses and how often it runs. With materiality, those " +
                 "place it on the grid that sets how much evidence it owes.") +
      this.fieldRows(this._AI_CLASS) + this._gridRow() +
      DetailShell.retiredFlag(this._record.retired);
  },

  // Resolved server-side from the grid tables; the console only draws it. An unplaced
  // system says what is missing rather than showing an empty cell.
  _gridRow() {
    const g = this._record.grid || {};
    const value = g.placed
      ? esc(g.position) + ' <span class="pill">' + esc(g.intensity) + "</span>" +
        '<div class="muted" style="font-size:var(--size-xs);margin-top:var(--space-2)">' +
        "Asks for evidence on concepts " + esc((g.concepts || []).join(", ")) + "</div>"
      : '<span class="muted">' + esc(g.position || "Not placed") +
        (g.missing && g.missing.length ? " &mdash; missing " + esc(g.missing.join(", ")) : "") +
        "</span>";
    return DetailShell.row("grid", "Grid position", value, false);
  },




  // A short note above a group of fields, saying what the group is for. These read as
  // the reviewer's own question rather than as a caption, because the fields below
  // them are prose and a blank textarea gets filled with whatever the owner assumes
  // was being asked.
  _lead(text) {
    return '<p class="muted" style="font-size:var(--size-sm);margin:0 0 var(--space-4)">' +
      text + "</p>";
  },

  _renderContent() {
    const d = this._record.data || {};
    const box = document.getElementById("ais-content");
    if (this._tab === "overview") {
      box.innerHTML = this._overview(); this._bindEdits(); return;
    }
    if (this._tab === "system") {
      box.innerHTML = '<div class="section-header">What it is built on</div>' +
        this._lead("The model, who provides it, and whether it can change under you. " +
                   "A version with no policy behind it is an accident rather than a control.") +
        this.fieldRows(this._LEFT) +
        '<div class="section-header" style="margin-top:var(--space-8)">Configuration history</div>' +
        this._lead("Each version of the configuration this system has run under. A " +
                   "snapshot cannot be edited once taken &mdash; that is what makes it " +
                   "evidence of what the system was, rather than a note about it.") +
        '<div id="ais-snapshots" class="empty">Loading&hellip;</div>' +
        (this._record.retired ? "" :
          '<button class="btn small" id="ais-snapshot" style="margin-top:var(--space-4)">' +
          "Take a snapshot&hellip;</button>") +
        '<div class="section-header" style="margin-top:var(--space-8)">Variability envelope</div>' +
        this._lead("How much the output moves under a pinned configuration. Measured " +
                   "over repeated runs, and bound to the configuration it was measured " +
                   "under &mdash; when that moves, the envelope describes a system " +
                   "that no longer exists.") +
        '<div id="ais-envelope" class="empty">Loading&hellip;</div>' +
        this._envelopeControls() +
        '<div class="section-header" style="margin-top:var(--space-8)">Testing</div>' +
        this.fieldRows(this._TESTING);
      this._bindEdits();
      this._loadSnapshots();
      this._loadEnvelope();
      this._bindEnvelopeControls();
      return;
    }
    if (this._tab === "exposure") {
      box.innerHTML = '<div class="section-header">Regulatory regimes</div>' +
        '<p class="muted" style="font-size:var(--size-sm)">Derived from where this ' +
        "system is used and what it does &mdash; not ticked. Change the markets it " +
        "serves and this changes with them.</p>" +
        '<div id="ais-regimes" class="empty">Loading&hellip;</div>' +
        '<div class="section-header" style="margin-top:var(--space-8)">What leaves the firm</div>' +
        this._lead("What is sent for inference, what in the contract permits it, and " +
                   "which regulatory class the system falls into. &ldquo;Not assessed&rdquo; " +
                   "is the absence of the assessment, not a class.") +
        this.fieldRows(this._EXPOSURE);
      this._bindEdits();
      this._loadRegimes();
      return;
    }
    if (this._tab === "controls") {
      box.innerHTML = '<div class="section-header">What stands in the way</div>' +
        this._lead("Where the human is, what filters the input and output, how the " +
                   "answer is grounded, and how you would know it had stopped working.") +
        this.fieldRows(this._CONTROLS) +
        '<div class="section-header" style="margin-top:var(--space-8)">Triggers</div>' +
        this._lead("The bar each property is judged against, and what happens when it " +
                   "breaks. A property with no bar set is listed too: that is the gap " +
                   "worth seeing.") +
        this._triggersPanel(d);
      this._bindEdits(); this._bindTriggers(); return;
    }
    if (this._tab === "evidence") {
      box.innerHTML = this._evidenceTab(); this._bindEvidence(); return;
    }
    if (this._tab === "risk") {
      box.innerHTML = '<div class="section-header">Risk assessment</div>' +
        this._lead("The owner sets these; they place the AI System on the heatmap " +
                   "below, which becomes its rating once the MRC signs it off.") +
        policyNotice(d.division) + this.riskTable() +
        DetailTabs.risk(this._risk, false, d.division);
      this._bindEdits(); return;
    }
    if (this._tab === "docs") {
      // The record's evidence pack: red-team results, the provider's model card, the
      // contract clause the Exposure tab refers to. No generated AI System Document
      // yet -- a model, a product and an ML Application each render one, and what an
      // AI System's should contain is a governance question rather than a template
      // one. Its absence is stated here rather than left as a missing button.
      box.innerHTML =
        '<p class="muted" style="font-size:var(--size-sm);margin:0 0 var(--space-5)">' +
        "Evidence filed against this record. There is no generated AI System Document " +
        "yet &mdash; what one should contain is still an open question.</p>" +
        '<div id="aisdocs-host"></div>';
      ModelDocs.render(this.recordId(), d.documents || [],
                       this._specs.doc_tab_categories || [], this._record.retired,
                       "/api/ai-systems/", () => this.refresh(), "aisdocs-host");
      return;
    }
    if (this._tab === "review") {
      box.innerHTML = this._reviewTab(d);
      this._bindReviewRail();
      return;
    }
    if (this._tab === "changes") {
      box.innerHTML = '<div id="ais-changes"></div>' +
        '<div class="section-header" style="margin-top:var(--space-8)">Releases</div>' +
        this._lead("What each release contained, sealed at the time. Sealed, not " +
                   "saved &mdash; a manifest that could be edited afterwards would be " +
                   "a note about the release rather than a record of it.") +
        this._releasesPanel(d);
      Changes.render("ai_system", this.recordId(), "ais-changes",
                     this._record.retired);
      this._bindReleases();
      return;
    }
    if (this._tab === "audit") { box.innerHTML = DetailTabs.audit(this._audit); return; }
    // Retiring an AI System is the MRC's decision, exactly as it is for a model, so
    // the tab is DangerZone's three states rather than a button of its own.
    if (this._tab === "danger") {
      box.innerHTML = DangerZone.content("AI System", this._record);
      DangerZone.bind({
        api: "/api/ai-systems", id: this.recordId(),
        onDone: () => { this.show(this.recordId(), "danger"); AISystems.loadList(); },
      });
      return;
    }
    // Everything else is a collection, rendered and bound by the shared machinery.
    this.renderCollection(this._tab, {autosave: this._tab === "review"});
  },
});
