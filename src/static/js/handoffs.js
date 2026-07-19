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

// The handoff editor: the field lineage + compatibility note on one chain edge.
// Opened from the Model Chain screen. Declaring the handoff is idempotent (POST
// returns the existing one), so opening an edge that has no handoff yet creates it.
const FL_FIELDS = [
  { key: "name", label: "Field", ph: "e.g. prs_spread" },
  { key: "type", label: "Type", ph: "e.g. float" },
  { key: "units", label: "Units", ph: "e.g. bps" },
  { key: "meaning", label: "Meaning", ph: "what it represents" },
];

const Handoffs = {
  _hid: null,
  _onChange: null,   // called after any mutation so the chain can refresh counts

  // Open (declaring if needed) the handoff on from->to, into #chain-handoff.
  async open(fromModel, toModel, onChange) {
    this._onChange = onChange;
    const h = await App.send("POST", "/api/handoffs", { from_model: fromModel, to_model: toModel });
    this._hid = h.handoff_id;
    this._render(h);
    document.getElementById("chain-handoff").scrollIntoView({ block: "nearest" });
  },

  close() {
    this._hid = null;
    const box = document.getElementById("chain-handoff");
    if (box) box.innerHTML = "";
    // Refresh the chain/edges table on close, so its counts and statuses catch
    // up — doing it per-edit would re-render the panel and shut this editor.
    if (this._onChange) this._onChange();
  },

  async _reload() {
    this._render(await App.get("/api/handoffs/" + encodeURIComponent(this._hid)));
  },

  _signoffPanel(d) {
    const status = d.status || "Draft";
    if (status === "Approved") {
      return '<div class="dz-row" style="border:1px solid #388e3c;background:#e8f5e9;padding:10px 14px;border-radius:6px;margin:8px 0">' +
        '<div class="dz-text"><b>MRC compatibility sign-off — approved</b>' +
        '<p class="muted">Ratified at ' + esc(d.mrc_signoff_meeting || "a meeting") +
        (d.mrc_signoff_date ? " (" + esc(d.mrc_signoff_date) + ")" : "") +
        ". Editing the field lineage or note does not currently re-open sign-off.</p></div></div>";
    }
    if (status === "Pending sign-off") {
      return '<div class="dz-row" style="border:1px solid #f57c00;background:#fff8e1;padding:10px 14px;border-radius:6px;margin:8px 0">' +
        '<div class="dz-text"><b>Pending MRC sign-off</b>' +
        '<p class="muted">Queued for the consumer model\'s committee — it will be taken at that ' +
        "committee's next scheduled meeting.</p></div></div>";
    }
    return '<div class="dz-row" style="border:1px solid var(--line);padding:10px 14px;border-radius:6px;margin:8px 0">' +
      '<div class="dz-text"><b>Not yet submitted for sign-off</b>' +
      '<p class="muted">When the field lineage and compatibility note are ready, ask the MRC to ' +
      "ratify the handoff's compatibility.</p></div>" +
      '<div class="dz-action"><button class="btn small primary" id="ho-request">Request MRC sign-off&hellip;</button></div></div>';
  },

  _render(h) {
    const d = h.data || {};
    const rows = (d.field_lineage || []).map((f) =>
      "<tr><td><b>" + esc(f.name) + "</b></td><td>" + esc(f.type || "—") + "</td><td>" +
      esc(f.units || "—") + "</td><td>" + esc(f.meaning || "—") + "</td>" +
      '<td><button class="btn small danger" data-fl-rm="' + esc(f.item_id) + '">Remove</button></td></tr>'
    ).join("") || '<tr><td colspan="5" class="muted">No fields declared yet.</td></tr>';
    const addCells = FL_FIELDS.map((f) =>
      '<td><input id="fl-' + f.key + '" placeholder="' + esc(f.ph) + '"></td>').join("");
    document.getElementById("chain-handoff").innerHTML =
      '<div class="card" style="margin-top:14px">' +
      '<div class="row" style="align-items:center;justify-content:space-between">' +
      "<h3>Handoff &mdash; " + esc(d.from_model) + " &rarr; " + esc(d.to_model) + "</h3>" +
      '<button class="btn small" id="ho-close">Close</button></div>' +
      '<p class="muted">The fields that cross this edge, and a note on whether the producer\'s ' +
      "output is compatible with what the consumer expects.</p>" +
      this._signoffPanel(d) +
      '<div class="field" style="max-width:none"><label>Compatibility note</label>' +
      '<textarea id="ho-compat" rows="3">' + esc(d.compatibility || "") + "</textarea>" +
      '<button class="btn small primary" id="ho-compat-save" style="margin-top:6px">Save note</button></div>' +
      '<div class="section-header">Fields passed</div>' +
      "<table><thead><tr><th>Field</th><th>Type</th><th>Units</th><th>Meaning</th><th></th></tr></thead>" +
      "<tbody>" + rows + "</tbody>" +
      "<tfoot><tr>" + addCells +
      '<td><button class="btn small primary" id="fl-add">Add field</button></td></tr></tfoot></table></div>';
    this._bind();
  },

  _bind() {
    document.getElementById("ho-close").onclick = () => this.close();
    const request = document.getElementById("ho-request");
    if (request) request.onclick = async () => {
      await App.send("POST", "/api/handoffs/" + encodeURIComponent(this._hid) + "/request-signoff", {});
      this._reload();
    };
    document.getElementById("ho-compat-save").onclick = async () => {
      await App.send("POST", "/api/handoffs/" + encodeURIComponent(this._hid) + "/field",
        { field: "compatibility", value: val("ho-compat") });
      this._reload();
    };
    document.getElementById("fl-add").onclick = async () => {
      const fields = {};
      FL_FIELDS.forEach((f) => { const v = val("fl-" + f.key); if (v) fields[f.key] = v; });
      await App.send("POST", "/api/handoffs/" + encodeURIComponent(this._hid) + "/collections/field_lineage",
        { fields: fields });
      this._reload();
    };
    document.querySelectorAll("[data-fl-rm]").forEach((btn) => {
      btn.onclick = async () => {
        const id = btn.getAttribute("data-fl-rm");
        await App.send("POST", "/api/handoffs/" + encodeURIComponent(this._hid) +
          "/collections/field_lineage/" + encodeURIComponent(id) + "/delete", {});
        this._reload();
      };
    });
  },
};
