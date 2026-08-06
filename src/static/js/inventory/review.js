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

// Detail — the Review tab: a model review run as a workflow, one stage at a time.
//
// A review is five pieces of work in a fixed order — read the pack, answer the
// nine questions, agree the weaknesses, agree the limitations of use, agree how
// the model will be monitored — ending in a reviewer sign-off. They used to be
// scattered across three tabs and the Overview, which left nobody able to say how
// far through a review actually was. The rail below is that answer.
//
// This is the first increment: the rail and the stages, each showing the work it
// owns. Per-stage agreement, the reviewer's verdict on each question, the
// owner/reviewer challenge threads and the sign-off that files the report all
// follow (see docs/design/review-workflow.md).
const REVIEW_STAGES = [
  { key: "documents", n: 1, label: "Preliminary documents" },
  { key: "questions", n: 2, label: "The nine questions" },
  { key: "weaknesses", n: 3, label: "Model weaknesses" },
  { key: "limitations", n: 4, label: "Limitations of use" },
  { key: "monitoring", n: 5, label: "Monitoring approach" },
  { key: "signoff", n: 6, label: "Sign-off" },
];
const REVIEW_DOC_CATEGORY = "Review";
// The brief the owner writes before the review starts, and who is to do it by when.
const REVIEW_BRIEF_FIELDS = ["review_trigger", "review_scope", "peer_reviewer",
  "review_due_date"];
// Shown only for a new version: the three documents that go stale together.
const NEW_VERSION_CHECKLIST = ["review_docs_updated", "review_sensitivities_updated",
  "review_test_docs_updated"];
const NEW_VERSION_TRIGGER = "New version";

