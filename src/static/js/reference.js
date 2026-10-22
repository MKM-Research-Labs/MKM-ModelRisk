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

// Admin tab: its sub-tabs, grouped by the KIND of thing each one holds, because the
// kind decides how it behaves -- who may change it, whether a change reaches records
// already made, and whether it is words or entries with properties. The tab bar was
// one row of two dozen tabs in the order they were added, and several lists of the same
// kind had ended up on separate tabs (and three on none at all).
//
// There is a single company per instance (no list / no "add another") — the Company
// tab edits the institution name + logo, stored on the MRC settings. The flat lists
// render through _renderList with working inline edit/remove; MRC is a drill-in.
const Reference = {
  _tab: "company",
  _SECTIONS: [
    // Who the institution is and how it is organised: the org tree, its committees and
    // its people. People carry an org unit, which is what seats them on a committee.
    ["Organisation", [
      ["company", "Company"], ["division", "Division"], ["line_of_business", "Line of Business"],
      ["mrc", "MRC"], ["people", "People"],
    ]],
    // Entries a record links to, each with properties of its own: what a model IS
    // (type, vendor, codebase), the platform and feeds it runs on, and the ML and AI
    // components an application is built from. Codebase, Foundation Model and Market
    // were admin-managed and served by /api/reference but had no tab, so they could
    // not be maintained from the console at all.
    ["Registers", [
      ["model_type", "Model Type"], ["vendor", "Vendor"], ["codebase", "Codebase"],
      ["calculating_agent", "Calc Agent"], ["data_source", "Data Source"],
      ["estimator", "Estimator"], ["feature", "Feature"],
      ["foundation_model", "Foundation Model"], ["market", "Market"],
    ]],
    // Words in a fixed set and nothing else -- the status words, the RACI roles and the
    // ML training enumerations -- on ONE tab, because they are one kind of thing: shown-as
    // is the institution's to change, stored-as is what records hold and never moves.
    ["Static data", [["vocabulary", "Vocabulary"]]],
    // Per-division and MRC-ratified, so a change is proposed and approved rather than
    // simply saved: the risk policy, the functional groups, the lifecycle stages and
    // what an ML review asks for.
    ["Policies", [
      ["risk", "Risk"], ["functional_groups", "Functional Groups"],
      ["lifecycle_stages", "Lifecycle Stages"], ["ml_review_policy", "ML Review Policy"],
    ]],
    // Standards copied onto each record when it is made, so editing one changes the
    // NEXT record and never rewrites one already held: the review questionnaires (the
    // model's own; then the five every ML Application and AI System answers, and each
    // one's own set) and the running order every meeting is seeded with.
    ["Templates", [
      ["review_questions", "Model Review"], ["common_questions", "Common (AI/ML)"],
      ["ml_application_questions", "ML Review"], ["ai_system_questions", "AI Review"],
      ["standing_agenda", "Agenda"],
    ]],
    // Institution-specific wording that is not a list — what the generated PDFs say
    // (classification, author, legal notice).
    ["Settings", [["misc", "Misc"]]],
  ],

  async render() {
    const el = document.getElementById("tab-reference");
    // Top down, as every other two-level screen does it (a model's review stages, the
    // org navigator): the sections across the top, then the open section's lists in a
    // row of their own beneath. A section holding one list is that list's tab, with no
    // second row to repeat it. ``data-holds`` names what a section holds, so a caller
    // that knows only the list (the e2e helpers) can find its way in.
    const open = this._SECTIONS.find(([, tabs]) => tabs.some(([k]) => k === this._tab)) ||
      this._SECTIONS[0];
    const tab = (active, attr, label) =>
      '<button class="dtab' + (active ? " active" : "") + '" ' + attr + ">" + label + "</button>";
    const top = this._SECTIONS.map(([title, tabs]) => tabs.length === 1
      ? tab(tabs[0][0] === this._tab, 'data-atab="' + tabs[0][0] + '"', title)
      : tab(open[0] === title, 'data-asec="' + title + '" data-holds="' +
            tabs.map(([k]) => k).join(" ") + '"', title)).join("");
    const second = open[1].length > 1
      ? '<div class="dtabs">' + open[1].map(([k, label]) =>
          tab(k === this._tab, 'data-atab="' + k + '"', label)).join("") + "</div>"
      : "";
    el.innerHTML = '<div class="card"><div class="dtabs">' + top + "</div>" + second +
      '<div id="admin-body"></div></div>';
    el.querySelectorAll("[data-atab]").forEach((btn) => {
      btn.onclick = () => { this._tab = btn.getAttribute("data-atab"); this.render(); };
    });
    // Opening a section opens its first list.
    el.querySelectorAll("[data-asec]").forEach((btn) => {
      btn.onclick = () => {
        this._tab = btn.getAttribute("data-holds").split(" ")[0];
        this.render();
      };
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
    // A list whose config says what it governs says so here too; the registers that
    // gained a tab without a hint of their own say it here.
    this._renderList(container, spec, res.data[this._tab] || [],
                     spec.hint || this._INTROS[this._tab] || "");
  },

  _INTROS: {
    codebase: "Where each model's code lives. A codebase carries its repository, so the " +
      "two travel together and cannot disagree.",
    foundation_model: "The foundation models your AI Systems are built on, with the " +
      "versions available for each. Ships empty: which models you actually run is yours " +
      "to state.",
    market: "Where an AI System is placed on the market or used \u2014 what decides which " +
      "regulatory regimes apply to it. Until you add one, the shipped markets are offered.",
  },
};
