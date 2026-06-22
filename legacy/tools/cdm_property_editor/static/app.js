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

let ASSETS = [];          // [{key, label}]
let ASSET = null;         // active asset key
let SCHEMA = null;        // { sections: [...], schema: {...} } for active asset
let ITEMS = [];           // summary rows for active asset
let CURRENT = null;       // full record open in the modal
let CURRENT_ID = null;
let ACTIVE_SECTION = null;
let ACTIVE_PERIL = "flood";
// Set after a RED commit returns an instant before/after recompute; consumed by
// the PRS Waterfall tab to overlay the baseline ("before") against the edit.
let PENDING_RECOMPUTE = null;
let CURRENT_PERILS = null; // {flood, wind, fire, seismic} for open record (null = loading)
let LINEAGE = null;        // {tiers, exact, amberPrefixes} from /api/lineage
let EDIT_SPECS = {};       // asset -> {path: spec} from /api/<asset>/edit-spec

const PERILS = [
  { key: "flood", label: "Flood" },
  { key: "wind", label: "Wind" },
  { key: "fire", label: "Fire" },
  { key: "seismic", label: "Seismic" },
];

// ---- field-usage lineage (mirrors lineage.field_usage.resolve) -------------

function lineageFor(path) {
  if (!LINEAGE) return null;
  if (LINEAGE.exact[path]) return LINEAGE.exact[path];
  for (const ap of LINEAGE.amberPrefixes) {
    if (path === ap.prefix || path.startsWith(ap.prefix + ".")) return ap.entry;
  }
  return {
    tier: "GREEN",
    summary: "Descriptive field — surfaced in the asset report only; not used by a "
             + "model or the PRS.",
    consumers: ["Asset report"],
    chain: [{ node: (path.split(".").pop() || path) + " (CDM)", kind: "field" },
            { node: "Asset report", kind: "output" }],
  };
}

function tierOf(path) {
  const e = lineageFor(path);
  return e ? e.tier : "GREEN";
}

const $ = (sel) => document.querySelector(sel);

const AUDIT_KEY = "__audit__";        // special top tab (not an asset)
const WATERFALL_KEY = "__waterfall__"; // synthetic detail tab (not a CDM section)
const WATERFALL_ASSETS = ["property", "commercial"];

// Synthetic "Report" detail tab — links to the main app's detailed PDF report
// for the asset. The value is the parent-window generator the report tab calls
// (the same functions the main-app context menus invoke via backend-handler.js).
const REPORT_KEY = "__report__";
const REPORT_FNS = {
  property: "generateReport",
  gauge: "generateGaugeReport",
  commercial: "generateCommercialReport",
  mortgage: "generateRLoanReport",
  commercial_loan: "generateCLoanReport",
};

const EYE_SVG =
  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
  'stroke-linecap="round" stroke-linejoin="round">' +
  '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>' +
  '<circle cx="12" cy="12" r="3"/></svg>';

// ---- helpers ---------------------------------------------------------------

function isField(node) {
  return node && typeof node === "object" && !Array.isArray(node) &&
         typeof node.type === "string";
}

function prettyLabel(key) {
  return String(key)
    .replace(/^_/, "")
    .replace(/_/g, " ")
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/([A-Z]+)([A-Z][a-z])/g, "$1 $2");
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") return "—";
  if (Array.isArray(value)) return value.length ? value.join(", ") : "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function fmtMoney(v) {
  if (v === null || v === undefined) return "";
  const n = Number(v);
  if (Number.isNaN(n)) return String(v);
  return "£" + n.toLocaleString(undefined, { maximumFractionDigits: 0 });
}

function badge(text, cls) {
  return `<span class="badge ${cls || "badge-na"}">${text || "—"}</span>`;
}

function assetLabel(key) {
  const a = ASSETS.find((x) => x.key === key);
  return a ? a.label : key;
}

// ---- top tab bar -----------------------------------------------------------

function renderAssetTabs() {
  const bar = $("#asset-tabs");
  bar.innerHTML = "";
  for (const a of ASSETS) {
    const btn = document.createElement("button");
    btn.className = "asset-tab" + (a.key === ASSET ? " active" : "");
    btn.textContent = a.label;
    btn.addEventListener("click", () => selectAsset(a.key));
    bar.appendChild(btn);
  }
}

// ---- left list -------------------------------------------------------------

function renderList(filter = "") {
  const list = $("#item-list");
  const f = filter.trim().toLowerCase();
  const items = ITEMS.filter((p) =>
    !f ||
    (p.id && String(p.id).toLowerCase().includes(f)) ||
    (p.sub && String(p.sub).toLowerCase().includes(f)) ||
    (p.tag && String(p.tag).toLowerCase().includes(f))
  );

  list.innerHTML = "";
  for (const p of items) {
    const li = document.createElement("li");
    li.className = "property-item" + (p.id === CURRENT_ID ? " active" : "");
    li.innerHTML =
      `<div class="pi-main">` +
        `<div class="pi-id">${p.id ?? "—"}</div>` +
        `<div class="pi-addr">${p.sub || ""}</div>` +
        `<div class="pi-meta">${badge(p.tag, p.tagClass)}` +
          `<span class="pi-value">${fmtMoney(p.value)}</span></div>` +
      `</div>` +
      `<button class="review-btn" title="Review detailed data" ` +
        `aria-label="Review ${p.id}">${EYE_SVG}</button>`;
    li.querySelector(".review-btn").addEventListener("click", (e) => {
      e.stopPropagation();
      openDetail(p.id);
    });
    li.addEventListener("click", () => openDetail(p.id));
    list.appendChild(li);
  }
  $("#count").textContent = `${items.length} / ${ITEMS.length} ${assetLabel(ASSET).toLowerCase()}`;
}

// ---- summary dashboard -----------------------------------------------------

