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
  // Hand-curated, so a field added in config does NOT appear here on its own. The two
  // sampling fields sit with the model pin because they are the same kind of fact: what
  // the system was configured with, as opposed to how it is governed.
  _LEFT: ["foundation_model", "provider", "pinned_version", "version_policy",
          "sampling_params", "instruction_hierarchy",
          "hosting", "deployment_pattern", "use_case"],
  _RIGHT: ["division", "line_of_business", "functional_group", "owner",
           "peer_reviewer", "tier",
           "materiality", "complexity", "rag_rating", "lifecycle_stage"],
  // The SR 26-2 boundary and the AI complexity axis; grid position is drawn after them.
  _AI_CLASS: ["model_class", "ai_system_type", "ai_autonomy", "ai_usage_frequency"],
  _EXPOSURE: ["data_egress", "data_egress_basis", "eu_ai_act_class",
              "eu_ai_act_rationale"],
  _CONTROLS: ["human_oversight", "guardrails", "grounding", "output_variability",
              "explainability_approach"],
  _TESTING: ["unit_tests", "integration_tests", "benchmark_tests"],

  // Agentic by its classification or by its deployment pattern: the classification is
  // newer, and a record not yet classified must not lose the Tools tab it had.
  _agentic() {
    const d = this._record.data || {};
    return d.ai_system_type === "AGENTIC" || d.ai_autonomy === "AGENT" ||
      /Agentic|Multi-agent/.test(d.deployment_pattern || "");
  },

  _header(d) {
    return '<div class="row" style="align-items:center">' +
      '<h3 style="margin:0">' + esc(this.recordId()) + " — " + fieldDisplay(d.name) +
      "</h3>" +
      '<span style="margin-left:var(--space-5)">' + tierBadge(d.tier, d.division) + " " +
      ragBadge(d.rag_rating, d.division) + " " +
      (this._record.retired ? '<span class="pill">retired</span>'
        : fieldDisplay(Stages.labelFor(d.lifecycle_stage, d.division))) +
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
