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

// Model detail (the Detail package). This core module owns the header card, the
// tab bar and tab routing, and the collection-tab wiring. The Overview tab and
// per-field editing augment Detail from detail_overview.js, loaded after.
// Description is promoted to a full-width summary band above the two columns.
// Tier + its rating rationale sit at the foot of Model Details, below Complexity.
// repo_location / codebase (Organisation), type / short_name / tier_rationale
// (Classification), methodology_rationale (Methodology) and model_owner_role /
// validation_date (Governance) are governed, audit-scored fields; each renders from
// the config specs via _row. They had been dropped from these lists, which left them
// uneditable while the audit still expected them.
const OVERVIEW_LEFT = ["division", "line_of_business", "repo_location", "codebase", "type", "vendor",
  "short_name", "methodology", "methodology_rationale", "source_module"];
// The owner's risk assessment (what places the model on the heatmap) lives on the Risk
// tab, next to the grid it drives — not the Overview. Only the headline rag_rating (owner
// vs table) stays on Overview, under Governance.
// The fields themselves are the risk-assessment table's business (risk_assessment.js):
// one row per dimension, in the Admin editor's Dimension / Rating / Rationale columns.
// Governance column. Note: recertification / review_frequency / last_review_date remain
// intentionally off the overview (the MRC sets sign-off + next review at sign-off); that
// they are still audit-scored is a separate, open decision, not this regression.
// Reviewer and validation date moved onto the Review tab, where the review is
// actually run; review_status stays because it is the one-line answer to "where
// is this model up to", and it links through to the workflow that sets it.
const OVERVIEW_RIGHT_TOP = ["rag_rating", "owner", "model_owner_role", "lifecycle_stage",
  "review_status"];
// The testing evidence is documentation, so it lives under Docs (between Analysis
// and Monitoring) rather than on a tab of its own. The categories behind that panel
// come from config with the rest — see doc_tab_groups in the field specs.
// Collection tabs that carry an in-context supporting-documents panel.
const COLLECTION_DOC_CATEGORY = {
  remediation_steps: "Remediation Evidence",
};
const HEADER_DATES = ["next_review_date"];

