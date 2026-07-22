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

// HTML-escape a value for safe insertion into the DOM.
function esc(v) {
  return String(v == null ? "" : v).replace(/[&<>"']/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
  });
}

// Read the trimmed value of an input by id.
function val(id) {
  const el = document.getElementById(id);
  return el ? el.value.trim() : "";
}

const App = {
  _pending: null,

  actor() {
    return document.getElementById("actor-input").value.trim() || "david.kelly@mkmresearchlabs.com";
  },

  headers() {
    return { "Content-Type": "application/json", "X-Auth-Request-User": this.actor() };
  },

  async get(path) {
    const res = await fetch(path, { headers: this.headers() });
    if (!res.ok) throw await this._error(res);
    return res.json();
  },

  async send(method, path, body) {
    const res = await fetch(path, {
      method: method,
      headers: this.headers(),
      body: JSON.stringify(body),
    });
    if (!res.ok) throw await this._error(res);
    return res.json();
  },

  async _error(res) {
    let message = "request failed (" + res.status + ")";
    try {
      const data = await res.json();
      if (data.error) message = data.error;
    } catch (e) {
      /* non-JSON error body */
    }
    const err = new Error(message);
    err.status = res.status;
    return err;
  },

  toast(message, kind) {
    const el = document.getElementById("toast");
    el.textContent = message;
    el.className = "toast " + (kind || "");
    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(function () {
      el.className = "toast hidden";
    }, 3200);
  },

  // Confirm-to-amend: apply the change immediately; the server decides whether
  // it is important enough (rule R1 policy) to need explicit confirmation first.
  // A 409 means confirmation is required — open the modal and re-send with the
  // reason. Non-critical changes just apply, with no dialog.
  async amend(summary, method, path, body, onDone) {
    try {
      await this.send(method, path, Object.assign({}, body || {}, { confirmed: false }));
      this._afterAmend(onDone);
    } catch (e) {
      if (e.status !== 409) { this.toast(e.message, "error"); return; }
      this._pending = { method: method, path: path, body: body, onDone: onDone };
      document.getElementById("confirm-summary").textContent = summary;
      document.getElementById("confirm-reason").value = "";
      document.getElementById("confirm-overlay").classList.remove("hidden");
    }
  },

  closeConfirm() {
    document.getElementById("confirm-overlay").classList.add("hidden");
    this._pending = null;
  },

  async confirmPending() {
    const p = this._pending;
    if (!p) return;
    const reason = document.getElementById("confirm-reason").value.trim() || null;
    const payload = Object.assign({}, p.body || {}, { confirmed: true, reason: reason });
    try {
      await this.send(p.method, p.path, payload);
      this.closeConfirm();
      this._afterAmend(p.onDone);
    } catch (e) {
      this.toast(e.message, "error");
    }
  },

  // Shared post-mutation refresh. A change may move committees/divisions/
  // lines of business, so drop the cached region nav and mark tabs stale; the current
  // tab is refreshed immediately by onDone.
  _afterAmend(onDone) {
    if (typeof MrcNav !== "undefined") MrcNav.invalidate();
    if (typeof Nav !== "undefined") Nav.markAllDirty();
    this.toast("Change recorded in the audit trail", "ok");
    if (onDone) onDone();
  },
};
