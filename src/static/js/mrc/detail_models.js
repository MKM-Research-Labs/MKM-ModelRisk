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

// MeetingDetail — the Signoff tab: Approvals (risk-rating sign-offs) plus an
// Analysis section with Models and Products sub-tabs. The scope table + per-item
// analysis review are written once and driven by a per-kind config, so models
// and products behave identically.
Object.assign(MeetingDetail, {
  // Org-scope filter shared by both kinds: the most specific level set on the
  // meeting (derived from its bound MRC) — line of business > division > all.
  _scopeFilter() {
    const md = this._meeting.data || {};
    if (md.line_of_business) return { key: "line_of_business", value: md.line_of_business };
    if (md.division) return { key: "division", value: md.division };
    return null;
  },

  // Everything that differs between a model scope pane and a product one.
  // Read from the served scope table (GET /api/meetings/fields), never restated
  // here. The console used to carry its own copy for models and products, which is
  // how ML Applications and AI Systems could be governed by a committee that had no
  // way to put them in front of itself: the record types existed, and the screen did
  // not know about them.
  _scopeKinds() { return (this._specs || {}).scope || []; },

  _scopeCfg(kind) {
    const served = this._scopeKinds().find((s) => s.kind === kind)
      || this._scopeKinds()[0] || {};
    // Where this screen keeps the two lists each kind needs: everything of that type,
    // and the rows already in scope at this meeting.
    const store = {
      model: { inventory: "_inventory", inScope: "_models", showAll: "_showAll" },
      product: { inventory: "_products", inScope: "_meetingProducts",
                 showAll: "_showAllProducts" },
      ml_application: { inventory: "_mlApplications", inScope: "_meetingMlApplications",
                        showAll: "_showAllMlApplications" },
      ai_system: { inventory: "_aiSystems", inScope: "_meetingAiSystems",
                   showAll: "_showAllAiSystems" },
    }[served.kind] || {};
    return {
      kind: served.kind, idKey: served.id_key, collection: served.collection,
      base: served.url, label: served.noun, plural: served.plural,
      nameKey: served.name_field,
      inventory: this[store.inventory] || [], inScope: this[store.inScope] || [],
      showAllKey: store.showAll, setKey: served.id_key + "s",
    };
  },

  _candidates(cfg) {
    const filter = this._scopeFilter();
    const inv = cfg.inventory.slice();
    if (this[cfg.showAllKey] || !filter) return inv;
    return inv.filter((m) => (m.data || {})[filter.key] === filter.value);
  },

  _modelsTab() {
    if (this._analysisKind === "handoff") {
      return this._approvalsSection() +
        '<div class="section-header" style="margin-top:var(--space-9)">Analysis</div>' +
        this._analysisSubtabs("handoff") + this._handoffAnalysis();
    }
    const cfg = this._scopeCfg(this._analysisKind || "model");
    // First pass has no document list yet; fetch it, then re-render once. The
    // picker shows a placeholder in the meantime rather than an empty dropdown.
    if (this._reviewableDocs === undefined || this._reviewableDocsKind !== cfg.kind) {
      this._reviewableDocsKind = cfg.kind;
      this._reviewableDocs = {};
      this._loadReviewableDocs(cfg).then(() => this._render());
    }
    return this._approvalsSection() +
      '<div class="section-header" style="margin-top:var(--space-9)">Analysis</div>' +
      this._analysisSubtabs(cfg.kind) +
      '<p class="muted" style="font-size:var(--size-sm)">Choose the ' + cfg.plural +
      " in scope, then record the confirmation to proceed and any follow-on actions.</p>" +
      this._scopeTable(cfg) + this._analysisReview(cfg);
  },

  // The reviewable documents held by each in-scope model, fetched once per render
  // so the picker can offer them without a request per row.
  async _loadReviewableDocs(cfg) {
    const ids = cfg.inScope.map((m) => m[cfg.idKey]);
    if (!ids.length) { this._reviewableDocs = {}; return; }
    const out = {};
    await Promise.all(ids.map(async (id) => {
      try { out[id] = await App.get("/api/" + cfg.base + "/" + id + "/reviewable-documents"); }
      catch (e) { out[id] = []; }
    }));
    this._reviewableDocs = out;
  },
});