const Detail = {
  _id: null, _model: null, _specs: null, _risk: null, _audit: [], _mrc: null,
  _decisions: [], _tab: "overview",

  // ``opts.scroll === false`` refreshes in place without jumping to the top — used
  // by the register tabs so an auto-saved edit does not scroll the page every time.
  async show(modelId, tab, opts) {
    this._id = modelId;
    this._specs = await Inventory.specs();
    // Fetch the independent reads in parallel so a re-render settles quickly.
    const [model, risk, mrc, audit, decisions, presentations] = await Promise.all([
      App.get("/api/models/" + modelId),
      App.get("/api/models/" + modelId + "/risk-rating"),
      App.get("/api/models/" + modelId + "/mrc"),
      App.get("/api/audit"),
      App.get("/api/models/" + modelId + "/decisions"),
      App.get("/api/models/" + modelId + "/analysis-presentations"),
    ]);
    this._model = model;
    this._risk = risk;
    this._mrc = mrc;
    this._audit = audit.filter((e) => e.aggregate_id === modelId);
    this._decisions = decisions;
    this._analysisPresentations = presentations;
    if (tab) this._tab = tab;
    this._render();
    if (!opts || opts.scroll !== false) {
      document.getElementById("m-detail").scrollIntoView({ block: "start" });
    }
  },

  specByKey(key) { return Inventory.specByKey(key); },
  collSpec(key) { return this._specs.collections.find((c) => c.key === key); },

  _render() {
    const d = this._model.data || {};
    document.getElementById("m-detail").innerHTML =
      '<div class="card">' + this._header(d) + this._tabbar(d) + '<div id="dt-content"></div></div>';
    document.querySelectorAll("[data-dtab]").forEach((b) => {
      b.onclick = () => { this._tab = b.getAttribute("data-dtab"); this._render(); };
    });
    this._renderContent();
    if (this._tab === "danger") this._bindRetire();
  },

  _header(d) {
    const sub = esc(this._id) + (d.version ? " · v" + esc(d.version) : "") + (d.category ? " · " + esc(d.category) : "");
    const dates = HEADER_DATES.map((k) => {
      // MRC sign-off shows the granting meeting id (not the date) once approved.
      const value = (k === "mrc_signoff_date" && d.mrc_signoff_meeting)
        ? esc(d.mrc_signoff_meeting) : fieldDisplay(d[k]);
      return '<span class="datechip"><span class="muted">' + esc(this.specByKey(k).label) +
        ":</span> <b>" + value + "</b></span>";
    }).join("");
    return '<div class="detail-header"><div>' +
      '<div class="name">' + esc(d.name || this._id) + "</div>" +
      '<div class="sub">' + sub + "</div>" +
      // The RAG rating is the governed
      // one, and a second, differently-derived verdict in the header invited the
      // question "where does that come from?" without answering it.
      '<div style="margin-top:8px">' + tierBadge(d.tier, d.division) + ' <span class="muted">' +
      esc(tierFullLabel(d.tier, d.division)) + "</span></div>" +
      '<div class="dh-dates">' + dates + "</div></div>" +
      '<div class="right"><div class="olabel">OWNER</div>' +
      '<div class="oname">' + fieldDisplay(d.owner) + "</div>" +
      '<div style="margin-top:6px">' + ragBadge(d.rag_rating, d.division) + "</div></div></div>";
  },

  _tabbar(d) {
    const n = (k) => (d[k] || []).length;
    const vq = d.validation_questions || [];
    const cov = vq.filter((q) => q.status === "Addressed").length + "/" + vq.length;
    const tabs = [
      ["overview", "Overview", null],
      ["version_history", "Versions", null],
      // Dependencies and Connections were two halves of one subject — a table of
      // declared feeds, and the picture those declarations draw. One tab now: the
      // graph you wire, with both registers beneath it.
      ["connections", "Connections", n("dependencies") + n("data_sources")],
      ["raci_roles", "RACI", n("raci_roles")],
      ["review", "Review", cov],
      ["risk", "Risk Rating", null],
      ["decisions", "MRC linkage",
        (d.signoff_history || []).length + this._decisions.length],
      ["docs", "Docs", DocLinks.countIn(d.documents, (this._specs.doc_tab_categories || [])
        .concat(this._specs.testing_doc_categories || []))],
      // Audit is the final tab — the complete, read-only record of every change,
      // entry and upload, so it always sits last after Danger.
      ["danger", "Danger", null], ["audit", "Audit", this._audit.length],
    ];
    return '<div class="dtabs">' + tabs.map((t) => {
      const danger = t[0] === "danger" ? " dtab-danger" : "";
      return '<button class="dtab' + (t[0] === this._tab ? " active" : "") + danger +
        '" data-dtab="' + t[0] + '">' +
        esc(t[1]) + (t[2] !== null ? " (" + t[2] + ")" : "") + "</button>";
    }).join("") + "</div>";
  },

  _renderContent() {
    const d = this._model.data || {};
    const box = document.getElementById("dt-content");
    if (this._tab === "overview") { box.innerHTML = this._overview(d); this._bindEdits(); return; }
    if (this._tab === "connections") {
      box.innerHTML =
        '<p class="muted" style="font-size:12px;margin-bottom:10px">This model\'s neighbourhood: ' +
        "what feeds it, what it feeds, and the models it shares a data source with. Drag a model or " +
        "a data source from the tray onto the canvas to connect it, or drag from a node’s handle " +
        "onto another node. Click an arrow to state what crosses it; click a model to re-centre.</p>" +
        '<div id="nbhd-host"></div>' +
        '<div id="nbhd-handoff"></div>' +
        '<p class="muted" style="font-size:12px;margin-top:16px">The declarations behind the picture. ' +
        "Every feed drawn above is one of these rows, on this model or on the model at the other end.</p>" +
        this._collSection("dependencies", d) +
        '<p class="muted" style="font-size:12px;margin-top:16px">The feeds this model pulls its inputs ' +
        "from. Any model that draws on the same source is linked to it above.</p>" +
        this._collSection("data_sources", d);
      Neighbourhood.render(this._id, "nbhd-host");
      this._bindCollections(["dependencies", "data_sources"]);
      return;
    }
    if (this._tab === "risk") {
      box.innerHTML =
        '<div class="section-header">Risk assessment</div>' +
        '<p class="muted" style="font-size:12px;margin:0 0 8px">The owner sets these; they place ' +
        "the model on the heatmap below, which becomes its rating once the MRC signs it off.</p>" +
        policyNotice(d.division) +
        this._riskTable(d) +
        DetailTabs.risk(this._risk, false, d.division);  // events are product-only
      this._bindEdits();          // the risk-assessment fields are editable here now
      this._bindSignoffRequest();
      return;
    }
    if (this._tab === "audit") { box.innerHTML = DetailTabs.audit(this._audit); return; }
    if (this._tab === "danger") { box.innerHTML = this._dangerContent(); return; }
    if (this._tab === "decisions") { box.innerHTML = this._mrcLinkage(d); return; }
    if (this._tab === "docs") {
      // Docs is the model's own documentation and supporting analysis. Testing
      // evidence lives on the Testing tab and Remediation Evidence on the
      // Remediation tab, each beside what it evidences, so nothing is listed twice.
      // The Model Risk Document is generated from the inventory on request, so it
      // is offered as an action rather than filed as one more uploaded row that
      // could go stale against the record it describes.
      box.innerHTML =
        '<div class="row" style="justify-content:space-between;align-items:center;margin-bottom:10px">' +
        '<span class="muted" style="font-size:12px">The full write-up for this model, ' +
        "generated from the current record — on its own, or zipped with its PDF evidence " +
        "to send on.</span>" +
        '<span><a class="btn small" href="/api/models/' + esc(this._id) +
        '/pack.zip">Client pack (ZIP)</a> ' +
        '<a class="btn small primary" target="_blank" rel="noopener" id="mrd-issue" href="/api/models/' +
        esc(this._id) + '/risk-document.pdf">Model Risk Document (PDF)</a></span></div>' +
        '<div id="docs-host"></div>';
      ModelDocs.render(this._id, d.documents || [], this._specs.doc_tab_categories || [],
        this._model.retired, "/api/models/", () => this.show(this._id, "docs"), "docs-host",
        this._specs.doc_tab_groups || {});
      // Issuing files a copy under History. Fetch the PDF ourselves so we know
      // when the server has finished generating and filing it, then refresh so the
      // new copy appears in History at once — a fixed timer used to race a slow
      // LaTeX compile and leave History lagging. The tab is opened up front, inside
      // the click, so the browser does not treat it as a blocked pop-up.
      const issue = document.getElementById("mrd-issue");
      if (issue) {
        issue.addEventListener("click", async (e) => {
          e.preventDefault();
          const win = window.open("", "_blank");
          try {
            const res = await fetch(issue.getAttribute("href"), { headers: App.headers() });
            if (!res.ok) throw new Error("The document could not be generated.");
            if (win) win.location = URL.createObjectURL(await res.blob());
            await this.show(this._id, "docs", { scroll: false });
          } catch (err) {
            if (win) win.close();
            App.toast(err.message || "Document generation failed.", "error");
          }
        });
      }
      return;
    }
    // The review, run as a workflow: one rail, one stage at a time. The stages
    // own the nine questions, the weaknesses and the limitations of use, which is
    // why none of them is a tab of its own any more.
    if (this._tab === "review") {
      box.innerHTML = this._reviewTab(d);
      this._bindReviewRail(); return;
    }
    // Versions & Changes overlap — one tab: the version timeline plus the
    // change-history register.
    if (this._tab === "version_history") {
      box.innerHTML = DetailTabs.versions(d, this.collSpec("version_history"), this._model.retired) +
        this._collSection("change_history", d);
      this._bindCollections(["version_history", "change_history"]); return;
    }
    const spec = this.collSpec(this._tab);
    let html = Collections.render(d, { collections: [spec] }, this._model.retired);
    const docCat = COLLECTION_DOC_CATEGORY[this._tab];
    const docOpts = { category: docCat, docs: d.documents || [], base: "/api/models/", id: this._id,
      retired: this._model.retired,
      refresh: () => this.show(this._id, this._tab, { scroll: false }) };
    if (docCat) html += '<div class="section-header" style="margin-top:14px">Supporting documents</div>' +
      DocPanel.html(docOpts);
    box.innerHTML = html;
    this._bindCollection(this._tab);
    if (docCat) DocPanel.bind(docOpts);
  },

  _collSection(key, d) {
    return Collections.render(d, { collections: [this.collSpec(key)] }, this._model.retired);
  },

  // The model's MRC record: granted rating sign-offs (which land here once a
  // committee approves) plus decisions linked from the meeting log. Actions are
  // now first-class on the model (the Actions tab), not a read-only projection.
  _mrcLinkage(d) {
    const signoffs = d.signoff_history || [];
    const soSection = signoffs.length
      ? DetailTabs.signoffHistory(signoffs, d.division)
      : '<div class="section-header">Sign-off history</div>' +
        '<div class="empty">No MRC sign-offs granted yet.</div>';
    // Every meeting where this model's analysis was presented (it was in scope),
    // with the committee's outcome and a link to the paper if one was tabled.
    const pres = this._analysisPresentations || [];
    const presSection = pres.length
      ? pres.map((a) => {
          const paper = a.analysis_filename
            ? ' &middot; <a href="/api/meetings/' + esc(a.meeting_id) + "/models/" + esc(this._id) +
              '/analysis" target="_blank" rel="noopener">analysis paper</a>'
            : "";
          return '<div class="prow"><div style="font-size:12px"><b>' + esc(a.meeting_id) + "</b> " +
            '<span class="muted">' + esc(a.meeting_date || "") + "</span> &mdash; " +
            esc(a.analysis_status || "Pending") +
            (a.presenter ? ' <span class="muted">presented by ' + esc(a.presenter) + "</span>" : "") +
            paper + "</div></div>";
        }).join("")
      : '<div class="empty">No analysis presented to an MRC yet.</div>';
    return '<p class="muted">The model&rsquo;s MRC record — granted rating sign-offs, the meetings ' +
      "its analysis was presented at, plus decisions linked from meetings (read-only, sourced from " +
      "the meeting log).</p>" +
      soSection +
      '<div class="section-header">Analysis presented to the MRC</div>' + presSection +
      '<div class="section-header">Decisions</div>' +
      DetailTabs.linkedItems("Decisions", this._decisions, ["description", "date"]);
  },

  _bindCollections(keys) {
    // Refresh in place (no scroll) so a register edit does not jump the page.
    Collections.bind("/api/models/" + this._id + "/collections/",
      { collections: keys.map((k) => this.collSpec(k)) },
      this._model.retired, () => this.show(this._id, this._tab, { scroll: false }),
      this._model.data);
  },

  _bindCollection(key) { this._bindCollections([key]); },

  _bindValidationSaves() {
    if (this._model.retired) return;
    const self = this;
    // Auto-save: changing a status, or leaving a rationale field (its change event
    // fires on blur / Enter), posts the row immediately. Updating a validation
    // question is a non-critical edit, so it applies without a confirmation dialog.
    // The fresh record the endpoint returns is re-rendered in place, so the
    // coverage tiles and the tab count reflect the change at once — and, unlike a
    // full reload, the view does not scroll back to the top on every keystroke.
    const save = async function (itemId) {
      try {
        const updated = await App.send(
          "POST", "/api/models/" + self._id + "/collections/validation_questions/" + itemId,
          { fields: { status: val("vq-" + itemId + "-status"),
                      rationale: val("vq-" + itemId + "-rationale") } });
        self._model = updated;
        if (typeof MrcNav !== "undefined") MrcNav.invalidate();
        if (typeof Nav !== "undefined") Nav.markAllDirty();
        App.toast("Change recorded in the audit trail", "ok");
        self._render();
      } catch (e) {
        App.toast(e.message, "error");
      }
    };
    document.querySelectorAll("select[data-vq-item], input[data-vq-item], textarea[data-vq-item]")
      .forEach(function (el) {
        el.onchange = () => save(el.getAttribute("data-vq-item"));
      });
  },
};