function renderSummary() {
  const cards = $("#cards");
  const n = ITEMS.length;
  const byTag = {};
  let totalValue = 0;
  let hasValue = false;
  for (const p of ITEMS) {
    const t = p.tag || "—";
    byTag[t] = (byTag[t] || 0) + 1;
    if (typeof p.value === "number") { totalValue += p.value; hasValue = true; }
  }
  const tagLine = Object.entries(byTag)
    .sort((a, b) => b[1] - a[1])
    .map(([k, v]) => `${k}: ${v}`).join(" · ");

  const card = (label, value, sub) =>
    `<div class="card"><div class="card-label">${label}</div>` +
    `<div class="card-value">${value}</div>` +
    (sub ? `<div class="card-sub">${sub}</div>` : "") + `</div>`;

  cards.innerHTML =
    card(assetLabel(ASSET), n, tagLine) +
    card("Total Value", hasValue ? fmtMoney(totalValue) : "—",
         hasValue ? "aggregate" : "no monetary value") +
    card("Categories", Object.keys(byTag).length, "distinct tags") +
    card("CDM Sections", (SCHEMA?.sections || []).length, "schema-defined");
}

// ---- detail modal ----------------------------------------------------------

// Mini location map: a self-rendered slippy map — OSM raster tiles placed as
// <img> elements with a centre marker. No library or API key; renders directly
// in our DOM (a cross-origin OSM iframe does not paint reliably here).
const MAP_W = 310, MAP_H = 122, MAP_Z = 15, TILE = 256;

