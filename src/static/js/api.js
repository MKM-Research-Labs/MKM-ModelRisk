// Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
//
// This software is licensed by MKM Research Labs for non-commercial
// research and educational use only. Any commercial use, including
// but not limited to use in or for products or services offered for sale,
// internal business operations intended for commercial advantage, or
// research and development conducted for a commercial entity, is expressly
// prohibited unless separately authorized in writing by MKM Research Labs.
//
// Use, reproduction, distribution, or modification of this code is subject to the
// terms and conditions of the license agreement provided with this software.
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
    return document.getElementById("actor-input").value.trim() || "dev@localhost";
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

  // Confirm-to-amend: open the modal, then send the mutation with confirmed=true.
  amend(summary, method, path, body, onDone) {
    this._pending = { method: method, path: path, body: body, onDone: onDone };
    document.getElementById("confirm-summary").textContent = summary;
    document.getElementById("confirm-reason").value = "";
    document.getElementById("confirm-overlay").classList.remove("hidden");
  },

  closeConfirm() {
    document.getElementById("confirm-overlay").classList.add("hidden");
    this._pending = null;
  },

  async confirmPending() {
    const p = this._pending;
    if (!p) return;
    const reason = document.getElementById("confirm-reason").value.trim() || null;
    const payload = Object.assign({}, p.body, { confirmed: true, reason: reason });
    try {
      await this.send(p.method, p.path, payload);
      // A mutation may change committees/divisions/departments — drop the cached
      // region nav, and mark tabs stale so they re-render with fresh data on the
      // next visit (the current tab is refreshed immediately by onDone below).
      if (typeof MrcNav !== "undefined") MrcNav.invalidate();
      if (typeof Nav !== "undefined") Nav.markAllDirty();
      this.closeConfirm();
      this.toast("Change recorded in the audit trail", "ok");
      if (p.onDone) p.onDone();
    } catch (e) {
      this.toast(e.message, "error");
    }
  },
};
