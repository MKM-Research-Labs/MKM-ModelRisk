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
// The model detail: what each tab draws.
//
// One dispatcher, one body per tab. Split from detail_core.js the same way the ML
// Application screen was, and for the same reason: what a model IS and what a
// particular tab of it puts on screen are changed for different reasons.
//
// Assigns onto Detail; loads after detail_core.js.

Object.assign(Detail, {

  _renderContent() {
    const d = this._model.data || {};
    const box = document.getElementById("dt-content");
    if (this._tab === "overview") {
      // Numerical methods sit beside the methodology they implement. Reference only:
      // nothing scores, classifies or reviews them (config/governance/_numerical_methods).
      box.innerHTML = this._overview(d) +
        '<p class="muted" style="font-size:var(--size-sm);margin-top:var(--space-8)">The off-the-shelf ' +
        "numerical methods this model is built with, for reference. They are not governed in their " +
        "own right; how this model sets them (bump size, path count, tolerance) belongs in its assumptions.</p>" +
        this._collSection("numerical_methods", d);
      this._bindEdits();
      this._bindCollections(["numerical_methods"]);
      return;
    }
    if (this._tab === "connections") {
      box.innerHTML =
        '<p class="muted" style="font-size:var(--size-sm);margin-bottom:var(--space-5)">This model\'s neighbourhood: ' +
        "what feeds it, what it feeds, and the models it shares a data source with. Drag a model or " +
        "a data source from the tray onto the canvas to connect it, or drag from a node’s handle " +
        "onto another node. Click an arrow to state what crosses it; click a model to re-centre.</p>" +
        '<div id="nbhd-host"></div>' +
        '<div id="nbhd-handoff"></div>' +
        '<p class="muted" style="font-size:var(--size-sm);margin-top:var(--space-8)">The declarations behind the picture. ' +
        "Every feed drawn above is one of these rows, on this model or on the model at the other end.</p>" +
        this._collSection("dependencies", d) +
        '<p class="muted" style="font-size:var(--size-sm);margin-top:var(--space-8)">The feeds this model pulls its inputs ' +
        "from. Any model that draws on the same source is linked to it above.</p>" +
        this._collSection("data_sources", d);
      Neighbourhood.render(this._id, "nbhd-host");
      this._bindCollections(["dependencies", "data_sources"]);
      return;
    }
    if (this._tab === "risk") {
      box.innerHTML =
        '<div class="section-header">Risk assessment</div>' +
        '<p class="muted" style="font-size:var(--size-sm);margin:0 0 var(--space-4)">The owner sets these; they place ' +
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
        '<div class="row" style="justify-content:space-between;align-items:center;margin-bottom:var(--space-5)">' +
        '<span class="muted" style="font-size:var(--size-sm)">The full write-up for this model, ' +
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
    if (docCat) html += '<div class="section-header" style="margin-top:var(--space-7)">Supporting documents</div>' +
      DocPanel.html(docOpts);
    box.innerHTML = html;
    this._bindCollection(this._tab);
    if (docCat) DocPanel.bind(docOpts);
  },
});