function miniMapHtml(lat, lon) {
  if (typeof lat !== "number" || typeof lon !== "number") return "";
  const n = 2 ** MAP_Z;
  const xf = ((lon + 180) / 360) * n;
  const latRad = (lat * Math.PI) / 180;
  const yf = ((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2) * n;
  const left = xf * TILE - MAP_W / 2; // world-pixel of the container's top-left
  const top = yf * TILE - MAP_H / 2;
  const x0 = Math.floor(left / TILE), x1 = Math.floor((left + MAP_W) / TILE);
  const y0 = Math.floor(top / TILE), y1 = Math.floor((top + MAP_H) / TILE);

  let tiles = "";
  for (let tx = x0; tx <= x1; tx++) {
    for (let ty = y0; ty <= y1; ty++) {
      if (tx < 0 || ty < 0 || tx >= n || ty >= n) continue;
      const px = tx * TILE - left, py = ty * TILE - top;
      tiles += `<img alt="" src="https://tile.openstreetmap.org/${MAP_Z}/${tx}/${ty}.png" ` +
        `style="left:${px}px;top:${py}px" />`;
    }
  }
  const big = `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=${MAP_Z}/${lat}/${lon}`;
  return `<div class="dc-map">` +
    `<div class="mini-map">${tiles}<div class="map-pin"></div>` +
      `<span class="map-attr">© OpenStreetMap</span></div>` +
    `<div class="dc-coords">` +
      `<span>${lat.toFixed(5)}, ${lon.toFixed(5)}</span>` +
      `<a href="${big}" target="_blank" rel="noopener">Larger map ↗</a>` +
    `</div></div>`;
}

function renderDetailCard() {
  const s = ITEMS.find((x) => x.id === CURRENT_ID) || {};
  const valueHtml = (s.value === null || s.value === undefined)
    ? ""
    : `<div class="dc-value"><div class="label">Value</div>` +
      `<div class="amount">${fmtMoney(s.value)}</div></div>`;
  const hasMap = typeof s.lat === "number" && typeof s.lon === "number";

  // Right-hand aside (≤1/3): map + perils panel, sat inside the blue header
  // alongside the prop identity. Shown for assets that have a location.
  const aside = hasMap
    ? `<div class="dc-aside">` +
        `<div class="peril-card">` +
          `<div class="peril-tabs" id="peril-tabs"></div>` +
          `<div class="peril-content" id="peril-content"></div>` +
        `</div>` +
        miniMapHtml(s.lat, s.lon) +
      `</div>`
    : "";

  $("#detail-card").innerHTML =
    `<div class="dc-identity">` +
      `<div class="dc-info">` +
        `<div class="dc-id">${CURRENT_ID}</div>` +
        `<div class="dc-sub">${s.sub || ""}</div>` +
        `<div class="dc-badges">${badge(s.tag, s.tagClass)}` +
          `<span class="dc-asset">${assetLabel(ASSET)}</span></div>` +
        valueHtml +
      `</div>` + aside +
    `</div>`;
  if (hasMap) { renderPerilTabs(); renderPerilContent(); }
}

function renderPerilTabs() {
  const bar = $("#peril-tabs");
  if (!bar) return;
  bar.innerHTML = "";
  for (const p of PERILS) {
    const btn = document.createElement("button");
    btn.className = "peril-tab" + (p.key === ACTIVE_PERIL ? " active" : "");
    btn.textContent = p.label;
    btn.addEventListener("click", () => {
      ACTIVE_PERIL = p.key;
      renderPerilTabs();
      renderPerilContent();
    });
    bar.appendChild(btn);
  }
}

function clusterBadge(type) {
  const cls = { isolated: "cl-isolated", doublet: "cl-doublet",
                cluster: "cl-cluster", persistent: "cl-persistent" }[type] || "cl-na";
  return `<span class="cl-badge ${cls}">${type || "—"}</span>`;
}

function msgHtml(text) { return `<div class="peril-msg">${text}</div>`; }

function fmtStat(s) {
  if (s.value === null || s.value === undefined) return "—";
  if (s.pct) return (s.value * 100).toFixed(2) + "%";
  const v = Number(s.value);
  if (Number.isNaN(v)) return String(s.value);
  if (v !== 0 && Math.abs(v) < 0.001) return v.toExponential(2);
  return v.toPrecision(3).replace(/\.?0+$/, "");
}

function segBarHtml(items) {
  const total = items.reduce((a, b) => a + (b.count || 0), 0) || 1;
  const seg = items.filter((it) => it.count > 0).map((it) =>
    `<span class="seg seg-${it.cls}" style="width:${(it.count / total * 100).toFixed(1)}%" ` +
    `title="${it.label}: ${it.count}"></span>`).join("");
  const legend = items.map((it) =>
    `<span class="lg"><span class="dot dot-${it.cls}"></span>${it.label}: ` +
    `<b>${(it.count || 0).toLocaleString()}</b></span>`).join("");
  return `<div class="seg-bar">${seg}</div><div class="seg-legend">${legend}</div>`;
}

function statRowsHtml(items) {
  return `<table class="stat-table"><tbody>` + items.map((s) =>
    `<tr><td>${s.label}</td><td class="sv">${fmtStat(s)}</td></tr>`).join("") +
    `</tbody></table>`;
}

// Flood / wind — a list of discrete events.
function eventTableHtml(data, peril) {
  if (!data || !data.supported) return msgHtml(data && data.reason || "Not modelled.");
  const evs = data.events || [];
  if (!evs.length)
    return msgHtml(data.note ||
      (`No ${peril} events on record` + (data.flood_zone ? ` · ${data.flood_zone}` : "") + "."));
  let rows = "";
  for (const e of evs) {
    const tip = `peak ${e.peak_m} m · depth ${e.depth_m} m` + (e.intensity ? ` · ${e.intensity}` : "");
    rows += `<tr title="${tip}"><td class="pt-storm">${e.storm}</td>` +
      `<td>${clusterBadge(e.type)}</td>` +
      `<td class="pt-num">${e.depth_m ? e.depth_m.toFixed(2) + " m" : "—"}</td>` +
      `<td class="pt-dmg">${e.damage_pct ? e.damage_pct.toFixed(1) + "%" : "—"}</td></tr>`;
  }
  const cap = `Top ${evs.length} of ${data.count} events` +
              (data.flood_zone ? ` &middot; ${data.flood_zone}` : "");
  return `<div class="peril-cap">${cap}</div>` +
    `<div class="peril-scroll"><table class="peril-table"><thead><tr>` +
      `<th>Storm</th><th>Type</th><th>Depth</th><th>Damage</th>` +
    `</tr></thead><tbody>${rows}</tbody></table></div>`;
}

// Fire — outcome distribution over simulated fires (commercial only).
function fireHtml(data) {
  if (!data || !data.supported) return msgHtml(data && data.reason || "Not modelled.");
  const cap = `${data.model} &middot; λ ${Number(data.lambda_annual).toFixed(3)}/yr &middot; ` +
              `${(data.n_fires || 0).toLocaleString()} fires / ${(data.n_sim || 0).toLocaleString()} sims`;
  return `<div class="peril-cap">${cap}</div>` +
    `<div class="peril-scroll">${segBarHtml(data.outcomes)}` +
    statRowsHtml(data.stats) + `</div>`;
}

// Seismic — site profile + damage-state distribution (commercial only).
function seismicHtml(data) {
  if (!data || !data.supported) return msgHtml(data && data.reason || "Not modelled.");
  const cap = `${data.model} &middot; ${data.n_events} events / ${(data.n_sim || 0).toLocaleString()} sims`;
  return `<div class="peril-cap">${cap}</div>` +
    `<div class="peril-scroll">${statRowsHtml(data.site)}` +
    `<div class="ds-title">Damage states</div>${segBarHtml(data.damage_states)}` +
    statRowsHtml(data.stats) + `</div>`;
}

function renderPerilContent() {
  const el = $("#peril-content");
  if (!el) return;
  if (CURRENT_PERILS === null) { el.innerHTML = msgHtml("Loading…"); return; }
  const data = CURRENT_PERILS[ACTIVE_PERIL];
  if (ACTIVE_PERIL === "fire") el.innerHTML = fireHtml(data);
  else if (ACTIVE_PERIL === "seismic") el.innerHTML = seismicHtml(data);
  else el.innerHTML = eventTableHtml(data, ACTIVE_PERIL);
}

async function loadPerils() {
  if (!(ASSET && CURRENT_ID)) return;
  const reqId = CURRENT_ID;
  CURRENT_PERILS = null;
  renderPerilContent();
  try {
    const res = await fetch(`/api/${ASSET}/items/${encodeURIComponent(CURRENT_ID)}/perils`);
    const data = await res.json();
    if (reqId !== CURRENT_ID) return; // a different record was opened meanwhile
    CURRENT_PERILS = data;
  } catch (err) {
    if (reqId !== CURRENT_ID) return;
    CURRENT_PERILS = {};
  }
  renderPerilContent();
}

// Section tabs come from the record's own top-level keys, ordered schema-first
// then any data-only keys (e.g. _commercial_meta), so nothing is hidden.
function recordSections() {
  const schemaKeys = Object.keys(SCHEMA.schema);
  const dataKeys = Object.keys(CURRENT || {});
  const ordered = schemaKeys.filter((k) => dataKeys.includes(k));
  for (const k of dataKeys) if (!schemaKeys.includes(k)) ordered.push(k);
  return ordered.length ? ordered : dataKeys;
}

function renderDetailTabs() {
  const tabs = $("#detail-tabs");
  tabs.innerHTML = "";
  const sections = recordSections().slice();
  // Synthetic PRS Waterfall tab, right of the CDM sections (property/commercial).
  if (WATERFALL_ASSETS.includes(ASSET)) sections.push(WATERFALL_KEY);
  // Synthetic Report tab — links to the asset's detailed PDF report.
  if (REPORT_FNS[ASSET]) sections.push(REPORT_KEY);
  for (const section of sections) {
    const btn = document.createElement("button");
    btn.className = "detail-tab" + (section === ACTIVE_SECTION ? " active" : "");
    if (section === WATERFALL_KEY) btn.classList.add("waterfall-tab");
    if (section === REPORT_KEY) btn.classList.add("report-tab");
    btn.textContent = section === WATERFALL_KEY ? "PRS Waterfall"
      : (section === REPORT_KEY ? "Report" : prettyLabel(section));
    btn.addEventListener("click", () => {
      ACTIVE_SECTION = section;
      renderDetailTabs();
      renderDetailBody();
    });
    tabs.appendChild(btn);
  }
}

function orderedEntries(schema, data) {
  const out = [];
  const seen = new Set();
  for (const [key, node] of Object.entries(schema)) {
    seen.add(key);
    out.push([key, node, data[key], isField(node) ? "field" : "group"]);
  }
  for (const [key, val] of Object.entries(data)) {
    if (seen.has(key)) continue;
    const isObj = val && typeof val === "object" && !Array.isArray(val);
    out.push([key, isObj ? {} : null, val, isObj ? "group" : "field"]);
  }
  return out;
}

const KEBAB_SVG =
  '<svg viewBox="0 0 24 24" width="14" height="14"><circle cx="12" cy="5" r="1.6"/>' +
  '<circle cx="12" cy="12" r="1.6"/><circle cx="12" cy="19" r="1.6"/></svg>';

function renderField(key, descriptor, value, path) {
  const fieldPath = path ? path + "." + key : key;
  const tier = tierOf(fieldPath);

  const cell = document.createElement("div");
  cell.className = "field tier-" + tier.toLowerCase();
  cell.dataset.path = fieldPath;

  const label = document.createElement("div");
  label.className = "field-label";
  label.textContent = prettyLabel(key);
  if (descriptor && descriptor.description) label.title = descriptor.description;

  // 3-dots field menu (extensible — lineage is the first item).
  const kebab = document.createElement("button");
  kebab.className = "field-kebab";
  kebab.title = "Field actions";
  kebab.innerHTML = KEBAB_SVG;
  kebab.addEventListener("click", (e) => {
    e.stopPropagation();
    openFieldMenu(kebab, fieldPath, prettyLabel(key), value);
  });
  label.appendChild(kebab);

  const val = document.createElement("div");
  val.className = "field-value";
  val.textContent = formatValue(value);

  const typ = document.createElement("div");
  typ.className = "field-type";
  typ.textContent = descriptor ? descriptor.type : "unknown";

  cell.appendChild(label);
  cell.appendChild(val);
  cell.appendChild(typ);
  return cell;
}

// Build an editor widget for a field from its spec (menu→select, number with
// min/max/step, date, checkbox, text), pre-filled with the current value. The
// caller reads the value on commit; for a checkbox use `.checked`.
function makeFieldInput(value, spec) {
  const cur = value;
  let el;
  if (spec.input === "select") {
    el = document.createElement("select");
    const blank = document.createElement("option");
    blank.value = ""; blank.textContent = "—";
    el.appendChild(blank);
    for (const opt of spec.options || []) {
      const o = document.createElement("option");
      o.value = opt; o.textContent = opt;
      if (String(cur) === String(opt)) o.selected = true;
      el.appendChild(o);
    }
  } else if (spec.input === "checkbox") {
    el = document.createElement("input");
    el.type = "checkbox";
    el.checked = cur === true || ["yes", "true", "1"].includes(String(cur).toLowerCase());
  } else {
    el = document.createElement("input");
    el.type = spec.input === "number" ? "number" : (spec.input === "date" ? "date" : "text");
    if (spec.input === "number") {
      if (spec.min !== null && spec.min !== undefined) el.min = spec.min;
      if (spec.max !== null && spec.max !== undefined) el.max = spec.max;
      if (spec.step !== null && spec.step !== undefined) el.step = spec.step;
    }
    el.value = (cur === null || cur === undefined) ? "" : cur;
  }
  el.className = "field-input";
  return el;
}

function renderGroup(schemaNode, dataNode, depth, path) {
  const frag = document.createDocumentFragment();
  const data = dataNode && typeof dataNode === "object" ? dataNode : {};
  const schema = schemaNode && typeof schemaNode === "object" ? schemaNode : {};

  let grid = null;
  const flush = () => { if (grid) { frag.appendChild(grid); grid = null; } };

  for (const [key, node, value, kind] of orderedEntries(schema, data)) {
    if (kind === "field") {
      if (!grid) { grid = document.createElement("div"); grid.className = "field-grid"; }
      grid.appendChild(renderField(key, node, value, path));
    } else {
      flush();
      const block = document.createElement("section");
      block.className = "subsection level-" + Math.min(depth, 3);
      const h = document.createElement("h3");
      h.className = "subsection-title";
      h.textContent = prettyLabel(key);
      block.appendChild(h);
      block.appendChild(renderGroup(node, value, depth + 1, path ? path + "." + key : key));
      frag.appendChild(block);
    }
  }
  flush();
  return frag;
}

function renderDetailBody() {
  const body = $("#detail-body");
  body.innerHTML = "";
  if (ACTIVE_SECTION === WATERFALL_KEY) { renderWaterfall(body); return; }
  if (ACTIVE_SECTION === REPORT_KEY) { renderReport(body); return; }
  const schemaNode = SCHEMA.schema[ACTIVE_SECTION] || {};
  const dataNode = CURRENT[ACTIVE_SECTION] || {};
  // A leaf-only section (rare) still renders by wrapping the value. The dotted
  // path is rooted at the section so it matches the lineage registry keys.
  if (dataNode && typeof dataNode === "object") {
    body.appendChild(renderGroup(schemaNode, dataNode, 0, ACTIVE_SECTION));
  } else {
    const grid = document.createElement("div");
    grid.className = "field-grid";
    grid.appendChild(renderField(ACTIVE_SECTION, isField(schemaNode) ? schemaNode : null, dataNode, ""));
    body.appendChild(grid);
  }
  const count = body.querySelectorAll(".field").length;
  $("#modal-foot").innerHTML =
    `<span>Section: <b>${prettyLabel(ACTIVE_SECTION)}</b></span>` +
    `<span>${count} fields</span>` +
    lineageLegendHtml();
}

// ---- PRS spread waterfall (synthetic tab) ---------------------------------

async function renderWaterfall(body) {
  $("#modal-foot").innerHTML = "<span>PRS spread waterfall</span>";
  body.innerHTML = `<div class="wf-msg">Loading waterfall…</div>`;
  let data;
  try {
    data = await (await fetch(
      `/api/${ASSET}/items/${encodeURIComponent(CURRENT_ID)}/waterfall`)).json();
  } catch (e) { body.innerHTML = `<div class="wf-msg">Failed to load waterfall.</div>`; return; }
  if (!data.supported) {
    body.innerHTML = `<div class="wf-msg">${data.reason || "Not available."}</div>`;
    return;
  }
  const sd = data.spread_decomposition;
  if (!sd || !Object.keys(sd).length) {
    body.innerHTML = `<div class="wf-msg">${data.note || "No waterfall for this asset."}</div>`;
    return;
  }
  // Reuse the main app's spread-waterfall renderer verbatim (the perfect basis
  // right panel) — fed via its `phcData.spread_decomposition` global and drawn
  // into a canvas, instead of duplicating the bar layout here.
  // Pending before/after recompute for THIS property (set by a RED commit).
  const rc = (PENDING_RECOMPUTE && PENDING_RECOMPUTE.id === CURRENT_ID
              && PENDING_RECOMPUTE.supported) ? PENDING_RECOMPUTE : null;
  const afterSd = rc ? rc.after : sd;
  const zone = data.flood_zone ? ` &middot; ${data.flood_zone}` : "";

  let deltaHtml = "";
  if (rc) {
    const b = rc.before.property_spread_bps || 0, a = rc.after.property_spread_bps || 0;
    const d = a - b, sign = d > 0 ? "+" : "";
    const cls = d < 0 ? "wf-down" : (d > 0 ? "wf-up" : "");
    deltaHtml =
      `<div class="wf-delta">After editing <b>${prettyLabel(rc.field.split(".").pop())}</b> — ` +
      `property spread <b>${b.toFixed(1)}</b> → <b>${a.toFixed(1)}</b> bps ` +
      `<span class="${cls}">(${sign}${d.toFixed(1)} bps)</span>` +
      `<span class="wf-delta-note">instant recompute · storms & portfolio unchanged</span></div>`;
  }

  const sub = rc ? "Baseline (ghost) vs your edit — Gauge → Property (bps)"
                 : `Gauge spread decomposed to the property spread (bps)${zone}`;
  body.innerHTML =
    `<div class="wf-wrap">` +
      `<div class="wf-head"><div>` +
        `<div class="wf-title">PRS spread waterfall</div>` +
        `<div class="wf-sub">${sub}</div>` +
      `</div><button class="wf-pricer" id="wf-pricer">Open PRS Pricer ↗</button></div>` +
      deltaHtml +
      `<div class="wf-canvas-wrap"><canvas id="wf-canvas"></canvas></div>` +
      `<div class="wf-final">Property spread: ` +
        `<b>${(afterSd.property_spread_bps || 0).toFixed(1)} bps</b></div>` +
    `</div>`;
  window.phcData = rc
    ? { spread_decomposition: rc.after, before_decomposition: rc.before }
    : { spread_decomposition: sd };
  if (typeof _renderSpreadWaterfall === "function") {
    // Highlight the Property step (or BRI, when present) — the total spread.
    const active = (afterSd.bri_spread_bps !== undefined && afterSd.bri_spread_bps !== null) ? 4 : 3;
    _renderSpreadWaterfall("wf-canvas", active);
  } else {
    document.querySelector(".wf-canvas-wrap").innerHTML =
      `<div class="wf-msg">Waterfall renderer unavailable.</div>`;
  }
  $("#wf-pricer").addEventListener("click", openPrsPricer);
}

// Open the actual PRS pricer — the same action as the property-level map menu
// ("Physical Risk Swap"). When the tool runs embedded in the main app (the
// house-icon iframe), the parent window exposes that function.
function openPrsPricer() {
  const fn = ASSET === "commercial" ? "viewCommercialHazard" : "viewPropertyHazard";
  const host = (window.parent && window.parent !== window) ? window.parent : window;
  if (typeof host[fn] === "function") {
    host[fn](CURRENT_ID);
  } else {
    alert("Open this asset in the main app to use the PRS Pricer (" + fn + ").");
  }
}

// ---- Report tab — link to the asset's detailed PDF report -----------------

function renderReport(body) {
  $("#modal-foot").innerHTML = "<span>Detailed report</span>";
  const label = { Properties: "property", Commercials: "commercial",
                  Gauges: "gauge" }[assetLabel(ASSET)] || assetLabel(ASSET).toLowerCase();
  body.innerHTML =
    `<div class="rep-wrap">` +
      `<div class="rep-title">Detailed ${label} report</div>` +
      `<div class="rep-sub">Generates the full PDF report for <b>${CURRENT_ID}</b> ` +
        `— the same report as the main-app context menu.</div>` +
      `<button class="rep-open" id="rep-open">Generate &amp; open report ↗</button>` +
      `<div class="rep-note">Opens in the main app. Reports are produced there ` +
        `(this sandbox tool links to them rather than regenerating).</div>` +
    `</div>`;
  $("#rep-open").addEventListener("click", openReport);
}

// Trigger the main app's report generator for this asset. Embedded in the main
// app (house-icon iframe) the parent window exposes generateReport /
// generateGaugeReport / generateCommercialReport / generateRLoanReport /
// generateCLoanReport (see static/js/backend-handler.js).
function openReport() {
  const fn = REPORT_FNS[ASSET];
  const host = (window.parent && window.parent !== window) ? window.parent : window;
  if (fn && typeof host[fn] === "function") {
    host[fn](CURRENT_ID);
  } else {
    alert("Open this asset in the main app to generate its report (" + fn + ").");
  }
}

// ---- lineage: legend, 3-dots field menu, lineage popup --------------------

function lineageLegendHtml() {
  if (!LINEAGE) return "";
  const t = LINEAGE.tiers;
  const dot = (k) =>
    `<span class="lin-leg"><span class="lin-dot tier-dot-${k.toLowerCase()}"></span>${t[k].label}</span>`;
  return `<span class="lin-legend">${dot("RED")}${dot("AMBER")}${dot("GREEN")}</span>`;
}

function closeFieldMenu() {
  const m = document.getElementById("field-menu");
  if (m) m.remove();
}

function openFieldMenu(anchor, fieldPath, fieldLabel, value) {
  closeFieldMenu();
  const menu = document.createElement("div");
  menu.className = "field-menu";
  menu.id = "field-menu";

  const spec = EDIT_SPECS[ASSET] && EDIT_SPECS[ASSET][fieldPath];
  if (spec) {
    const amendBtn = document.createElement("button");
    amendBtn.className = "field-menu-item";
    amendBtn.textContent = "Amend";
    amendBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      closeFieldMenu();
      openAmendPopup(fieldPath, fieldLabel, value, spec);
    });
    menu.appendChild(amendBtn);
  }

  const lineageBtn = document.createElement("button");
  lineageBtn.className = "field-menu-item";
  lineageBtn.textContent = "Data lineage";
  lineageBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    closeFieldMenu();
    openLineagePopup(fieldPath, fieldLabel);
  });
  menu.appendChild(lineageBtn);
  const more = document.createElement("div");
  more.className = "field-menu-more";
  more.textContent = "more to come…";
  menu.appendChild(more);
  document.body.appendChild(menu);
  const r = anchor.getBoundingClientRect();
  menu.style.top = (r.bottom + 4) + "px";
  menu.style.left = Math.min(r.left, window.innerWidth - 170) + "px";
  setTimeout(() => document.addEventListener("click", closeFieldMenu, { once: true }), 0);
}

