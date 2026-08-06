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

// The session identity. In production the actor comes from the client's SSO; here
// it is confirmed on entry from the People directory so every recorded change is
// attributed to someone who actually exists in the org, rather than to whatever
// was typed into a free-text box.
//
// On entry an identity gate blocks the console until you confirm who you are. Once
// confirmed the choice is fixed for the rest of the visit — the header picker is
// disabled and cannot be changed — so who you are cannot drift part-way through a
// session (an SSO would not let it). The value stamped on the audit trail is the
// person's email where they have one (it identifies them unambiguously and matches
// what an SSO would send) and their name otherwise. The last identity is
// remembered only to pre-select the gate, so a returning user just clicks Confirm.
const ACTOR_STORAGE_KEY = "modelrisk.actor";

const Actor = {
  _locked: false,

  async init() {
    const el = document.getElementById("actor-input");
    if (!el) return;
    // The header picker is a locked display of the confirmed identity — never a
    // free control. The gate below is the only way to set who you are.
    el.disabled = true;
    const overlay = document.getElementById("actor-overlay");
    const gate = document.getElementById("actor-gate-select");
    const confirmBtn = document.getElementById("actor-gate-confirm");
    // Put the gate up at once so entry is blocked before any identity-bearing
    // action; Confirm is enabled once the People list has loaded.
    if (overlay) overlay.classList.remove("hidden");
    if (confirmBtn) confirmBtn.disabled = true;
    // The identity the server resolved for this request (SSO, or the deployment's
    // configured dev fallback). Blank only if it could not resolve one at all.
    const fallback = el.getAttribute("data-default") || "";
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
    if (fallback && !options.some((o) => o.value === fallback)) {
      options.unshift({ value: fallback, label: fallback });
    }
    // Neither a directory nor a resolved identity: say so rather than offering a
    // blank option that would attribute changes to nobody.
    if (!options.length) {
      if (confirmBtn) confirmBtn.disabled = true;
      el.innerHTML = "";
      if (gate) gate.innerHTML = '<option value="">No people on record</option>';
      return;
    }
    const optionsHtml = options.map((o) =>
      '<option value="' + esc(o.value) + '">' + esc(o.label) + "</option>").join("");
    el.innerHTML = optionsHtml;
    if (gate) gate.innerHTML = optionsHtml;
    // Pre-select the last identity so a returning user just clicks Confirm, and so
    // any read issued before confirmation is still attributed to a real person.
    const saved = this._saved();
    const preset = (saved && options.some((o) => o.value === saved)) ? saved : options[0].value;
    el.value = preset;
    if (gate) gate.value = preset;
    if (confirmBtn) {
      confirmBtn.disabled = false;
      confirmBtn.onclick = () => this._confirm(gate ? gate.value : preset);
    }
    if (gate) gate.focus();
  },

  // Lock the chosen identity in for the session: stamp it on the header picker,
  // disable further change, and drop the gate. This is a one-way door by design.
  _confirm(value) {
    if (this._locked) return;
    const el = document.getElementById("actor-input");
    el.value = value;
    el.disabled = true;
    this._remember(value);
    this._locked = true;
    const label = document.querySelector(".actor label");
    if (label) label.textContent = "Signed in as";
    const hint = document.querySelector(".actor .hint");
    if (hint) {
      hint.textContent = "session identity — locked";
      hint.setAttribute("title",
        "Confirmed at entry and fixed for this session. In production your SSO sets " +
        "this; it cannot be changed mid-session.");
    }
    const overlay = document.getElementById("actor-overlay");
    if (overlay) overlay.classList.add("hidden");
  },

  _saved() {
    try { return window.localStorage.getItem(ACTOR_STORAGE_KEY); } catch (e) { return null; }
  },

  _remember(value) {
    try { window.localStorage.setItem(ACTOR_STORAGE_KEY, value); } catch (e) { /* private mode */ }
  },
};
