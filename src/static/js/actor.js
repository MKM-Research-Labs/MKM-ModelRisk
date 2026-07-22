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

// The header "Acting as" picker. In production the actor comes from the client's
// SSO; here it is chosen from the People directory so every recorded change is
// attributed to someone who actually exists in the org, rather than to whatever
// was typed into a free-text box.
//
// The value stamped on the audit trail is the person's email where they have one
// (it identifies them unambiguously and matches what an SSO would send) and their
// name otherwise. The selection is remembered, so a reload does not silently
// change who you are part-way through a session.
const ACTOR_STORAGE_KEY = "modelrisk.actor";

const Actor = {
  async init() {
    const el = document.getElementById("actor-input");
    if (!el) return;
    const fallback = el.getAttribute("data-default") || "dev@localhost";
    let people = [];
    try {
      // /api/reference returns {collections: [specs], data: {list: [rows]}}.
      const lists = await App.get("/api/reference");
      people = (lists && lists.data && lists.data.people) || [];
    } catch (e) { /* reference lists not reachable yet */ }
    const options = people
      .map((p) => ({ value: p.email || p.name, label: p.name || p.email }))
      .filter((o) => o.value);
    // A fresh instance has no People yet; the fallback keeps the console usable
    // (and keeps whatever the deployment's SSO header already resolved to).
    if (!options.some((o) => o.value === fallback)) {
      options.unshift({ value: fallback, label: fallback });
    }
    el.innerHTML = options.map((o) =>
      '<option value="' + esc(o.value) + '">' + esc(o.label) + "</option>").join("");
    const saved = this._saved();
    if (saved && options.some((o) => o.value === saved)) el.value = saved;
    el.onchange = () => this._remember(el.value);
  },

  _saved() {
    try { return window.localStorage.getItem(ACTOR_STORAGE_KEY); } catch (e) { return null; }
  },

  _remember(value) {
    try { window.localStorage.setItem(ACTOR_STORAGE_KEY, value); } catch (e) { /* private mode */ }
  },
};