function openLineagePopup(fieldPath, fieldLabel) {
  const e = lineageFor(fieldPath) || {};
  const tier = e.tier || "GREEN";
  const meta = (LINEAGE && LINEAGE.tiers[tier]) || {};
  const chain = (e.chain || []).map((n) =>
    `<div class="lin-node lin-${n.kind}">${n.node}` +
    (n.ref ? `<div class="lin-ref">${n.ref}</div>` : "") + `</div>`
  ).join('<div class="lin-arrow">↓</div>');
  const consumers = (e.consumers || [])
    .map((c) => `<span class="lin-consumer">${c}</span>`).join("");

  const overlay = document.createElement("div");
  overlay.className = "lin-overlay";
  overlay.id = "lin-overlay";
  overlay.innerHTML =
    `<div class="lin-popup">` +
      `<div class="lin-head"><div class="lin-head-main">` +
        `<div class="lin-title">${fieldLabel}</div>` +
        `<div class="lin-path">${fieldPath}</div></div>` +
        `<button class="icon-btn close" id="lin-close">&times;</button></div>` +
      `<div class="lin-body">` +
        `<span class="lin-tier tier-pill-${tier.toLowerCase()}">${meta.label || tier}</span>` +
        `<div class="lin-summary">${e.summary || ""}</div>` +
        `<div class="lin-section-title">Downstream lineage</div>` +
        `<div class="lin-chain">${chain}</div>` +
        (consumers
          ? `<div class="lin-section-title">Consumers</div><div class="lin-consumers">${consumers}</div>`
          : "") +
      `</div>` +
    `</div>`;
  document.body.appendChild(overlay);
  overlay.addEventListener("click", (ev) => { if (ev.target.id === "lin-overlay") overlay.remove(); });
  document.getElementById("lin-close").addEventListener("click", () => overlay.remove());
}

