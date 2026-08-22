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

// The client-pack workflow: a Generate button opens a preview popup listing what
// the pack will contain (built cheaply, no PDF compilation), where the user can
// supplement it with extra documents, and a commit step that builds, retains and
// records the timestamped ZIP. Below the button sits the bi-temporal pack history.
// Augments the Clients object; loaded after clients_detail.js.
Object.assign(Clients, {
  _packSize(bytes) {
    const n = Number(bytes) || 0;
    return n >= 1024 ? (n / 1024).toFixed(1) + " KB" : n + " B";
  },

  _packSection(client) {
    const packs = ((client.data || {}).packs || []).slice().reverse();   // newest first
    const rows = packs.length
      ? packs.map((p) =>
          "<tr><td>" + esc(p.generated_at) + "</td><td>" + esc(p.as_of) + "</td><td>" +
          this._packSize(p.size) + '</td><td><a href="/api/clients/' +
          esc(client.client_id) + "/packs/" + esc(p.item_id) + '.zip">Download</a></td></tr>')
          .join("")
      : '<tr><td colspan="4" class="empty">No packs generated yet.</td></tr>';
    return '<div class="section-header">Client pack</div>' +
      '<p class="muted">Preview the full evidence pack, add any extra documents, then ' +
      "generate it. Each generation is timestamped and retained below.</p>" +
      '<div class="row" style="margin-bottom:var(--space-4)">' +
      '<button class="btn" id="cpack-preview">Generate client pack&hellip;</button></div>' +
      "<table><thead><tr><th>Generated at</th><th>As of</th><th>Size</th><th></th></tr></thead>" +
      "<tbody>" + rows + "</tbody></table>";
  },

  _wirePack(clientId) {
    const btn = document.getElementById("cpack-preview");
    if (btn) btn.onclick = () => this._openPreview(clientId);
  },

  _openPreview(clientId) {
    let ov = document.getElementById("client-pack-overlay");
    if (!ov) {
      ov = document.createElement("div");
      ov.id = "client-pack-overlay";
      ov.className = "overlay";
      document.body.appendChild(ov);
    }
    ov.classList.remove("hidden");
    this._renderPreview(clientId);
  },

  _closePreview() {
    const ov = document.getElementById("client-pack-overlay");
    if (ov) ov.classList.add("hidden");
  },

  _list(items) {
    return items.length
      ? '<ul style="margin:var(--space-2) 0 0 var(--space-9)">' + items.join("") + "</ul>"
      : '<p class="muted" style="margin:var(--space-2) 0">None.</p>';
  },

  _previewBody(m) {
    const models = m.models.map((x) =>
      "<li>" + esc(x.name || x.model_id) + " (" + esc(x.model_id) + ")" +
      (x.present ? "" : ' <span class="badge" style="background:var(--muted)">not in inventory</span>') +
      (x.attachments && x.attachments.length
        ? ' <span class="muted">— ' + x.attachments.map(esc).join(", ") + "</span>" : "") +
      "</li>");
    const supp = m.supplementary.map((d) =>
      "<li>" + esc(d.name) + ' <button class="btn small ghost" data-suppdel="' +
      esc(d.item_id) + '">Remove</button></li>');
    const warn = (m.warnings || []).length
      ? '<div class="section-header">Warnings</div>' +
        '<ul style="margin:var(--space-2) 0 0 var(--space-9);color:var(--gold)">' +
        m.warnings.map((w) => "<li>" + esc(w) + "</li>").join("") + "</ul>"
      : "";
    return '<div class="section-header">Model documentation &amp; evidence</div>' + this._list(models) +
      '<div class="section-header">Supplementary documents</div>' + this._list(supp) +
      '<div class="row" style="margin:var(--space-3) 0 var(--space-1);align-items:center">' +
      '<input type="file" id="cpack-supp-file">' +
      '<button class="btn small" id="cpack-supp-add">Add document</button></div>' +
      '<div class="section-header">Also included</div>' +
      '<ul style="margin:var(--space-2) 0 0 var(--space-9)">' +
      "<li>Recent MRC minutes: " + m.minutes.length + "</li>" +
      "<li>Operational-event write-ups: " + m.event_count + " event(s)</li>" +
      "<li>MRC Terms of Reference: " + (m.tor.present ? esc(m.tor.name) : "none uploaded") + "</li>" +
      "<li>Governance Completeness (gaps) audit</li></ul>" + warn;
  },

  async _renderPreview(clientId) {
    const ov = document.getElementById("client-pack-overlay");
    ov.innerHTML = '<div class="modal"><h2>Client pack — preview</h2>' +
      '<p class="muted">Building preview&hellip;</p></div>';
    let m;
    try {
      m = await App.get("/api/clients/" + clientId + "/pack/preview");
    } catch (e) { App.toast(e.message, "error"); this._closePreview(); return; }
    // Cap the modal to the viewport and scroll its body: the preview lists every
    // model and its documents, so it easily runs taller than the screen. The
    // header and action buttons stay put while the body scrolls (bar on the right).
    ov.innerHTML = '<div class="modal" style="width:680px;max-width:92vw;max-height:85vh;' +
      'text-align:left;display:flex;flex-direction:column">' +
      '<h2 style="flex:0 0 auto">Client pack — preview</h2>' +
      '<div style="overflow-y:auto;flex:1 1 auto;margin:0 -var(--space-2);padding:0 var(--space-2)">' +
      this._previewBody(m) + "</div>" +
      '<div class="modal-actions" style="flex:0 0 auto">' +
      '<button id="cpack-cancel" class="btn ghost">Cancel</button>' +
      '<button id="cpack-commit" class="btn primary">Generate &amp; retain</button></div></div>';
    document.getElementById("cpack-cancel").onclick = () => this._closePreview();
    document.getElementById("cpack-commit").onclick = () => this._commitPack(clientId);
    document.getElementById("cpack-supp-add").onclick = () => this._uploadSupp(clientId);
    ov.querySelectorAll("[data-suppdel]").forEach((btn) => {
      btn.onclick = () => this._removeSupp(clientId, btn.getAttribute("data-suppdel"));
    });
  },

  async _uploadSupp(clientId) {
    const input = document.getElementById("cpack-supp-file");
    if (!input.files || !input.files.length) { App.toast("Choose a file first.", "error"); return; }
    const fd = new FormData();
    fd.append("file", input.files[0]);
    try {
      const res = await fetch("/api/clients/" + clientId + "/documents",
        { method: "POST", headers: { "X-Auth-Request-User": App.actor() }, body: fd });
      if (!res.ok) throw await App._error(res);
      App.toast("Document added", "ok");
      this._renderPreview(clientId);   // refresh so it shows in the pack contents
    } catch (e) { App.toast(e.message, "error"); }
  },

  _removeSupp(clientId, itemId) {
    App.amend("Remove a supplementary document.", "POST",
      "/api/clients/" + clientId + "/documents/" + itemId + "/delete", {},
      () => this._renderPreview(clientId));
  },

  async _commitPack(clientId) {
    const btn = document.getElementById("cpack-commit");
    btn.disabled = true; btn.textContent = "Generating…";
    try {
      await App.send("POST", "/api/clients/" + clientId + "/pack", { confirmed: true });
      this._closePreview();
      App.toast("Client pack generated and retained", "ok");
      Nav.markAllDirty();
      this._showDetail(clientId);
    } catch (e) {
      App.toast(e.message, "error");
      btn.disabled = false; btn.textContent = "Generate & retain";
    }
  },
});