Object.assign(Detail, {
  // Which stage is open. Held on Detail (not in the URL) so switching model tabs
  // and coming back leaves the reviewer where they were.
  _reviewStage: "documents",

  _reviewTab(d) {
    const rail = REVIEW_STAGES.map((s) =>
      '<button class="dtab' + (s.key === this._reviewStage ? " active" : "") +
      '" data-rstage="' + s.key + '">' + s.n + ". " + esc(s.label) +
      this._stageBadge(s.key, d) + "</button>").join("");
    return '<p class="muted" style="font-size:12px;margin:0 0 8px">The review, in the order it ' +
      "runs. Each stage is agreed between the model owner and the reviewer before the review " +
      "moves on; the reviewer signs off at the end and the report goes to the MRC with the " +
      "risk rating.</p>" +
      '<div class="dtabs">' + rail + "</div>" +
      '<div id="review-stage" style="margin-top:12px"></div>';
  },

  // What the stage has to show for itself so far — a count, or nothing where a
  // count would mean nothing. Not a state: agreement comes in the next increment,
  // and a badge that looked like one would be claiming more than it knows.
  _stageBadge(key, d) {
    const n = (k) => (d[k] || []).length;
    // An agreed stage says so, in place of its count: once the reviewer has
    // approved it, how many rows it holds is no longer the interesting fact.
    if ((d.review_progress || []).some((r) => r.stage === key)) return " ✓";
    if (key === "documents") {
      return " (" + DocLinks.countIn(d.documents, [REVIEW_DOC_CATEGORY]) + ")";
    }
    if (key === "questions") {
      const vq = d.validation_questions || [];
      return " (" + vq.filter((q) => q.status === "Addressed").length + "/" + vq.length + ")";
    }
    if (key === "weaknesses") return " (" + n("model_weaknesses") + ")";
    if (key === "limitations") return " (" + n("limitations") + ")";
    return "";
  },

  _renderReviewStage() {
    const d = this._model.data || {};
    const box = document.getElementById("review-stage");
    const docOpts = {
      category: REVIEW_DOC_CATEGORY, docs: d.documents || [], base: "/api/models/",
      id: this._id, retired: this._model.retired,
      refresh: () => this.show(this._id, "review", { scroll: false }),
    };
    if (this._reviewStage === "documents") {
      box.innerHTML = '<div class="section-header">The brief</div>' +
        '<p class="muted" style="font-size:12px">What this review is for, who is doing it, and ' +
        "by when. A reviewer handed a model and no brief writes the review they imagine is " +
        "wanted.</p>" +
        REVIEW_BRIEF_FIELDS.map((k) => this._row(k, d)).join("") +
        this._newVersionChecklist(d) +
        '<div class="section-header" style="margin-top:16px">Preliminary documents</div>' +
        '<p class="muted" style="font-size:12px">The pack the reviewer works from. These are ' +
        "the review's own working papers — the model's documentation lives on the Docs tab.</p>" +
        DocPanel.html(docOpts) + this._stageApproval("documents", d);
      DocPanel.bind(docOpts);
      this._bindEdits();
      this._bindStageApproval("documents");
      return;
    }
    if (this._reviewStage === "questions") {
      box.innerHTML = DetailTabs.validation(d, this._model.retired) +
        this._stageApproval("questions", d);
      this._bindValidationSaves();
      this._bindStageApproval("questions");
      return;
    }
    if (this._reviewStage === "weaknesses") {
      box.innerHTML = '<p class="muted" style="font-size:12px">What the model does badly, or ' +
        "not at all &mdash; proposed by the owner, agreed with the reviewer.</p>" +
        this._collSection("model_weaknesses", d) + this._stageApproval("weaknesses", d);
      this._bindCollections(["model_weaknesses"]);
      this._bindStageApproval("weaknesses");
      return;
    }
    if (this._reviewStage === "limitations") {
      box.innerHTML = '<p class="muted" style="font-size:12px">Where the model may and may not ' +
        "be used, with the trigger that would surface a breach and the control that compensates.</p>" +
        this._collSection("limitations", d) + this._stageApproval("limitations", d);
      this._bindCollections(["limitations"]);
      this._bindStageApproval("limitations");
      return;
    }
    if (this._reviewStage === "monitoring") {
      box.innerHTML = '<div class="section-header">Monitoring approach</div>' +
        '<p class="muted" style="font-size:12px">How this model will be watched once it is in ' +
        "use, in your own words &mdash; what would be looked at, how often, and what would " +
        "prompt a second look.</p>" + this._row("monitoring_approach", d) +
        this._stageApproval("monitoring", d);
      this._bindEdits();
      this._bindStageApproval("monitoring");
      return;
    }
    // Sign-off is the next increment; say so plainly rather than showing an empty
    // panel that looks like a feature that failed to load.
    box.innerHTML = '<div class="section-header">Reviewer sign-off</div>' +
      '<div class="empty">Not built yet. The reviewer\'s final commentary, the sign-off gate ' +
      "and the Model Review Report the MRC receives land in a later increment.</div>";
  },

  // The three documents that go stale together when a model is re-versioned. The
  // owner ticks each; alongside the tick we show what is actually on file, so the
  // confirmation is made against the record rather than from memory.
  _newVersionChecklist(d) {
    if (d.review_trigger !== NEW_VERSION_TRIGGER) return "";
    const held = {
      review_docs_updated: DocLinks.countIn(d.documents, ["Core Documentation"]),
      review_sensitivities_updated: DocLinks.countIn(d.documents, ["Sensitivity"]),
      review_test_docs_updated: DocLinks.countIn(d.documents, ["Test Results"]),
    };
    return '<div class="section-header" style="margin-top:16px">New version checklist</div>' +
      '<p class="muted" style="font-size:12px">This review follows a new version, so the ' +
      "model's own documents need to have caught up with it. The count beside each is what " +
      "is on file today.</p>" +
      NEW_VERSION_CHECKLIST.map((k) =>
        this._row(k, d).replace("</div><span class=\"edit-btn\"",
          '<span class="muted" style="font-size:11px;margin-left:10px">' +
          held[k] + " on file</span></div><span class=\"edit-btn\"")).join("");
  },

  // The reviewer's interim approval of a stage: the button, or the record of the
  // approval already given. Not a lock — the stage stays editable afterwards, and
  // approving again after a reopening simply adds another row.
  _stageApproval(stageKey, d) {
    const given = (d.review_progress || []).filter((r) => r.stage === stageKey).slice(-1)[0];
    const label = REVIEW_STAGES.find((s) => s.key === stageKey).label;
    const record = given
      ? '<div class="muted" style="font-size:12px">Interim approval by <b>' +
        esc(given.approved_by || "") + "</b> on " + esc((given.approved_at || "").slice(0, 10)) +
        (given.note ? ' &mdash; "' + esc(given.note) + '"' : "") + "</div>"
      : '<div class="muted" style="font-size:12px">Not yet agreed.</div>';
    if (this._model.retired) return '<div style="margin-top:16px">' + record + "</div>";
    return '<div class="section-header" style="margin-top:18px">Interim approval</div>' +
      '<p class="muted" style="font-size:12px">The reviewer agrees ' + esc(label.toLowerCase()) +
      " and the review moves on. This does not close the stage &mdash; it stays open if you " +
      "need to come back to it.</p>" + record +
      '<div class="row" style="margin-top:8px"><input id="rv-note" placeholder="Note (optional)" ' +
      'style="flex:1"><button class="btn small primary" data-rapprove="' + esc(stageKey) + '">' +
      (given ? "Approve again&hellip;" : "Interim approval&hellip;") + "</button></div>";
  },

  _bindStageApproval(stageKey) {
    const btn = document.querySelector('[data-rapprove="' + stageKey + '"]');
    if (!btn) return;
    btn.onclick = () => {
      const label = REVIEW_STAGES.find((s) => s.key === stageKey).label;
      const note = val("rv-note");
      App.amend('Interim approval of "' + label + '" for ' + this._id + ".", "POST",
        "/api/models/" + this._id + "/review/approve-stage", { stage: stageKey, note: note },
        () => {
          // Approving moves the review on: land the reviewer on the next stage.
          const i = REVIEW_STAGES.findIndex((s) => s.key === stageKey);
          this._reviewStage = REVIEW_STAGES[Math.min(i + 1, REVIEW_STAGES.length - 1)].key;
          this.show(this._id, "review", { scroll: false });
          Inventory.loadList();
        });
    };
  },

  _bindReviewRail() {
    document.querySelectorAll("[data-rstage]").forEach((btn) => {
      btn.onclick = () => {
        this._reviewStage = btn.getAttribute("data-rstage");
        this._renderContent();
      };
    });
    this._renderReviewStage();
  },
});