// ---- amend a field via the 3-dots menu (commit to sandbox + audit) --------

async function ensureEditSpec(asset) {
  if (EDIT_SPECS[asset]) return;
  try { EDIT_SPECS[asset] = await (await fetch(`/api/${asset}/edit-spec`)).json(); }
  catch (_) { EDIT_SPECS[asset] = {}; }
}

// ---- add a new record (zero-portfolio / add) ------------------------------
// Curated core fields shown on the add form, per creatable asset. The rest of
// the CDM is filled later via the normal field editor. Paths must exist in the
// schema (validated); the id + catchment are minted server-side.
const CREATE_FIELDS = {
  property: [
    ["PropertyHeader.Location.BuildingNumber", "Building number"],
    ["PropertyHeader.Location.StreetName", "Street"],
    ["PropertyHeader.Location.TownCity", "Town / city"],
    ["PropertyHeader.Location.Postcode", "Postcode"],
    ["PropertyHeader.Header.propertyType", "Property type"],
    ["PropertyHeader.Valuation.PropertyValue", "Value (£)"],
    ["PropertyHeader.Location.LatitudeDegrees", "Latitude"],
    ["PropertyHeader.Location.LongitudeDegrees", "Longitude"],
    ["PropertyHeader.Construction.FloorLevelMeters", "Floor level (m)"],
    ["PropertyHeader.RiskAssessment.GroundLevelMeters", "Ground level (m)"],
  ],
  commercial: [
    ["CommercialAsset.Location.BuildingNumber", "Building number"],
    ["CommercialAsset.Location.StreetName", "Street"],
    ["CommercialAsset.Location.TownCity", "Town / city"],
    ["CommercialAsset.Location.Postcode", "Postcode"],
    ["CommercialAsset.CommercialAttributes.CommercialType", "Commercial type"],
    ["CommercialAsset.Valuation.PropertyValue", "Value (£)"],
    ["CommercialAsset.Location.LatitudeDegrees", "Latitude"],
    ["CommercialAsset.Location.LongitudeDegrees", "Longitude"],
    ["CommercialAsset.Construction.FloorLevelMeters", "Floor level (m)"],
    ["CommercialAsset.RiskAssessment.GroundLevelMeters", "Ground level (m)"],
  ],
};

