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
// Opened by clicking an arrow — either on the whole-estate Model Chain screen or on
// a model's own Connections tab, which is why the host element is a parameter and
// not a constant. Declaring the handoff is idempotent (POST
// returns the existing one), so opening an edge that has no handoff yet creates it.
// A field lineage row is a pair: the provider's (giver's) field mapped to the
// consumer's (receiver's) field, so compatibility is stated field by field.
const FL_PROVIDER = [
  { key: "provider_field", label: "Field", ph: "e.g. prs_spread" },
  { key: "provider_type", label: "Type", ph: "float" },
  { key: "provider_units", label: "Units", ph: "bps" },
];
const FL_CONSUMER = [
  { key: "consumer_field", label: "Field", ph: "e.g. spread_in" },
  { key: "consumer_type", label: "Type", ph: "float" },
  { key: "consumer_units", label: "Units", ph: "bps" },
];
const FL_FIELDS = FL_PROVIDER.concat(FL_CONSUMER, [{ key: "note", label: "Note", ph: "mapping / compatibility" }]);

function _fieldCell(name, type, units) {
  const sub = [type, units].filter(Boolean).join(" · ");
  return "<b>" + esc(name || "—") + "</b>" + (sub ? '<br><span class="muted">' + esc(sub) + "</span>" : "");
}

const Handoffs = {
  _hid: null,
  _onChange: null,   // called after any mutation so the chain can refresh counts
  // Which element the panel renders into. The Chain screen has one host; a model's
  // Connections tab opens the same editor from its own arrows, into its own.
  _host: "chain-handoff",

  // Open (declaring if needed) the handoff on from->to, into the host element.
  async open(fromModel, toModel, onChange, hostId) {
    this._onChange = onChange;
    this._host = hostId || "chain-handoff";
    const h = await App.send("POST", "/api/handoffs", { from_model: fromModel, to_model: toModel });
    this._hid = h.handoff_id;
    this._render(h);
    document.getElementById(this._host).scrollIntoView({ block: "nearest" });
  },

  close() {
    this._hid = null;
    const box = document.getElementById(this._host);
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
      "<tr><td>" + _fieldCell(f.provider_field, f.provider_type, f.provider_units) +
      "</td><td>" + _fieldCell(f.consumer_field, f.consumer_type, f.consumer_units) +
      "</td><td>" + esc(f.note || "—") + "</td>" +
      '<td><button class="btn small danger" data-fl-rm="' + esc(f.item_id) + '">Remove</button></td></tr>'
    ).join("") || '<tr><td colspan="4" class="muted">No field mappings declared yet.</td></tr>';
    const side = (specs) => specs.map((f) =>
      '<div class="field"><label>' + esc(f.label) + "</label>" +
      '<input id="fl-' + f.key + '" placeholder="' + esc(f.ph) + '"></div>').join("");
    document.getElementById(this._host).innerHTML =
      '<div class="card" style="margin-top:14px">' +
      '<div class="row" style="align-items:center;justify-content:space-between">' +
      "<h3>Handoff &mdash; " + esc(d.from_model) + " &rarr; " + esc(d.to_model) + "</h3>" +
      '<div class="row" style="gap:8px">' +
      '<a class="btn small" href="/api/handoffs/' + encodeURIComponent(this._hid) +
      '/handover.pdf" target="_blank">↓ Handover document</a>' +
      '<button class="btn small" id="ho-close">Close</button></div></div>' +
      '<p class="muted">Each row pairs a <b>provider</b> field (' + esc(d.from_model) +
      ") with the <b>consumer</b> field it feeds (" + esc(d.to_model) +
      "), so compatibility is stated field by field.</p>" +
      this._signoffPanel(d) +
      '<div class="field" style="max-width:none"><label>Compatibility note</label>' +
      '<textarea id="ho-compat" rows="3">' + esc(d.compatibility || "") + "</textarea>" +
      '<button class="btn small primary" id="ho-compat-save" style="margin-top:6px">Save note</button></div>' +
      '<div class="section-header">Field lineage</div>' +
      '<table><thead><tr><th>Provider &mdash; ' + esc(d.from_model) + "</th><th>Consumer &mdash; " +
      esc(d.to_model) + "</th><th>Mapping / compatibility</th><th></th></tr></thead>" +
      "<tbody>" + rows + "</tbody></table>" +
      '<div class="row" style="gap:16px;margin-top:10px;align-items:flex-end">' +
      '<div><div class="muted" style="font-size:11px;margin-bottom:2px">PROVIDER FIELD</div>' +
      '<div class="row" style="gap:8px">' + side(FL_PROVIDER) + "</div></div>" +
      '<div><div class="muted" style="font-size:11px;margin-bottom:2px">CONSUMER FIELD</div>' +
      '<div class="row" style="gap:8px">' + side(FL_CONSUMER) + "</div></div>" +
      '<div class="field"><label>Note</label><input id="fl-note" placeholder="mapping / compatibility"></div>' +
      '<button class="btn small primary" id="fl-add">Add mapping</button></div></div>';
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
