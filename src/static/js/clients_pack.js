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

// The client-pack section of a client's detail: a Generate button plus the
// bi-temporal history of retained packs (as-of + generated-at), each downloadable.
// Augments the Clients object; loaded after clients_detail.js.
Object.assign(Clients, {
  _packSize(bytes) {
    const n = Number(bytes) || 0;
    return n >= 1024 ? (n / 1024).toFixed(1) + " KB" : n + " B";
  },

  _packSection(client) {
    // Newest first: the history is appended, so reverse a copy for display.
    const packs = ((client.data || {}).packs || []).slice().reverse();
    const rows = packs.length
      ? packs.map((p) =>
          "<tr><td>" + esc(p.generated_at) + "</td><td>" + esc(p.as_of) + "</td><td>" +
          this._packSize(p.size) + '</td><td><a href="/api/clients/' +
          esc(client.client_id) + "/packs/" + esc(p.item_id) + '.zip">Download</a></td></tr>')
          .join("")
      : '<tr><td colspan="4" class="empty">No packs generated yet.</td></tr>';
    return '<div class="section-header">Client pack</div>' +
      '<p class="muted">The full evidence pack: the linked models\' documentation and ' +
      "test/analysis, recent MRC minutes, operational-event write-ups, the MRC Terms of " +
      "Reference and the Governance Completeness (gaps) audit. Each generation is timestamped " +
      "and retained below.</p>" +
      '<div class="row" style="margin-bottom:8px;align-items:center">' +
      '<button class="btn" id="cpack-gen">Generate client pack</button>' +
      '<a class="btn ghost" href="/api/clients/' + esc(client.client_id) +
      '/pack.zip">Download a fresh build now</a></div>' +
      "<table><thead><tr><th>Generated at</th><th>As of</th><th>Size</th><th></th></tr></thead>" +
      "<tbody>" + rows + "</tbody></table>";
  },

  _wirePack(clientId) {
    const btn = document.getElementById("cpack-gen");
    if (btn) {
      btn.onclick = () => App.amend("Generate a client pack.", "POST",
        "/api/clients/" + clientId + "/pack", {}, () => this._showDetail(clientId));
    }
  },
});