async function openCreateForm() {
  const fields = CREATE_FIELDS[ASSET];
  if (!fields) return;
  await ensureEditSpec(ASSET);
  const noun = ASSET === "commercial" ? "commercial asset" : "property";
  const overlay = document.createElement("div");
  overlay.className = "lin-overlay";
  overlay.id = "create-overlay";
  overlay.innerHTML =
    `<div class="lin-popup create-popup">` +
      `<div class="lin-head"><div class="lin-head-main">` +
        `<div class="lin-title">Add ${noun}</div>` +
        `<div class="lin-path">New record → sandbox · id &amp; catchment minted on save</div></div>` +
        `<button class="icon-btn close" id="create-close">&times;</button></div>` +
      `<div class="lin-body">` +
        `<div id="create-grid" class="create-grid"></div>` +
        `<div class="amend-err" id="create-err"></div>` +
        `<div class="amend-actions">` +
          `<button class="cancel-btn" id="create-cancel">Cancel</button>` +
          `<button class="save-btn" id="create-save">Create record</button>` +
        `</div>` +
      `</div>` +
    `</div>`;
  document.body.appendChild(overlay);

  const grid = document.getElementById("create-grid");
  const inputs = {};
  for (const [path, label] of fields) {
    const spec = (EDIT_SPECS[ASSET] && EDIT_SPECS[ASSET][path]) || { input: "text" };
    const row = document.createElement("label");
    row.className = "create-row";
    const lab = document.createElement("span");
    lab.className = "create-lab";
    lab.textContent = label;
    const input = makeFieldInput("", spec);
    row.appendChild(lab);
    row.appendChild(input);
    grid.appendChild(row);
    inputs[path] = { input, spec };
  }

  const close = () => overlay.remove();
  overlay.addEventListener("click", (ev) => { if (ev.target.id === "create-overlay") close(); });
  document.getElementById("create-close").addEventListener("click", close);
  document.getElementById("create-cancel").addEventListener("click", close);
  document.getElementById("create-save").addEventListener("click", () => submitCreate(inputs, close));
}

