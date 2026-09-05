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
// The Review panel: a review run as a workflow, one stage at a time.
//
// Shared by every governed record type — a model, an ML Application and an AI System
// are reviewed identically, so they are reviewed by this. Each screen mixes the panel
// in and supplies the `_rv*` accessors in review_contract.js, which is the whole of
// what differs between them.
//
// Nothing here names a stage, a verdict or a trigger. Those come from the record
// type's own /fields payload (review_specs in src/web/_review_stages.py), because a
// console carrying its own copy is a console that offers an adopter's renamed stage
// under the old name — or a trigger the start-cycle endpoint then refuses.
//
// The stages are the work in the order it happens, ending in the reviewer's sign-off,
// which files the report the MRC receives. See docs/design/review-workflow.md.
//
// This file is the rail and the frame: which stage is open, what its badge says, what
// its body draws, and agreeing one. Two companions assign onto ReviewPanel and load
// after it — review_evidence.js (what the review recorded) and review_signoff.js (how
// it closes).
const REVIEW_DOC_CATEGORY = "Review";

const ReviewPanel = {
  // Which stage is open. Held on Detail (not in the URL) so switching model tabs
  // and coming back leaves the reviewer where they were.
  _reviewStage: "documents",

  _reviewTab(d) {
    const rail = this._rvStages().map((s) =>
      '<button class="dtab' + (s.key === this._reviewStage ? " active" : "") +
      '" data-rstage="' + s.key + '">' + s.n + ". " + esc(s.label) +
      this._stageBadge(s.key, d) + "</button>").join("");
    return '<p class="muted" style="font-size:var(--size-sm);margin:0 0 var(--space-4)">The review, in the order it ' +
      "runs. Each stage is agreed between the model owner and the reviewer before the review " +
      "moves on; the reviewer signs off at the end and the report goes to the MRC with the " +
      "risk rating.</p>" +
      '<div class="dtabs">' + rail + "</div>" +
      '<div id="' + this._rvPfx() + 'review-stage" style="margin-top:var(--space-6)"></div>';
  },

  // What the stage has to show for itself: a tick once agreed, else a count of
  // the work in it — or nothing, where a count would mean nothing.
  _stageBadge(key, d) {
    const n = (k) => (d[k] || []).length;
    // An agreed stage says so, in place of its count: once the reviewer has
    // approved it, how many rows it holds is no longer the interesting fact.
    if ((d.review_progress || []).some((r) => r.stage === key)) return " ✓";
    if (key === "documents") {
      return " (" + DocLinks.countIn(d.documents, [REVIEW_DOC_CATEGORY]) + ")";
    }
    if (key === "questions") {
      const vq = d[this._rvQuestionsKey()] || [];
      return " (" + vq.filter((q) => q.status === "Addressed").length + "/" + vq.length + ")";
    }
    if (key === "assumptions") return " (" + n("assumptions") + ")";
    if (key === "weaknesses") return " (" + n("model_weaknesses") + ")";
    if (key === "limitations") return " (" + n("limitations") + ")";
    return "";
  },

  _renderReviewStage() {
    const d = this._rvData();
    const box = this._rvEl("review-stage");
    const docOpts = {
      category: REVIEW_DOC_CATEGORY, docs: d.documents || [], base: this._rvApi(),
      id: this._rvId(), retired: this._rvRetired(),
      refresh: () => this._rvReload(),
    };
    if (this._reviewStage === "documents") {
      box.innerHTML = '<div class="section-header">The brief</div>' +
        '<p class="muted" style="font-size:var(--size-sm)">What this review is for, who is doing it, and ' +
        "by when. A reviewer handed a model and no brief writes the review they imagine is " +
        "wanted.</p>" +
        this._rvBriefFields().map((k) => this._rvRow(k, d)).join("") +
        this._newVersionChecklist(d) +
        '<div class="section-header" style="margin-top:var(--space-8)">Preliminary documents</div>' +
        '<p class="muted" style="font-size:var(--size-sm)">The pack the reviewer works from. These are ' +
        "the review's own working papers — the model's documentation lives on the Docs tab.</p>" +
        DocPanel.html(docOpts) + this._thread("documents", d) + this._stageApproval("documents", d);
      DocPanel.bind(docOpts);
      this._rvBindEdits();
      this._bindThread("documents");
      this._bindStageApproval("documents");
      return;
    }
    if (this._reviewStage === "assumptions") {
      box.innerHTML = '<p class="muted" style="font-size:var(--size-sm)">What the model takes to be true ' +
        "for its results to hold &mdash; and what is watched, or done, if one stops holding. " +
        "The sixth of the nine questions asks whether these are documented and justified, which " +
        "is why they are agreed before the questions rather than after.</p>" +
        this._rvColl("assumptions", d) + this._thread("assumptions", d) +
        this._stageApproval("assumptions", d);
      this._rvBindColls(["assumptions"]);
      this._bindThread("assumptions");
      this._bindStageApproval("assumptions");
      return;
    }
    if (this._reviewStage === "questions") {
      box.innerHTML = this._questionsTable(d) + this._thread("questions", d) + this._stageApproval("questions", d);
      this._rvBindOwnerAnswers();
      this._bindVerdictSaves();
      this._bindThread("questions");
      this._bindStageApproval("questions");
      return;
    }
    if (this._reviewStage === "weaknesses") {
      box.innerHTML = '<p class="muted" style="font-size:var(--size-sm)">What the model does badly, or ' +
        "not at all &mdash; proposed by the owner, agreed with the reviewer.</p>" +
        this._rvColl("model_weaknesses", d) + this._thread("weaknesses", d) + this._stageApproval("weaknesses", d);
      this._rvBindColls(["model_weaknesses"]);
      this._bindThread("weaknesses");
      this._bindStageApproval("weaknesses");
      return;
    }
    if (this._reviewStage === "limitations") {
      box.innerHTML = '<p class="muted" style="font-size:var(--size-sm)">Where the model may and may not ' +
        "be used, with the trigger that would surface a breach and the control that compensates.</p>" +
        this._rvColl("limitations", d) + this._thread("limitations", d) + this._stageApproval("limitations", d);
      this._rvBindColls(["limitations"]);
      this._bindThread("limitations");
      this._bindStageApproval("limitations");
      return;
    }
    if (this._reviewStage === "monitoring") {
      // The measured position is fetched and rendered above the approach: what the
      // statistics say comes before what somebody said they would do about it. Fetched
      // rather than computed here — the measures are one implementation with
      // hand-checked arithmetic, and a second in JavaScript would be a second answer.
      box.innerHTML = '<div class="section-header">Measured position</div>' +
        '<div id="' + this._rvPfx() + 'measured" class="empty">Loading&hellip;</div>' +
        '<div class="section-header" style="margin-top:var(--space-8)">Monitoring approach</div>' +
        '<p class="muted" style="font-size:var(--size-sm)">How this model will be watched once it is in ' +
        "use, in your own words &mdash; what would be looked at, how often, and what would " +
        "prompt a second look.</p>" + this._rvRow("monitoring_approach", d) +
        this._thread("monitoring", d) + this._stageApproval("monitoring", d);
      this._rvBindEdits();
      this._loadMeasured();
      this._bindThread("monitoring");
      this._bindStageApproval("monitoring");
      return;
    }
    if (this._reviewStage === "remediation") {
      box.innerHTML = '<div class="section-header">Remediation</div>' +
        '<p class="muted" style="font-size:var(--size-sm)">What the review found that has to be put ' +
        "right, and where each step has got to. The committee sees these before it signs the " +
        "review off.</p>" +
        this._rvColl("remediation_steps", d) +
        this._thread("remediation", d) + this._stageApproval("remediation", d);
      this._rvBindColls(["remediation_steps"]);
      this._bindThread("remediation");
      this._bindStageApproval("remediation");
      return;
    }
    box.innerHTML = this._signoffPanel(d);
    this._bindThread("signoff");
    this._bindSignoff();
    this._bindCycle();
  },

  // The reviewer's interim approval of a stage: the button, or the record of the
  // approval already given. Not a lock — the stage stays editable afterwards, and
  // approving again after a reopening simply adds another row.
  _stageApproval(stageKey, d) {
    const given = (d.review_progress || []).filter((r) => r.stage === stageKey).slice(-1)[0];
    const label = this._rvStages().find((s) => s.key === stageKey).label;
    const record = given
      ? '<div class="muted" style="font-size:var(--size-sm)">Interim approval by <b>' +
        esc(given.approved_by || "") + "</b> on " + esc((given.approved_at || "").slice(0, 10)) +
        (given.note ? ' &mdash; "' + esc(given.note) + '"' : "") + "</div>"
      : '<div class="muted" style="font-size:var(--size-sm)">Not yet agreed.</div>';
    if (this._rvRetired()) return '<div style="margin-top:var(--space-8)">' + record + "</div>";
    return '<div class="section-header" style="margin-top:var(--space-9)">Interim approval</div>' +
      '<p class="muted" style="font-size:var(--size-sm)">The reviewer agrees ' + esc(label.toLowerCase()) +
      " and the review moves on. This does not close the stage &mdash; it stays open if you " +
      "need to come back to it.</p>" + record +
      '<div class="row" style="margin-top:var(--space-4)"><input id="' + this._rvPfx() + 'rv-note" placeholder="Note (optional)" ' +
      'style="flex:1"><button class="btn small primary" data-rapprove="' + esc(stageKey) + '">' +
      (given ? "Approve again&hellip;" : "Interim approval&hellip;") + "</button></div>";
  },

  _bindStageApproval(stageKey) {
    const btn = this._rvScope().querySelector('[data-rapprove="' + stageKey + '"]');
    if (!btn) return;
    btn.onclick = () => {
      const label = this._rvStages().find((s) => s.key === stageKey).label;
      const note = this._rvVal("rv-note");
      App.amend('Interim approval of "' + label + '" for ' + this._rvId() + ".", "POST",
        this._rvApi() + this._rvId() + "/review/approve-stage", { stage: stageKey, note: note },
        () => {
          // Approving moves the review on: land the reviewer on the next stage.
          const i = this._rvStages().findIndex((s) => s.key === stageKey);
          this._reviewStage = this._rvStages()[Math.min(i + 1, this._rvStages().length - 1)].key;
          this._rvReload();
          this._rvAfterApprove();
        });
    };
  },

  _bindReviewRail() {
    this._rvAll("[data-rstage]").forEach((btn) => {
      btn.onclick = () => {
        this._reviewStage = btn.getAttribute("data-rstage");
        this._rvRerender();
      };
    });
    this._renderReviewStage();
  },
};
