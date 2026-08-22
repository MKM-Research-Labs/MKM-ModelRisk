# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Visual design tokens — the console's whole look and feel (coding rule R1).

Every colour, type size, spacing step, corner radius and shadow the console draws
with is named here and nowhere else. `src/web/_theme.py` serialises this into the
``:root`` custom-property block served at ``/theme.css``, which is linked ahead of
``app.css``; the stylesheet and the JavaScript then refer to tokens rather than to
values. An adopting institution rebrands by changing this file (later: by shipping a
theme file — see docs/design/theme_config.md §4.3), not by editing the front end.

Keys are the CSS custom-property name without the leading ``--``, so a token is
spelled the same way here, in the stylesheet and in an adopter's override. There is
no translation layer to drift.

Values are strings, deliberately: a token is whatever CSS accepts in that position —
a hex colour, a length, a font stack, a whole ``box-shadow``. Nothing here is
arithmetic, so nothing here needs to be a number.
"""
from __future__ import annotations

# --- The adopter's identity: the one group a rebrand almost always touches. -------
# ``accent`` is the interactive colour — links, active tabs, focus borders, the
# selected state of anything. ``header-*`` is the banner gradient carried by the
# topbar and every detail header.
BRAND = {
    "accent": "#1976d2",
    "accent-soft": "#e3f2fd",
    "accent-border": "#bbdefb",
    "accent-ink": "#0d47a1",
    "accent-wash": "#f7fbff",
    "header-from": "#f5f7fa",
    "header-to": "#c3cfe2",
    "header-ink": "#2a3a4d",
    "header-sub": "#5b6b7d",
}

# --- Paper and ink: the neutral scale everything else sits on. --------------------
SURFACE = {
    "bg": "#eef1f5",
    "panel": "#ffffff",
    "raised": "#fafafa",
    "sunken": "#f5f5f5",
    "control": "#f9f9f9",
    "readonly": "#f4f5f7",
    "code": "#f0f0f0",
    "line": "#e0e0e0",
    "line-soft": "#eeeeee",
    # A hairline over an unknown background (the date strip under a detail header),
    # so it darkens whatever it crosses instead of assuming the panel colour.
    "rule": "rgba(0, 0, 0, 0.12)",
}

TEXT = {
    "text": "#333333",
    "text-2": "#555555",
    "muted": "#888888",
    "inverse": "#ffffff",
}

# --- Red / Amber / Green is this product's own vocabulary, not a colour choice. ---
# ``VALID_RAG_RATINGS`` names these ratings, the risk policy lets a division recolour
# them per policy, and these are the platform fallbacks used until it loads. They are
# therefore named for the rating, not for a semantic role.
RAG = {
    "green": "#388e3c",
    "amber": "#f57c00",
    "red": "#d32f2f",
    "grey": "#9e9e9e",
    # A lighter ramp of the same three hues. The seeded Materiality and Complexity
    # bands use it so a dimension's low-to-high scale reads as related to the overall
    # rating without competing with it — those bands are an input to the rating, not
    # the rating itself.
    "green-soft": "#66bb6a",
    "amber-soft": "#ffa726",
    "red-soft": "#ef5350",
}

# --- Banner and chip tints, keyed to the state they announce. ---------------------
# Two warn tints and two danger lines are carried on purpose: they are what the
# console renders today, and collapsing them is a visual change, not a refactor.
# See docs/design/theme_config.md §5 step 4.
STATE = {
    "danger-bg": "#fdecea",
    "danger-ink": "#b71c1c",
    "danger-line": "#f5c6c2",
    "danger-line-soft": "#f1c5c2",
    "warn-bg": "#fff8e1",
    "warn-bg-alt": "#fef3c7",
    "warn-ink": "#92400e",
    "warn-line": "#d97706",
}

# --- The graph canvases (model chain, neighbourhood, product component map). ------
# A second and third hue the rest of the console never uses: indigo marks a staged
# or proposed thing, teal a terminal node, slate the edges between them.
GRAPH = {
    "indigo": "#6366f1",
    "indigo-ink": "#4338ca",
    "indigo-bg": "#eef2ff",
    "indigo-wash": "#f5f6ff",
    "teal": "#00897b",
    "teal-bg": "#e0f2f1",
    "slate": "#94a3b8",
    "node-ink": "#1f2937",
    "node-sub": "#4b5563",
    "tray-bg": "#fbfcfe",
    "toast-bg": "#323232",
}

# --- Type. ``family`` is the whole stack, so an adopter's face and its fallbacks ---
# arrive together. Sizes are a scale, not a set of one-offs: the console currently
# spells 11px and 12px 132 times between them.
TYPE = {
    "font": "Arial, Helvetica, sans-serif",
    "font-mono": "ui-monospace, Menlo, monospace",
    "line-height": "1.5",
    "size-xxs": "10px",
    "size-xs": "11px",
    "size-sm": "12px",
    "size-md": "13px",
    "size-lg": "16px",
    "size-xl": "20px",
}

SPACE = {
    "space-1": "4px",
    "space-2": "6px",
    "space-3": "8px",
    "space-4": "12px",
    "space-5": "16px",
    "space-6": "24px",
}

RADIUS = {
    "radius-sm": "3px",
    "radius-md": "6px",
    "radius-lg": "8px",
    "radius-xl": "10px",
    "radius-pill": "12px",
}

# Whole ``box-shadow`` values rather than just their colours, so an adopter with a
# flatter house style sets them to ``none`` and the elevation goes away everywhere.
SHADOW = {
    "shadow-card": "0 1px 3px rgba(0, 0, 0, 0.04)",
    "shadow-card-hover": "0 1px 4px rgba(0, 0, 0, 0.12)",
    "shadow-modal": "0 8px 32px rgba(0, 0, 0, 0.3)",
    "shadow-toast": "0 4px 16px rgba(0, 0, 0, 0.25)",
    "shadow-ghost": "0 2px 8px rgba(0, 0, 0, 0.18)",
    "scrim": "rgba(0, 0, 0, 0.45)",
}

# --- Seed colours for the risk policy --------------------------------------------
# The policy an institution starts with before an admin edits anything, assembled in
# src/governance/risk_policy/_defaults.py and reaching the console through
# /api/risk-policy. A division can recolour its own bands from Admin; these are what
# it inherits until it does, and they are the same visual decision as everything
# above — so they are named here rather than in the module that assembles the seed.
#
# Deliberately NOT emitted as custom properties: they are seed data for the policy
# store, not tokens the stylesheet resolves against, so they are absent from
# THEME_GROUPS below.
RISK_RATING_COLOURS = {"Red": RAG["red"], "Amber": RAG["amber"], "Green": RAG["green"]}

# Keyed by the legacy tier integer, which is the band's score.
MISSION_CRITICALITY_COLOURS = {1: RAG["red"], 2: RAG["amber"], 3: BRAND["accent"]}

LEVEL_COLOURS = {"Low": RAG["green-soft"], "Medium": RAG["amber-soft"],
                 "High": RAG["red-soft"]}

# What a band nobody has coloured falls back to — an absence, not a rating.
UNRATED_COLOUR = RAG["grey"]

# The groups in the order they are emitted, so the served stylesheet reads in the
# same order as this file and a diff of either is legible.
THEME_GROUPS = (
    ("brand", BRAND),
    ("surface", SURFACE),
    ("text", TEXT),
    ("rag", RAG),
    ("state", STATE),
    ("graph", GRAPH),
    ("type", TYPE),
    ("space", SPACE),
    ("radius", RADIUS),
    ("shadow", SHADOW),
)

# Every token, flat, keyed by custom-property name. Token names are unique across
# the groups — the groups organise this file, they do not namespace it — and
# tests/web/test_theme.py holds that true.
THEME = {name: value for _, group in THEME_GROUPS for name, value in group.items()}
