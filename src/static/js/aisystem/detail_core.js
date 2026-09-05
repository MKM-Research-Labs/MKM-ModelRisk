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

// The AI System detail view.
//
// Built on RecordDetail (the fetch/render/close sequence) and DetailShell (the tab
// strip, the field row, the inline editor), so what is written here is only what is
// actually particular to an AI System: which tabs it carries and what each draws.
//
// The tab order is the order a reviewer asks the questions in. Overview says what it
// is; The AI system says what it is built on and whether that can change; Exposure
// says what leaves the firm and under what law; Controls says what stands between the
// two. Tools comes next and only where the system has any -- a tab offering an empty
// list to a summariser is noise on every record that is not agentic.
const AISystemDetail = RecordDetail.attach({
  _LEFT: ["foundation_model", "provider", "pinned_version", "version_policy",
          "hosting", "deployment_pattern", "use_case"],
  _RIGHT: ["division", "line_of_business", "owner", "peer_reviewer", "tier",
           "materiality", "complexity", "rag_rating", "lifecycle_stage"],
  _EXPOSURE: ["data_egress", "data_egress_basis", "eu_ai_act_class",
              "eu_ai_act_rationale"],
  _CONTROLS: ["human_oversight", "guardrails", "grounding", "output_variability",
              "explainability_approach"],
  _TESTING: ["unit_tests", "integration_tests", "benchmark_tests"],

  _agentic() {
    const d = this._record.data || {};
    return /Agentic|Multi-agent/.test(d.deployment_pattern || "");
  },

  _header(d) {
    return '<div class="row" style="align-items:center">' +
      '<h3 style="margin:0">' + esc(this.recordId()) + " — " + fieldDisplay(d.name) +
      "</h3>" +
      '<span style="margin-left:var(--space-5)">' + tierBadge(d.tier, d.division) + " " +
      ragBadge(d.rag_rating, d.division) + " " +
      (this._record.retired ? '<span class="pill">retired</span>'
        : optionLabel(AISystems.fieldSpec("lifecycle_stage"), d.lifecycle_stage)) +
      "</span>" +
      '<span style="flex:1"></span>' +
      '<button class="btn small ghost" id="ais-content-close">Close</button></div>';
  },

  _tabbar(d) {
    const n = (k) => (d[k] || []).length;
    const asked = d.ai_review_questions || [];
    const tabs = [
      ["overview", "Overview", null],
      ["system", "The AI system", null],
      ["exposure", "Exposure", null],
      ["controls", "Controls", null],
    ];
    // Only where it can act. An empty Tools tab on a summariser invites somebody to
    // fill it in, and there is nothing true to put there.
    if (this._agentic()) tabs.push(["agent_tools", "Tools", n("agent_tools")]);
    // The tab bar mirrors a model's, because an AI System is a model-governed record
    // and is reviewed identically. Assumptions, the questions, weaknesses, limitations
    // and remediation are NOT tabs: they are stages of the review, reached through it,
    // each with its interim approval and its record of challenge. They were top-level
    // here, which let somebody fill in the registers without a review ever happening —
    // and left nobody able to say how far through a review actually was.
    tabs.push(
      ["review", "Review",
       asked.filter((q) => q.status === "Addressed").length + "/" + asked.length],
      ["risk", "Risk", null],
      ["data_sources", "Data sources", n("data_sources")],
      ["fairness_assessments", "Fairness", n("fairness_assessments")],
      ["evaluations", "Evaluations", n("evaluations")],
      ["docs", "Docs", DocLinks.countIn(d.documents, this._specs.doc_tab_categories)],
      ["changes", "Changes", null],
      ["audit", "Audit", null],
      ["danger", "Danger", null]);
    return DetailShell.tabBar(tabs, this._tab, "data-aistab");
  },

  _bindEdits() {
    if (this._record.retired) return;
    const self = this;
    const d = this._record.data || {};
    document.querySelectorAll("#ais-content [data-edit]").forEach(function (btn) {
      const key = btn.getAttribute("data-edit");
      btn.onclick = function () {
        DetailShell.fieldEditor({
          scope: "#ais-content", prefix: "aised", spec: AISystems.fieldSpec(key),
          current: d[key], division: d.division, withSave: true,
          onCancel: () => self._renderContent(),
          onSave: (value, shown) => self.saveField(
            key, value,
            "Set " + AISystems.fieldSpec(key).label + ' = "' + shown + '" on ' +
            self.recordId() + "."),
        });
      };
    });
  },

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
      DetailShell.retiredFlag(this._record.retired);
  },




  // A short note above a group of fields, saying what the group is for. These read as
  // the reviewer's own question rather than as a caption, because the fields below
  // them are prose and a blank textarea gets filled with whatever the owner assumes
  // was being asked.
  _lead(text) {
    return '<p class="muted" style="font-size:var(--size-sm);margin:0 0 var(--space-4)">' +
      text + "</p>";
  },

  // Which regimes bite, and why. Resolved server-side: applicability is config the
  // institution can extend, and a copy of the rules in the console would answer
  // differently the moment somebody added a regime.
  async _loadRegimes() {
    const box = document.getElementById("ais-regimes");
    if (!box) return;
    try {
      const body = await App.get("/api/ai-systems/" +
        encodeURIComponent(this.recordId()) + "/regimes");
      if (!body.regimes.length) {
        box.className = "empty";
        box.textContent = "No regime applies on the markets recorded for this system.";
        return;
      }
      box.className = "";
      box.innerHTML = body.regimes.map((r) =>
        '<div class="inforow"><div class="k">' + esc(r.name) + '</div><div class="v">' +
        esc(r.because) + '<span class="muted" style="font-size:var(--size-xs)"> &middot; ' +
        r.clauses + " obligations</span></div></div>").join("");
    } catch (e) {
      box.className = "empty";
      box.textContent = e.message;
    }
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
        '<div class="section-header" style="margin-top:var(--space-8)">Testing</div>' +
        this.fieldRows(this._TESTING);
      this._bindEdits(); return;
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
        this.fieldRows(this._CONTROLS);
      this._bindEdits(); return;
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
      box.innerHTML = '<div id="ais-changes"></div>';
      Changes.render("ai_system", this.recordId(), "ais-changes",
                     this._record.retired);
      return;
    }
    if (this._tab === "audit") { box.innerHTML = DetailTabs.audit(this._audit); return; }
    if (this._tab === "danger") {
      box.innerHTML = '<div class="section-header">Retire</div>' +
        this._lead("A retired AI System leaves the estate and every figure drawn from " +
                   "it. The record survives in the log and can be brought back.") +
        (this._record.retired
          ? '<div class="empty">Already retired.</div>'
          : '<button class="btn danger" id="ais-retire">Retire this AI System&hellip;</button>');
      const btn = document.getElementById("ais-retire");
      if (btn) btn.onclick = () => this.retire("AI System");
      return;
    }
    // Everything else is a collection, rendered and bound by the shared machinery.
    this.renderCollection(this._tab, {autosave: this._tab === "review"});
  },
}, {
  api: "/api/ai-systems",
  idKey: "ai_system_id",
  listEl: "ais-listview",
  detailEl: "ais-detail",
  contentEl: "ais-content",
  tabAttr: "data-aistab",
  specs: () => AISystems._specs || AISystems.specs(),
  fieldSpec: (key) => AISystems.fieldSpec(key),
  onClose: () => AISystems.loadList(),
});

// The Review tab: the shared review panel (review_panel.js), the same workflow a model's
// review runs. The defaults in the contract already suit a RecordDetail screen, so the
// only thing supplied here is the list refresh after an interim approval — the list
// column shows review status, and it is stale the moment a stage is agreed.
Object.assign(AISystemDetail, ReviewPanelContract, ReviewPanel, {
  _rvAfterApprove() { if (typeof AISystems !== "undefined") AISystems.loadList(); },
});
