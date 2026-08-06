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
      box.innerHTML = '<div class="section-header">Preliminary documents</div>' +
        '<p class="muted" style="font-size:12px">The pack the reviewer works from. These are ' +
        "the review's own working papers — the model's documentation lives on the Docs tab.</p>" +
        DocPanel.html(docOpts);
      DocPanel.bind(docOpts);
      return;
    }
    if (this._reviewStage === "questions") {
      box.innerHTML = DetailTabs.validation(d, this._model.retired);
      this._bindValidationSaves();
      return;
    }
    if (this._reviewStage === "weaknesses") {
      box.innerHTML = '<p class="muted" style="font-size:12px">What the model does badly, or ' +
        "not at all &mdash; proposed by the owner, agreed with the reviewer.</p>" +
        this._collSection("model_weaknesses", d);
      this._bindCollections(["model_weaknesses"]);
      return;
    }
    if (this._reviewStage === "limitations") {
      box.innerHTML = '<p class="muted" style="font-size:12px">Where the model may and may not ' +
        "be used, with the trigger that would surface a breach and the control that compensates.</p>" +
        this._collSection("limitations", d);
      this._bindCollections(["limitations"]);
      return;
    }
    if (this._reviewStage === "monitoring") {
      box.innerHTML = '<div class="section-header">Monitoring approach</div>' +
        '<p class="muted" style="font-size:12px">How this model will be watched once it is in ' +
        "use, in your own words &mdash; what would be looked at, how often, and what would " +
        "prompt a second look.</p>" + this._row("monitoring_approach", d);
      this._bindEdits();
      return;
    }
    // Sign-off is the next increment; say so plainly rather than showing an empty
    // panel that looks like a feature that failed to load.
    box.innerHTML = '<div class="section-header">Reviewer sign-off</div>' +
      '<div class="empty">Not built yet. The reviewer\'s final commentary, the sign-off gate ' +
      "and the Model Review Report the MRC receives land in a later increment.</div>";
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
