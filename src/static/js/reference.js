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

// Admin tab: sub-tabs for each reference section. There is a single company per
// instance (no list / no "add another") — the Company tab edits the institution
// name + logo, stored on the MRC settings. The simple lists (Division,
// Line of Business, Calc Agent, People) render through _renderList with working inline
// edit/remove; MRC is a drill-in.
const Reference = {
  _tab: "company",
  _TABS: [
    ["company", "Company"], ["division", "Division"], ["line_of_business", "Line of Business"],
    ["mrc", "MRC"], ["calculating_agent", "Calc Agent"], ["data_source", "Data Source"],
    ["people", "People"],
    // model_type (and codebase) are admin-managed and already exposed by
    // /api/reference; they were just missing from the tab bar, so the type field's
    // reference list could not be maintained from the UI. Vendor sits with it —
    // both classify the model itself (its type and who supplies it).
    ["model_type", "Model Type"], ["vendor", "Vendor"],
    // The off-the-shelf ML engines an ML Application is built on. Beside Model Type
    // and Vendor because it is the same kind of thing: what a record is classified
    // as, and who supplies it.
    ["estimator", "Estimator"],
    // The features an ML Application is fitted on. Its own tab, beside Estimator,
    // because it is the same kind of thing: a register of entries with properties,
    // not a vocabulary of words.
    ["feature", "Feature"],
    // The per-division risk policy: dimensions, ratings and the generated grids.
    ["risk", "Risk"],
    // How a division carves its estate up by function -- what a record is FOR, as
    // against Model Type above, which is what it IS. MRC-ratified like the two
    // policies, so it sits with them rather than among the flat lists.
    ["functional_groups", "Functional Groups"],
    // The stages a record moves through: the institution's catalogue, and each
    // division's choice from it. MRC-ratified at both layers, so it sits with the
    // policies rather than among the flat lists — which is where it used to be, as an
    // admin list that edited a label and nothing else.
    ["lifecycle_stages", "Lifecycle Stages"],
    // The questionnaire every review works through. Its own tab rather than a row
    // among the reference lists: it is the institution's own standard, and the
    // review workflow is built around it.
    ["review_questions", "Model Review"],
    // The running order every meeting is seeded with. Beside the questionnaire
    // because they are the same kind of thing: a standard the institution sets,
    // copied onto each record it applies to.
    // The three questionnaires an APPLICATION of a model is asked, in the order a
    // record is asked them: the five shared questions first, then whichever
    // type-specific set applies. Grouped here rather than scattered, because "which
    // list is this question on" is the first thing an administrator editing them
    // needs to know.
    //
    // Common sits apart from Model Review above it: a model answers the institution's
    // own review questionnaire, while an ML Application and an AI System both answer
    // these five and then their own.
    ["common_questions", "Common (AI/ML)"],
    // The ML questionnaire, deliberately separate from the AI one: the two processes
    // ask different things, and the sets move apart. What they SHARE is above.
    ["ml_application_questions", "ML Review"],
    // The AI questionnaire, which had no tab at all — the list was reachable only
    // through the shipped fallback, so an institution could not reword the questions
    // its own AI Systems are asked.
    ["ai_system_questions", "AI Review"],
    // The enumerations the Training tab is typed against. One tab, not eleven —
    // the same reasoning as the status vocabularies below: shown together rather
    // than as eleven tabs nobody would find.
    ["ml_training", "ML Training"],
    // What a division's ML review actually asks for. Beside the two lists it governs
    // -- the questions and the training vocabularies -- because it is the tab that
    // decides how much of them anybody is shown.
    ["ml_review_policy", "ML Review Policy"],
    ["standing_agenda", "Agenda"],
    // Every status vocabulary on one tab: shown-as is the institution's to change,
    // stored-as is what the records already hold and never moves.
    ["vocabulary", "Vocabulary"],
    // Institution-specific wording that is not a reference list — what the
    // generated PDFs say (classification, author, legal notice).
    ["misc", "Misc"],
  ],

  async render() {
    const el = document.getElementById("tab-reference");
    const bar = this._TABS.map(([k, label]) =>
      '<button class="dtab' + (k === this._tab ? " active" : "") + '" data-atab="' + k + '">' +
      label + "</button>").join("");
    el.innerHTML = '<div class="card"><div class="dtabs">' + bar + '</div><div id="admin-body"></div></div>';
    el.querySelectorAll("[data-atab]").forEach((btn) => {
      btn.onclick = () => { this._tab = btn.getAttribute("data-atab"); this.render(); };
    });
    await this._renderBody(document.getElementById("admin-body"));
  },

  async _renderBody(container) {
    // The single company (institution name + logo) lives on the MRC settings,
    // not the reference lists — edited as one record, never added to.
    if (this._tab === "company") {
      await this._renderInstitution(container);
      return;
    }
    // The risk policy is per-division structured config, not a flat reference list.
    if (this._tab === "risk") {
      await RiskEditor.render(container);
      return;
    }
    // Likewise the functional groups: a per-division, MRC-ratified list rather than
    // an admin-managed one, so it does not come from /api/reference at all.
    if (this._tab === "functional_groups") {
      await FunctionalGroupsEditor.render(container);
      return;
    }
    // Likewise the lifecycle stages: two ratified layers rather than an admin list.
    if (this._tab === "lifecycle_stages") {
      await LifecycleStagesEditor.render(container);
      return;
    }
    // Likewise the ML review policy: per-division, MRC-ratified, and about the other
    // lists rather than being one.
    if (this._tab === "ml_review_policy") {
      await MlReviewPolicyEditor.render(container);
      return;
    }
    // Misc is the singleton settings that are wording, not lists.
    if (this._tab === "misc") {
      await AdminMisc.render(container);
      return;
    }
    const res = await App.get("/api/reference");
    if (this._tab === "vocabulary") { this._renderVocabularies(container, res); return; }
    if (this._tab === "ml_training") {
      this._renderVocabularies(container, res, this._ML_VOCABULARIES,
        "The enumerations an ML Application's Training tab is typed against \u2014 the " +
        "learning task, how the data was split, how it was scaled, what it was scored " +
        "on. Typed rather than free text so the estate can be asked which models were " +
        "fitted a particular way; admin-managed so you can add what you actually fit. ");
      return;
    }
    const spec = res.collections.find((c) => c.key === this._tab);
    // MRC committees are entities with a drill-in detail (fields + per-committee
    // Terms of Reference); the scope field reacts to the committee's level.
    if (this._tab === "mrc") {
      Committees.render(container, spec, res.data.mrc || [], res.data);
      return;
    }
    if (!spec) { container.innerHTML = '<div class="empty">This section has moved.</div>'; return; }
    if (this._tab === "standing_agenda") {
      this._renderList(container, spec, res.data[this._tab] || [],
        "The running order every meeting is seeded with. A meeting is copied the list " +
        "as it stands when it is scheduled and keeps its own agenda, so editing here " +
        "changes the <em>next</em> meeting — it never rewrites one already held. " +
        "<b>Role</b> is what the console draws for the item (a rollcall, the previous " +
        "minutes, the sign-off review); leave it blank for business the committee " +
        "always takes, which renders as an ordinary agenda item.");
      return;
    }
    if (this._tab === "feature") {
      this._renderList(container, spec, res.data[this._tab] || [],
        "The features your ML Applications are fitted on. Linked from a train rather " +
        "than typed into it, so a feature that turns out to be wrong \u2014 or to have " +
        "leaked \u2014 can be traced to every fit that used it at once. Nothing is " +
        "seeded here: a starter list of ours would be somebody else's model.");
      return;
    }
    if (this._tab === "estimator") {
      this._renderList(container, spec, res.data[this._tab] || [],
        "The off-the-shelf ML engines an ML Application can be built on \u2014 one row per " +
        "source and estimator, carrying the versions available for it. An ML Application " +
        "picks the estimator and then one of its versions, so the menu is set here and the " +
        "choice is made on the record. <b>Available versions</b> is comma-separated and " +
        "ships empty on purpose: which releases you actually run is yours to state, not " +
        "ours to guess.");
      return;
    }
    if (this._tab === "ml_application_questions") {
      this._renderList(container, spec, res.data[this._tab] || [],
        "The questions every ML Application review works through. Separate from the model " +
        "questionnaire because an ML Application is asked different things \u2014 what it was " +
        "trained on, why this estimator, how it is known to still work. A record is copied " +
        "the list as it stands when it is registered and keeps its own answers, so editing " +
        "here changes what the <em>next</em> review asks.");
      return;
    }
    if (this._tab === "review_questions") {
      this._renderList(container, spec, res.data[this._tab] || [],
        "The questions every review works through, asked of each model in this order. A " +
        "model is copied the list as it stands when it is registered and keeps its own " +
        "answers, so editing here changes what the <em>next</em> review asks — it never " +
        "rewrites an answer already given.");
      return;
    }
    this._renderList(container, spec, res.data[this._tab] || []);
  },
};