async function submitCreate(inputs, close) {
  const errEl = document.getElementById("create-err");
  errEl.textContent = "";
  const changes = {};
  for (const [path, { input, spec }] of Object.entries(inputs)) {
    const v = spec.input === "checkbox" ? input.checked : input.value;
    if (v !== "" && v !== null && v !== undefined) changes[path] = v;
  }
  try {
    const res = await fetch(`/api/${ASSET}/items`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ changes }),
    });
    const data = await res.json();
    if (res.ok && data.status === "success") {
      close();
      await reloadItems();
      openDetail(data.id);
    } else {
      errEl.textContent = data.error ||
        (data.errors && Object.values(data.errors)[0]) || "Create failed";
    }
  } catch (err) {
    errEl.textContent = "Create failed: " + err.message;
  }
}

async function reloadItems() {
  try {
    ITEMS = await (await fetch(`/api/${ASSET}/items`)).json();
    renderList($("#search").value);
    renderSummary();
  } catch (_) { /* leave the list as-is */ }
}

function openAmendPopup(fieldPath, fieldLabel, value, spec) {
  const overlay = document.createElement("div");
  overlay.className = "lin-overlay";
  overlay.id = "amend-overlay";
  overlay.innerHTML =
    `<div class="lin-popup amend-popup">` +
      `<div class="lin-head"><div class="lin-head-main">` +
        `<div class="lin-title">Amend ${fieldLabel}</div>` +
        `<div class="lin-path">${fieldPath}</div></div>` +
        `<button class="icon-btn close" id="amend-close">&times;</button></div>` +
      `<div class="lin-body">` +
        `<div class="amend-old">Current: <b>${formatValue(value)}</b></div>` +
        `<div id="amend-input-wrap"></div>` +
        `<div class="amend-err" id="amend-err"></div>` +
        `<div class="amend-actions">` +
          `<button class="cancel-btn" id="amend-cancel">Cancel</button>` +
          `<button class="save-btn" id="amend-save">Commit change</button>` +
        `</div>` +
      `</div>` +
    `</div>`;
  document.body.appendChild(overlay);

  const input = makeFieldInput(value, spec);
  document.getElementById("amend-input-wrap").appendChild(input);
  input.focus();

  const close = () => overlay.remove();
  overlay.addEventListener("click", (ev) => { if (ev.target.id === "amend-overlay") close(); });
  document.getElementById("amend-close").addEventListener("click", close);
  document.getElementById("amend-cancel").addEventListener("click", close);
  document.getElementById("amend-save").addEventListener("click", () =>
    commitAmend(fieldPath, spec, input, close));
}

