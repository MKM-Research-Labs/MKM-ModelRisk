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
// The reference data an adopter maintains, rendered and edited in place.
//
// Two kinds of list, drawn the same way: the controlled vocabularies (validation
// statuses, RACI roles, learning tasks, encodings) and the reference registers
// (people, divisions, vendors, data sources).
//
// Renaming an entry here must change what every screen displays without changing what
// any record stores. That is why a value is matched on its stored key and displayed
// through its spec — a status renamed in Admin that redisplays by its stored value on
// one screen is the bug this arrangement exists to prevent.
//
// Assigns onto Reference; loads after reference.js.

Object.assign(Reference, {

  // Every vocabulary on the one Static data tab, in three groups (a row of sub-tabs): the status words a
  // record carries, the roles its RACI is assigned to, and the enumerations an ML
  // Application's training is typed against. One tab because they are one kind of
  // thing; grouped because "which words are these" is the first thing an administrator
  // needs to know. Each list is an ordinary reference list with the same two columns.
  //
  // The lifecycle stages are not here: they are ratified per division on their own
  // tab, and the old admin list for them edited a label nothing reads any more.
  _VOCABULARY_GROUPS: [
    ["Status", "The words the console shows for a record's status, in the order a record " +
      "meets them.",
     ["version_lifecycle", "validation_status", "impact_level", "priority_level",
      "remediation_status", "vq_status"]],
    ["RACI", "", ["raci_role"]],
    ["ML Training", "The enumerations an ML Application's Training tab is typed against " +
      "\u2014 the learning task, how the data was split, how it was scaled, what it was " +
      "scored on. Typed rather than free text so the estate can be asked which models " +
      "were fitted a particular way; admin-managed so you can add what you actually fit.",
     ["learning_task", "missing_data_treatment", "categorical_encoding",
      "scaling_method", "scaler_fit_point", "split_method",
      "cross_validation_method", "search_method", "determinism",
      "primary_metric", "naive_baseline"]],
  ],

  // Which group of the Vocabulary tab is open: a row of its own, like any other
  // second level on this console, rather than three headed pages run together.
  _vocabGroup: "Status",

  _renderVocabularies(container, res) {
    const groups = this._VOCABULARY_GROUPS;
    const [title, blurb, keys] = groups.find(([t]) => t === this._vocabGroup) || groups[0];
    container.innerHTML =
      '<div class="dtabs">' + groups.map(([t]) =>
        '<button class="dtab' + (t === title ? " active" : "") + '" data-vgroup="' + t + '">' +
        t + "</button>").join("") + "</div>" +
      '<p class="muted"><b>Shown as</b> is yours to change; <b>stored as</b> is the word ' +
      "the records themselves carry and the code matches on, fixed once an entry exists. " +
      "Renaming therefore changes every screen without moving anything on record." +
      (blurb ? " " + blurb : "") + "</p>" +
      keys.map((key) => '<div id="voc-' + key + '"></div>').join("");
    container.querySelectorAll("[data-vgroup]").forEach((btn) => {
      btn.onclick = () => {
        this._vocabGroup = btn.getAttribute("data-vgroup");
        this._renderVocabularies(container, res);
      };
    });
    keys.forEach((key) => {
      const spec = res.collections.find((c) => c.key === key);
      if (!spec) return;
      // Each list says what it governs. The paragraph above explains the columns and
      // the group; this says which words these are.
      this._renderList(document.getElementById("voc-" + key), spec,
                       res.data[key] || [], spec.hint || "");
    });
  },

  // A plain reference list rendered as a table with a working add form and
  // inline edit / remove per row (via the confirm-to-amend flow). Selectors
  // mirror the shared Collections module so the e2e helpers can drive both.
  _renderList(container, spec, items, intro) {
    const cols = spec.fields.filter((f) => !f.hidden);
    const head = cols.map((f) => "<th>" + esc(f.label) + "</th>").join("") + "<th></th>";
    const body = items.length
      ? items.map((it, i) =>
          '<tr id="rlrow-' + esc(it.item_id) + '">' +
          cols.map((f) => "<td>" + optionLabel(f, it[f.key]) + "</td>").join("") +
          '<td class="rowact">' +
          '<button class="edit-btn" data-mv="up|' + esc(it.item_id) + '" title="Move up"' +
          (i === 0 ? " disabled" : "") + ">\u2191</button>" +
          '<button class="edit-btn" data-mv="down|' + esc(it.item_id) + '" title="Move down"' +
          (i === items.length - 1 ? " disabled" : "") + ">\u2193</button> " +
          '<button class="btn small" data-ed="' + esc(spec.key) + "|" + esc(it.item_id) +
          '">Edit</button> <button class="btn small danger" data-rm="' + esc(spec.key) + "|" + esc(it.item_id) +
          '">Remove</button></td></tr>').join("")
      : '<tr><td colspan="' + (cols.length + 1) + '" class="empty">None yet.</td></tr>';
    // A readonly field (a person's ratified roles) is recorded by the process that
    // grants it, so it is shown in the table but never offered as an input.
    // A prose field takes the width that is going. The add row is a flex row, so a
    // textarea sized by its rows attribute alone sat in a small box with the rest of
    // the line empty beside it — on the review questions, the field holding the
    // longest text on the screen was the narrowest thing on it. A multichoice is
    // the same shape of problem: it lists its options down the row and got no more
    // room than a one-line text box, which left the roles picker cramped.
    const wide = (f) => f.type === "textarea" || f.type === "multichoice";
    const addInputs = cols.filter((f) => !f.readonly).map((f) =>
      '<div class="field"' + (wide(f) ? ' style="flex:1;min-width:280px"' : "") +
      "><label>" + esc(f.label) + (f.required ? " *" : "") + "</label>" +
      inputControl("add-" + spec.key + "-" + f.key, f) + "</div>").join("");
    container.innerHTML =
      '<div class="section-header">' + esc(spec.label) + "</div>" +
      (intro ? '<p class="muted" style="font-size:var(--size-sm)">' + intro + "</p>" : "") +
      "<table><thead><tr>" + head + "</tr></thead><tbody>" + body + "</tbody></table>" +
      '<div class="row" style="margin-top:var(--space-4)">' + addInputs +
      '<button class="btn small" data-add="' + esc(spec.key) + '">Add&hellip;</button></div>';
    container.querySelector('[data-add="' + spec.key + '"]').onclick = () => {
      const fields = {};
      // An empty list is dropped on ADD (nothing to say yet); on edit it is kept, so a
      // role can be taken away.
      cols.filter((f) => !f.readonly).forEach((f) => {
        const v = val("add-" + spec.key + "-" + f.key);
        if (v !== "" && !(Array.isArray(v) && !v.length)) fields[f.key] = v;
      });
      App.amend("Add to " + spec.label + ".", "POST",
        "/api/reference/collections/" + spec.key, { fields: fields }, () => this.render());
    };
    container.querySelectorAll("[data-rm]").forEach((btn) => {
      const id = btn.getAttribute("data-rm").split("|")[1];
      btn.onclick = () => App.amend("Remove " + id + ".", "POST",
        "/api/reference/collections/" + spec.key + "/" + id + "/delete", {}, () => this.render());
    });
    container.querySelectorAll("[data-mv]").forEach((btn) => {
      if (btn.disabled) return;
      const [direction, id] = btn.getAttribute("data-mv").split("|");
      // Reordering is an edit to what every dropdown offers, so it is confirmed and
      // recorded like the others rather than treated as a display preference.
      btn.onclick = () => App.amend("Move " + id + " " + direction + ".", "POST",
        "/api/reference/collections/" + spec.key + "/" + id + "/move",
        { direction: direction }, () => this.render());
    });
    container.querySelectorAll("[data-ed]").forEach((btn) => {
      const id = btn.getAttribute("data-ed").split("|")[1];
      const item = items.find((i) => i.item_id === id);
      btn.onclick = () => this._listEdit(spec, cols, item);
    });
  },

  _listEdit(spec, cols, item) {
    const row = document.getElementById("rlrow-" + item.item_id);
    row.innerHTML = '<td colspan="' + (cols.length + 1) + '"><div class="row">' +
      cols.map((f) => '<div class="field"><label>' + esc(f.label) + "</label>" +
        (f.readonly || f.immutable
          ? '<div class="ro">' + fieldDisplay(item[f.key]) + "</div>"
          : inputControl("ce-" + f.key, f)) + "</div>").join("") +
      '<button class="btn small primary" id="ce-save">Save&hellip;</button>' +
      '<button class="btn small" id="ce-cancel">Cancel</button></div></td>';
    cols.filter((f) => !f.readonly && !f.immutable).forEach((f) => {
      const el = document.getElementById("ce-" + f.key);
      const current = item[f.key];
      if (current === null || current === undefined) return;
      // A multi-select cannot be filled by assigning `.value`; each held value has to be
      // marked selected, or editing a person would quietly drop their roles.
      if (el.multiple) {
        const held = new Set(Array.isArray(current) ? current : [current]);
        [...el.options].forEach((o) => { o.selected = held.has(o.value); });
      } else {
        el.value = current;
      }
    });
    document.getElementById("ce-cancel").onclick = () => this.render();
    document.getElementById("ce-save").onclick = () => {
      const fields = {};
      cols.filter((f) => !f.readonly && !f.immutable).forEach((f) => {
        const v = val("ce-" + f.key);
        if (v !== "" || Array.isArray(v)) fields[f.key] = v;
      });
      App.amend("Update " + item.item_id + ".", "POST",
        "/api/reference/collections/" + spec.key + "/" + item.item_id, { fields: fields }, () => this.render());
    };
  },
});
