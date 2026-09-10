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
// Admin -> Lifecycle stages: the tab, and its lower pane — what one division uses.
//
// Two layers, two committees, one screen. The catalogue above is the institution's and
// the Company MRC ratifies it (lifecycle_catalogue.js); this pane is one division's
// choice from it, ratified by that division's own MRC.
//
// A division that has ratified nothing uses the WHOLE catalogue. That is not a gap to be
// filled in — it is the sensible default, and the state line says so rather than nagging.
// Narrowing is for a division that genuinely does not use a stage.
const LifecycleStagesEditor = {
  _division: null, _divisions: [], _chosen: [], _detail: null, _box: null,

  async render(container) {
    this._box = container;
    container.innerHTML = '<div id="lcat-pane"></div>' +
      '<hr style="margin:var(--space-8) 0;border:0;border-top:1px solid var(--line)">' +
      '<div id="ldiv-pane"></div>';
    // The catalogue is drawn first and re-draws this pane when it changes, because
    // narrowing a division is a choice FROM the catalogue: a stage removed above must
    // not go on being offered below.
    await LifecycleCatalogueEditor.render(document.getElementById("lcat-pane"),
                                          () => this._load());
    const reg = await App.get("/api/lifecycle-stages");
    this._divisions = Object.keys(reg.divisions || {});
    if (!this._division || this._divisions.indexOf(this._division) < 0) {
      this._division = this._divisions[0] || null;
    }
    await this._load();
  },

  async _load() {
    const box = document.getElementById("ldiv-pane");
    if (!box) return;
    if (!this._division) {
      box.innerHTML = '<div class="empty">No divisions defined yet — add one under the ' +
        "Division tab, then say which stages it uses here.</div>";
      return;
    }
    this._detail = await App.get("/api/lifecycle-stages/" +
      encodeURIComponent(this._division));
    // The draft if there is one, else what was ratified. Empty means "everything", and
    // the checkboxes below show every catalogue stage ticked to say so.
    this._chosen = (this._detail.draft || this._detail.chosen || []).slice();
    this._draw();
  },

  _catalogue() {
    return LifecycleCatalogueEditor._detail.live || [];
  },

  // What is ticked. Nothing chosen means the whole catalogue is in use, so everything
  // reads as ticked — which is also what saving that state would mean.
  _isOn(value) {
    return this._chosen.length === 0 || this._chosen.indexOf(value) >= 0;
  },

  _inUse(value) {
    return (this._detail.in_use || {})[value] || 0;
  },

  _draw() {
    const box = document.getElementById("ldiv-pane");
    box.innerHTML =
      PolicyEditor.header("ldiv", this._divisions, this._division) +
      '<p class="lead muted" style="font-size:var(--size-sm);max-width:74ch">Which of the ' +
      "catalogue's stages this division's records use, and the order its screens offer " +
      "them in. A division that has chosen nothing uses them all, which is the sensible " +
      "default — narrow it only where a stage genuinely does not apply. Edits save as a " +
      "draft and are proposed to this division's MRC.</p>" +
      '<div id="ldiv-list"></div>';
    PolicyEditor.status("ldiv", this._detail.state,
      "Nothing narrowed — this division uses every stage in the catalogue.");
    this._drawList();
    PolicyEditor.bindDivision("ldiv", (d) => { this._division = d; this._load(); });
  },

  _drawList() {
    const chosen = this._chosen.length ? this._chosen
      : this._catalogue().map((s) => s.value);
    const rows = chosen.map((value, i) => this._row(value, i)).join("");
    const unchosen = this._catalogue()
      .filter((s) => chosen.indexOf(s.value) < 0)
      .map((s) => this._offRow(s)).join("");
    document.getElementById("ldiv-list").innerHTML =
      '<table class="grid"><thead><tr><th style="width:44%">Stage</th>' +
      '<th style="width:16%">Stored as</th><th style="width:14%">Records in it</th>' +
      "<th></th></tr></thead><tbody>" + rows + unchosen + "</tbody></table>";
    this._bind();
  },

  _label(value) {
    const found = this._catalogue().find((s) => s.value === value);
    return (found && found.label) || value;
  },

  _row(value, i) {
    const inUse = this._inUse(value);
    const last = this._chosen.length ? this._chosen.length - 1
      : this._catalogue().length - 1;
    return '<tr><td><strong>' + esc(this._label(value)) + "</strong></td>" +
      '<td><span class="code">' + esc(value) + "</span></td>" +
      "<td>" + (inUse
        ? esc(inUse) + (inUse === 1 ? " record" : " records")
        : '<span class="muted">none</span>') + "</td>" +
      '<td class="rowact">' +
      '<button class="edit-btn" data-ldiv-mv="up" data-ldiv-i="' + i + '" title="Move up"' +
      (i === 0 ? " disabled" : "") + ">&uarr;</button>" +
      '<button class="edit-btn" data-ldiv-mv="down" data-ldiv-i="' + i + '" title="Move down"' +
      (i === last ? " disabled" : "") + ">&darr;</button> " +
      '<button class="btn small danger" data-ldiv-off="' + esc(value) + '"' +
      (inUse ? ' disabled title="' + esc(inUse) +
        ' record(s) are in this stage — move them first"' : "") +
      ">Not used</button></td></tr>";
  },

  _offRow(stage) {
    return '<tr class="muted"><td>' + esc(stage.label || stage.value) + "</td>" +
      '<td><span class="code">' + esc(stage.value) + "</span></td>" +
      '<td><span class="muted">not used here</span></td>' +
      '<td class="rowact"><button class="btn small" data-ldiv-on="' + esc(stage.value) +
      '">Use</button></td></tr>';
  },

  // Every change saves the WHOLE list, because what the committee ratifies is the list
  // that will be in force rather than a change to it.
  async _save(next) {
    try {
      this._detail = await App.send("POST", "/api/lifecycle-stages/" +
        encodeURIComponent(this._division) + "/propose", { stages: next });
      this._chosen = (this._detail.draft || this._detail.chosen || []).slice();
      this._draw();
    } catch (e) {
      App.toast(e.message || "Not saved", "error");
      await this._load();
    }
  },

  _bind() {
    const self = this;
    const current = () => (self._chosen.length ? self._chosen.slice()
      : self._catalogue().map((s) => s.value));
    this._box.querySelectorAll("[data-ldiv-mv]").forEach((btn) => {
      btn.onclick = () => {
        const list = current();
        const i = Number(btn.getAttribute("data-ldiv-i"));
        const j = btn.getAttribute("data-ldiv-mv") === "up" ? i - 1 : i + 1;
        if (j < 0 || j >= list.length) return;
        const t = list[i]; list[i] = list[j]; list[j] = t;
        self._save(list);
      };
    });
    this._box.querySelectorAll("[data-ldiv-off]").forEach((btn) => {
      btn.onclick = () => {
        const value = btn.getAttribute("data-ldiv-off");
        const list = current().filter((v) => v !== value);
        if (!list.length) {
          App.toast("A division has to use at least one stage", "error");
          return;
        }
        self._save(list);
      };
    });
    this._box.querySelectorAll("[data-ldiv-on]").forEach((btn) => {
      btn.onclick = () => self._save(current().concat([btn.getAttribute("data-ldiv-on")]));
    });
  },
};