async function commitAmend(fieldPath, spec, input, close) {
  const newVal = spec.input === "checkbox" ? input.checked : input.value;
  const errEl = document.getElementById("amend-err");
  errEl.textContent = "";
  input.classList.remove("input-error");
  try {
    const res = await fetch(`/api/${ASSET}/items/${encodeURIComponent(CURRENT_ID)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ changes: { [fieldPath]: newVal } }),
    });
    const data = await res.json();
    if (res.ok && data.status === "success") {
      CURRENT = data.record;
      close();
      await reloadItems();
      // RED edit → instant before/after on the PRS Waterfall. Unsupported RED
      // edits (gauge thresholds / ground level) report a "needs full re-run" note.
      if (data.recompute && data.recompute.supported) {
        PENDING_RECOMPUTE = Object.assign({ id: CURRENT_ID }, data.recompute);
        ACTIVE_SECTION = WATERFALL_KEY;
      } else if (data.recompute) {
        PENDING_RECOMPUTE = null;
        setStatus(data.recompute.reason || "Recompute not available for this edit.");
      }
      renderDetailCard();
      renderDetailTabs();
      renderDetailBody();
    } else {
      const msg = (data.errors && data.errors[fieldPath]) || data.error || "Invalid value";
      errEl.textContent = msg;
      input.classList.add("input-error");
    }
  } catch (err) {
    errEl.textContent = "Save failed: " + err.message;
  }
}

async function openDetail(rid) {
  setStatus("Loading " + rid + "…");
  try {
    const res = await fetch(`/api/${ASSET}/items/${encodeURIComponent(rid)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    CURRENT = await res.json();
    CURRENT_ID = rid;
    PENDING_RECOMPUTE = null;  // don't leak a recompute across properties
    ACTIVE_SECTION = recordSections()[0];
    ACTIVE_PERIL = "flood";
    CURRENT_PERILS = null;
    await ensureEditSpec(ASSET);  // so the field menu can offer "Amend"
    const singular = { Properties: "Property", Commercials: "Commercial",
                       Gauges: "Gauge" }[assetLabel(ASSET)] || assetLabel(ASSET);
    $("#modal-title").textContent = singular + " Detail";
    renderList($("#search").value);
    renderDetailCard();
    renderDetailTabs();
    renderDetailBody();
    $("#modal-overlay").classList.remove("hidden");
    setStatus("");
    loadPerils();
  } catch (err) {
    setStatus("Error: " + err.message, true);
  }
}

function closeModal() { $("#modal-overlay").classList.add("hidden"); }

function toggleExpand() {
  const m = $("#modal");
  const expanded = m.classList.toggle("expanded");
  const btn = $("#modal-expand");
  btn.innerHTML = expanded ? "&#x2750;" : "&#x26F6;";
  btn.title = expanded ? "Restore" : "Expand";
}

function setStatus(msg, isError = false) {
  const el = $("#status");
  el.textContent = msg;
  el.classList.toggle("error", isError);
}

// ---- asset switching -------------------------------------------------------

async function selectAsset(key) {
  ASSET = key;
  CURRENT_ID = null;
  closeModal();
  renderAssetTabs();
  const isAudit = key === AUDIT_KEY;
  $(".content").classList.toggle("audit-view", isAudit);   // light-blue panel
  $(".hint").classList.toggle("hidden", isAudit);
  // The "+ Add" control is only shown for creatable assets (property/commercial).
  $("#add-record").classList.toggle("hidden", isAudit || !CREATE_FIELDS[key]);
  if (!isAudit && CREATE_FIELDS[key]) ensureEditSpec(key);
  if (isAudit) { await renderAudit(); return; }

  const label = assetLabel(key);
  $("#sidebar-title").textContent = label;
  $("#content-title").textContent = label + " Portfolio";
  $("#content-sub").textContent =
    "Common Domain Model — sandbox copy. Select a record's review icon to inspect its full CDM record.";
  $("#search").value = "";
  setStatus("Loading " + label + "…");
  try {
    const [schemaRes, itemsRes] = await Promise.all([
      fetch(`/api/${key}/schema`),
      fetch(`/api/${key}/items`),
    ]);
    SCHEMA = await schemaRes.json();
    ITEMS = await itemsRes.json();
    renderList();
    renderSummary();
    setStatus("");
  } catch (err) {
    setStatus("Failed to load " + label + ": " + err.message, true);
  }
}

// ---- audit trail view ------------------------------------------------------

async function renderAudit() {
  $("#sidebar-title").textContent = "Audit";
  $("#item-list").innerHTML = "";
  $("#content-title").textContent = "Audit Trail";
  $("#content-sub").textContent =
    "Field amendments committed to the sandbox (newest first).";
  const cards = $("#cards");
  cards.innerHTML = '<div class="audit-msg">Loading…</div>';
  let entries = [];
  try { entries = await (await fetch("/api/audit")).json(); } catch (_) { entries = []; }
  $("#count").textContent = `${entries.length} amendment${entries.length === 1 ? "" : "s"}`;
  if (!entries.length) {
    cards.innerHTML = '<div class="audit-msg">No amendments yet. Use a field’s '
      + '⋮ menu → Amend to make one.</div>';
    return;
  }
  const rows = entries.map((e) =>
    `<tr>` +
      `<td class="au-when">${(e.timestamp || "").replace("T", " ")}</td>` +
      `<td><span class="au-badge">${e.asset_label || e.asset}</span></td>` +
      `<td class="au-rec">${e.record_id}</td>` +
      `<td class="au-field" title="${e.field}">${prettyLabel(e.field_label || "")}</td>` +
      `<td class="au-change"><span class="au-old">${formatValue(e.old)}</span>` +
        `<span class="au-arrow">→</span>` +
        `<span class="au-new">${formatValue(e.new)}</span></td>` +
      `<td>${e.user || ""}</td>` +
    `</tr>`).join("");
  // Same layout as the regulatory-workflow audit trail: a "Showing X of Y" bar
  // above a flat table (Timestamp · Asset · Record · Field · Change · User).
  cards.innerHTML =
    `<div class="audit-pane">` +
      `<div class="audit-showing">Showing <b>${entries.length}</b> of ` +
        `<b>${entries.length}</b> entries</div>` +
      `<table class="audit-table"><thead><tr>` +
        `<th>Timestamp</th><th>Asset</th><th>Record</th><th>Field</th>` +
        `<th>Change</th><th>User</th>` +
      `</tr></thead><tbody>${rows}</tbody></table>` +
    `</div>`;
}

// ---- boot ------------------------------------------------------------------

async function boot() {
  setStatus("Loading…");
  try {
    ASSETS = await (await fetch("/api/assets")).json();
    ASSETS.push({ key: AUDIT_KEY, label: "Audit" });  // special non-asset tab
    try { LINEAGE = await (await fetch("/api/lineage")).json(); } catch (_) { LINEAGE = null; }
    $("#search").addEventListener("input", (e) => renderList(e.target.value));
    $("#add-record").addEventListener("click", openCreateForm);
    $("#modal-close").addEventListener("click", closeModal);
    $("#modal-expand").addEventListener("click", toggleExpand);
    $("#modal-overlay").addEventListener("click", (e) => {
      if (e.target.id === "modal-overlay") closeModal();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeModal();
    });
    // Default to Properties if present, else the first asset.
    const def = ASSETS.find((a) => a.key === "property") || ASSETS[0];
    if (def) await selectAsset(def.key);
  } catch (err) {
    setStatus("Failed to load: " + err.message, true);
  }
}

boot();
