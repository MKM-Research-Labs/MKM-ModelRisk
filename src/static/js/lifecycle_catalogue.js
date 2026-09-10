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
// Admin -> Lifecycle stages, upper pane: the institution's CATALOGUE.
//
// The words every division chooses from, and the Company-level MRC ratifies them. Edits
// auto-save as a draft proposed to that committee; records keep using the last approved
// catalogue until it signs the draft off — the same journey as the three per-division
// editors beside it, so an admin who has set one does not have to learn this.
//
// **A record stores the value and screens show the label.** Renaming here therefore
// moves nothing in the estate, which is the whole point of the two columns — and it is
// why "Stored as" is fixed once a stage exists. The domain refuses to change it, because
// every record in that stage carries it.
const LifecycleCatalogueEditor = {
  _stages: [], _detail: null, _box: null, _onChange: null,

  async render(container, onChange) {
    this._box = container;
    this._onChange = onChange;
    await this._load();
  },

  async _load() {
    this._detail = await App.get("/api/lifecycle-catalogue");
    this._syncFromDetail();
    this._draw();
  },

  // Edit the pending draft if there is one, otherwise start from the live catalogue.
  // Copied rather than referenced: the working list is edited in place, and mutating
  // what the response holds would leave the "live" it also carries reading as the draft.
  _syncFromDetail() {
    this._stages = JSON.parse(JSON.stringify(
      this._detail.draft || this._detail.live || []));
  },

  // How many live records are in a stage. A stage not yet saved has no value anybody
  // could be in, so it counts none.
  _inUse(stage) {
    return (this._detail.in_use || {})[stage.value] || 0;
  },

  // A stage the estate has never used can still have its stored value corrected; one
  // that is in use cannot, and neither can one the committee has already ratified —
  // records carry the value either way, and the domain refuses the edit.
  _valueIsFixed(stage) {
    return this._inUse(stage) > 0 ||
      (this._detail.live || []).some((s) => s.value === stage.value);
  },

  async _save() {
    try {
      this._detail = await App.send(
        "POST", "/api/lifecycle-catalogue/propose", { stages: this._stages });
      this._syncFromDetail();
      this._draw();
      if (this._onChange) this._onChange();
    } catch (e) {
      App.toast(e.message || "Not saved", "error");
      // Reloading rather than leaving the screen ahead of the server: a removal the
      // domain refused has already gone from the working list, and showing it gone
      // while it is still ratified is worse than making somebody retype a word.
      await this._load();
    }
  },

  _draw() {
    this._box.innerHTML =
      '<div class="row" style="justify-content:space-between;align-items:center">' +
      "<h3 style=\"margin:0\">The institution's catalogue</h3>" +
      '<div id="lcat-status"></div></div>' +
      '<p class="lead muted" style="font-size:var(--size-sm);max-width:74ch">Every stage ' +
      "this institution recognises, in the order they are offered. The " +
      "<strong>Company MRC</strong> ratifies this list; each division then says which of " +
      "these stages it uses, below. A record stores the value and screens show the " +
      'label, so renaming a stage moves nothing — which is why "Stored as" is fixed ' +
      "once a stage exists.</p>" +
      '<div id="lcat-list"></div>';
    PolicyEditor.status("lcat", this._detail.state,
      "Running on the stages the platform ships. Edits start a draft.");
    this._drawRatifier();
    this._drawList();
  },

  // A draft nobody can ratify is worse than no draft: it looks saved and goes nowhere.
  // The catalogue is firm-wide, so only a Company-level committee may sign it off, and
  // an estate whose only committee sits at Division level has none. Said here, before
  // somebody edits, rather than discovered when no meeting ever carries it.
  _drawRatifier() {
    if (this._detail.ratifier) return;
    this._box.insertAdjacentHTML("beforeend",
      '<div class="callout warn" style="padding:var(--space-4) var(--space-5);' +
      "border:1px solid var(--amber);border-radius:var(--radius-md);" +
      'background:var(--warn-bg);margin-bottom:var(--space-5)">' +
      "<b>No Company-level committee</b><p class=\"muted\" " +
      'style="font-size:var(--size-sm);margin:var(--space-2) 0 0">The catalogue is ' +
      "firm-wide, so a <strong>Company-level</strong> MRC ratifies it — and this " +
      "institution has not defined one. Edits here will save as a draft that no meeting " +
      "can carry. Add a Company-level committee under Admin &rarr; MRC first.</p></div>");
  },

  _drawList() {
    const rows = this._stages.length
      ? this._stages.map((s, i) => this._row(s, i)).join("")
      : '<tr><td colspan="5" class="empty">No stages. A catalogue cannot be empty.</td></tr>';
    document.getElementById("lcat-list").innerHTML =
      '<table class="grid"><thead><tr><th style="width:18%">Shown as</th>' +
      '<th style="width:16%">Stored as</th><th style="width:40%">What it means</th>' +
      '<th style="width:10%">Records in it</th><th></th></tr></thead><tbody>' + rows +
      "</tbody></table>" +
      '<div class="add-form"><div class="field"><label>Shown as</label>' +
      '<input id="lcat-new-label" placeholder="Decommissioning"></div>' +
      '<div class="field" style="flex:1;min-width:280px"><label>What it means</label>' +
      '<input id="lcat-new-desc"></div>' +
      '<div class="add-form-actions"><button class="btn small primary" id="lcat-add">' +
      "Add stage</button></div></div>";
    this._bind();
  },

  _row(stage, i) {
    const inUse = this._inUse(stage);
    const fixed = this._valueIsFixed(stage);
    return '<tr><td><input data-lcat-f="label" data-lcat-i="' + i + '" value="' +
      esc(stage.label || "") + '"></td>' +
      "<td>" + (fixed
        ? '<span class="code">' + esc(stage.value || "") + "</span>"
        : '<input data-lcat-f="value" data-lcat-i="' + i + '" value="' +
          esc(stage.value || "") + '">') + "</td>" +
      '<td><input data-lcat-f="description" data-lcat-i="' + i +
      '" style="width:100%" value="' + esc(stage.description || "") + '"></td>' +
      "<td>" + (inUse
        ? esc(inUse) + (inUse === 1 ? " record" : " records")
        : '<span class="muted">none</span>') + "</td>" +
      '<td class="rowact">' +
      '<button class="edit-btn" data-lcat-mv="up" data-lcat-i="' + i + '" title="Move up"' +
      (i === 0 ? " disabled" : "") + ">&uarr;</button>" +
      '<button class="edit-btn" data-lcat-mv="down" data-lcat-i="' + i + '" title="Move down"' +
      (i === this._stages.length - 1 ? " disabled" : "") + ">&darr;</button> " +
      '<button class="btn small danger" data-lcat-rm="' + i + '"' +
      (inUse ? ' disabled title="' + esc(inUse) +
        ' record(s) are in this stage — move them first"' : "") +
      ">Remove</button></td></tr>";
  },

  _bind() {
    const self = this;
    this._box.querySelectorAll("[data-lcat-f]").forEach((inp) => {
      inp.onchange = () => {
        self._stages[Number(inp.getAttribute("data-lcat-i"))]
          [inp.getAttribute("data-lcat-f")] = inp.value;
        self._save();
      };
    });
    this._box.querySelectorAll("[data-lcat-mv]").forEach((btn) => {
      btn.onclick = () => {
        const i = Number(btn.getAttribute("data-lcat-i"));
        const j = btn.getAttribute("data-lcat-mv") === "up" ? i - 1 : i + 1;
        if (j < 0 || j >= self._stages.length) return;
        const t = self._stages[i]; self._stages[i] = self._stages[j]; self._stages[j] = t;
        self._save();
      };
    });
    this._box.querySelectorAll("[data-lcat-rm]").forEach((btn) => {
      btn.onclick = () => {
        self._stages.splice(Number(btn.getAttribute("data-lcat-rm")), 1);
        self._save();
      };
    });
    const add = document.getElementById("lcat-add");
    if (add) {
      add.onclick = () => {
        const label = (document.getElementById("lcat-new-label").value || "").trim();
        if (!label) { App.toast("A stage needs a label", "error"); return; }
        // The stored value starts as the label, which is what makes a new stage free of
        // migration in its turn — the same rule the shipped five were seeded under.
        // It stays editable until the stage is ratified or something is in it.
        self._stages.push({ value: label, label: label,
                            description: document.getElementById("lcat-new-desc").value || "" });
        self._save();
      };
    }
  },
};
