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

// AI Systems: the list view (master) beside its detail (see aisystem/detail_core.js).
//
// An AI System is a deployed use of a generative or agentic model, so the list answers
// the questions asked across an AI estate rather than a model one: what is it built on,
// can it act, and what data leaves the firm to make it work. Those three columns are
// the ones somebody scans for -- a bank's AI governance committee opens this asking
// "what have we got that is agentic, and what is it touching".
const AISystems = {
  _specs: null,
  _ref: {},
  _committees: [],

  async specs() {
    // Re-fetched so foundation models added in Admin appear in the register dropdown.
    this._specs = await App.get("/api/ai-systems/fields");
    DocLinks.configure(this._specs);
    return this._specs;
  },

  fieldSpec(key) {
    let found = null;
    this._specs.groups.forEach((g) => g.fields.forEach((f) => { if (f.key === key) found = f; }));
    return found;
  },

  // Returning to this tab lands on the list, not on whichever record was
  // last opened. The panel is cached between visits, so without this the
  // detail stays on screen with the list hidden underneath it.
  onShow() { AISystemDetail.resetToList(); },

  async render() {
    await this.specs();
    document.getElementById("tab-aisystems").innerHTML =
      '<div id="ais-listview"><div id="ais-summary"></div>' +
      '<div class="card"><div class="row" style="align-items:center">' +
      '<h3 style="margin:0">AI Systems</h3><span style="flex:1"></span>' +
      '<button class="btn small primary" id="ais-register">+ Register AI System</button>' +
      '</div><div id="ais-list" style="margin-top:var(--space-6)"></div></div></div>' +
      '<div id="ais-detail"></div>';
    document.getElementById("ais-register").onclick = () => this.openRegister();
    await this.loadList();
  },

  openRegister() {
    const idField = '<div class="field"><label for="areg-ai_system_id">' +
      'AI System ID *</label><input id="areg-ai_system_id" placeholder="AIS-0001"></div>';
    // Required fields carry the star; the optional ones (Line of Business) do not, so
    // the form never implies an obligation the domain does not enforce.
    const field = (k, required) => {
      const f = this.fieldSpec(k);
      return '<div class="field"><label for="areg-' + k + '">' + esc(f.label) +
        (required ? " *" : "") + "</label>" + inputControl("areg-" + k, f) + "</div>";
    };
    const body = this._specs.register.map((k) => field(k, true)).join("") +
      (this._specs.register_optional || []).map((k) => field(k, false)).join("");
    document.getElementById("ais-reg-body").innerHTML = idField + body;
    // Naming a line of business is what lets a Line of Business-level committee pick
    // this record up; without one it can only ever route to its division's.
    bindLineOfBusinessPicker("areg", this._ref);
    document.getElementById("ais-register-overlay").classList.remove("hidden");
    document.getElementById("areg-ai_system_id").focus();
  },

  closeRegister() {
    document.getElementById("ais-register-overlay").classList.add("hidden");
  },

  submitRegister() {
    const id = val("areg-ai_system_id");
    const fields = {};
    // The optional fields are collected the same way and simply not checked below:
    // blank is a real answer for a record governed at division level.
    this._specs.register.concat(this._specs.register_optional || [])
      .forEach((k) => { const v = val("areg-" + k); if (v !== "") fields[k] = v; });
    const missing = [id ? null : "AI System ID"]
      .concat(this._specs.register.filter((k) => !fields[k]).map((k) => this.fieldSpec(k).label))
      .filter(Boolean);
    if (missing.length) { App.toast(missing.join(", ") + " required", "error"); return; }
    this.closeRegister();
    App.amend('Register AI System "' + id + '" (' + fields.deployment_pattern + ").",
      "POST", "/api/ai-systems", { ai_system_id: id, fields: fields },
      () => this.render());
  },

  _list: null,

  list() {
    if (!this._list) {
      const self = this;
      this._list = createRecordList({
        idKey: "ai_system_id", summaryId: "ais-summary", listId: "ais-list",
        filtersId: "ais-filters", tableId: "ais-table", p: "as-",
        noun: "AI Systems",
        groupBy: "functional_group",
        // Two tiles this estate wants and no other does. Agency first, because it is
        // the question that decides which risks even apply; then what is leaving the
        // firm, because that is the one an auditor opens with.
        extraTiles: (live, tile) => {
          const agentic = live.filter((m) => /Agentic|Multi-agent/.test(m.d.deployment_pattern || ""));
          const leaving = live.filter((m) => /Confidential|Personal|Regulated/.test(m.d.data_egress || ""));
          return [
            tile("Agentic", String(agentic.length),
                 Theme.value(agentic.length ? "amber" : "green"), "can call tools"),
            tile("Sensitive data leaving", String(leaving.length),
                 Theme.value(leaving.length ? "amber" : "green"), "sent for inference"),
          ];
        },
        spec: (key) => self.fieldSpec(key),
        reload: () => self.loadList(),
      }, [
        { key: "id", label: "ID", sortVal: (m) => m.id.toLowerCase(),
          cell: (m) => '<span class="modelid">' + esc(m.id) + "</span>" },
        { key: "name", label: "Name", sortVal: (m) => (m.d.name || "").toLowerCase(),
          cell: (m) => fieldDisplay(m.d.name) },
        // The model and the version pinned to it, together: a model name without a
        // version says nothing about whether it can change under the firm.
        { key: "model", label: "Foundation model",
          sortVal: (m) => (m.d.foundation_model || "").toLowerCase(),
          cell: (m) => '<span class="code">' + fieldDisplay(m.d.foundation_model) +
            (m.d.pinned_version
              ? ' <span class="muted">' + esc(m.d.pinned_version) + "</span>" : "") +
            "</span>" },
        { key: "pattern", label: "Pattern",
          sortVal: (m) => (m.d.deployment_pattern || "").toLowerCase(),
          cell: (m) => fieldDisplay(m.d.deployment_pattern) },
        { key: "egress", label: "Data sent",
          sortVal: (m) => (m.d.data_egress || "").toLowerCase(),
          cell: (m) => fieldDisplay(m.d.data_egress) },
        { key: "tier", label: "Criticality", sortVal: (m) => m.d.tier || 99,
          cell: (m) => tierBadge(m.d.tier, m.d.division) },
        { key: "rag", label: "Risk Rating",
          sortVal: (m) => ragOrder(m.d.rag_rating, m.d.division),
          cell: (m) => ragBadge(m.d.rag_rating, m.d.division) },
        { key: "owner", label: "Owner", sortVal: (m) => (m.d.owner || "").toLowerCase(),
          cell: (m) => fieldDisplay(m.d.owner) },
        { key: "next", label: "Next Review",
          sortVal: (m) => m.d.next_review_date || "9999",
          cell: (m) => fieldDisplay(m.d.next_review_date) },
        { key: "mrc", label: "MRC Status", sortVal: (m) => mrcState(m.d),
          cell: (m) => mrcStatusBadge(m.d) },
        { key: "lifecycle", label: "Lifecycle",
          sortVal: (m) => m.retired ? "zz" : (m.d.lifecycle_stage || "").toLowerCase(),
          cell: (m) => m.retired ? '<span class="pill">retired</span>'
            : fieldDisplay(Stages.labelFor(m.d.lifecycle_stage, m.d.division)) },
      ]);
    }
    return this._list;
  },

  async loadList() {
    const nav = await MrcNav.load();
    await Groups.load();
    await Stages.load();
    this._ref = nav.ref;
    this._committees = nav.committees;
    // Hibernated records are fetched only when the Lifecycle filter asks for them —
    // and asking is the only route back to one, which is where its reactivation is
    // raised with the MRC.
    const wantsHibernated = this.list().wantsHibernated();
    const all = await App.get(
      "/api/ai-systems" + (wantsHibernated ? "?include_retired=1" : ""));
    const wanted = wantsHibernated ? all : all.filter((r) => !r.retired);
    const records = wanted.filter((r) => MrcNav.inScope(this._committees, this._ref, r.data));
    this.list().mount(records, (id) => AISystemDetail.show(id));
  },
};
