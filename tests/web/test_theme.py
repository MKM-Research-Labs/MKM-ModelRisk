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
"""Tests for the design tokens and the stylesheet they are served as.

The load-bearing claim is the last test: every ``var(--…)`` the front end reads
resolves to a token that exists. A missing token is not an error anywhere — the
browser silently drops the declaration — so a rename would otherwise reach a screen
as a colour quietly falling back to black.
"""
from __future__ import annotations

import re

from audit.styling import colour_literal_findings
from config.paths import STATIC_DIR, TEMPLATES_DIR
from config.theme import (LEVEL_COLOURS, MISSION_CRITICALITY_COLOURS, RAG,
                          RISK_RATING_COLOURS, STATUS_COLOUR_DEFAULTS,
                          STATUS_COLOUR_TOKENS, THEME, THEME_GROUPS, UNRATED_COLOUR)
from src.governance.risk_policy._defaults import default_policy
from src.web._theme import theme_css, theme_version

_VAR_REFERENCE = re.compile(r"var\(\s*--([a-zA-Z0-9_-]+)")
_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_HEX_COLOUR = re.compile(r"#[0-9a-fA-F]{3,8}\b")
_FRONT_END = (STATIC_DIR, TEMPLATES_DIR)


def _referenced_tokens() -> dict[str, set[str]]:
    """Every ``--token`` the stylesheet, the JavaScript or the template reads."""
    found: dict[str, set[str]] = {}
    for root in _FRONT_END:
        for path in sorted(root.rglob("*")):
            if path.suffix not in (".css", ".js", ".html"):
                continue
            for match in _VAR_REFERENCE.finditer(path.read_text(encoding="utf-8")):
                found.setdefault(match.group(1), set()).add(str(path))
    return found


def test_token_names_are_unique_across_the_groups():
    # The groups organise config/theme.py; they do not namespace it, so a name
    # reused in two groups would have one silently win.
    declared = sum(len(group) for _, group in THEME_GROUPS)
    assert declared == len(THEME)


def test_every_token_has_a_non_empty_string_value():
    # Values go straight into CSS, so a stray None or int would emit a broken
    # declaration rather than raise.
    assert all(isinstance(value, str) and value.strip() for value in THEME.values())


def test_theme_css_is_a_single_root_block():
    css = theme_css()
    assert css.startswith(":root {\n")
    assert css.rstrip().endswith("}")
    # A serialiser, not a stylesheet: no rules of its own (rule R7).
    assert css.count("{") == 1


def test_theme_css_declares_every_token():
    css = theme_css()
    for name, value in THEME.items():
        assert f"  --{name}: {value};" in css


def test_theme_css_carries_the_accent_the_console_was_built_around():
    assert "--accent: #1976d2;" in theme_css()


def test_theme_version_is_stable_for_unchanged_tokens():
    assert theme_version() == theme_version()


def test_theme_version_moves_when_a_token_changes():
    # The whole point of the stamp: a rebrand must not be masked by a browser cache.
    rebranded = dict(THEME, accent="#7e57c2")
    assert theme_version(rebranded) != theme_version()


def test_theme_route_serves_the_tokens_as_css(client):
    response = client.get("/theme.css")
    assert response.status_code == 200
    assert response.mimetype == "text/css"
    assert b"--accent: #1976d2;" in response.data


def test_index_links_the_tokens_before_the_stylesheet(client):
    # Ordering is load-bearing: app.css resolves its var(--…) against this block,
    # so a link placed after it would leave the first paint unstyled.
    html = client.get("/").get_data(as_text=True)
    assert "/theme.css?v=" in html
    assert html.index("/theme.css") < html.index("css/app.css")


def test_index_stamps_the_theme_link_with_its_own_version(client):
    html = client.get("/").get_data(as_text=True)
    assert f"/theme.css?v={theme_version()}" in html


def test_the_stylesheet_no_longer_declares_its_own_root_block():
    # One source of truth: a :root here would shadow the served tokens. Comments are
    # stripped first — the file's own header warns against reintroducing one, and
    # naming the thing it forbids must not read as doing it.
    stylesheet = (STATIC_DIR / "css" / "app.css").read_text(encoding="utf-8")
    assert ":root" not in _COMMENT.sub("", stylesheet)


def test_every_referenced_token_is_defined():
    unresolved = {name: sorted(where) for name, where in _referenced_tokens().items()
                  if name not in THEME}
    assert not unresolved, f"undefined design tokens referenced: {unresolved}"


def test_the_seed_colours_are_not_emitted_as_custom_properties():
    # They are seed data for the policy store, not tokens the stylesheet resolves
    # against. Emitting them would put a --Red into :root that nothing ever reads.
    assert "Red" not in THEME
    assert "--Red" not in theme_css()


def test_the_seeded_policy_takes_every_colour_from_the_theme():
    values = set(THEME.values())
    policy = default_policy()
    coloured = [band for dimension in policy["dimensions"].values()
                for band in dimension["bands"]] + policy["risk_ratings"]
    assert coloured, "the seed policy declares no bands at all"
    assert all(band["colour"] in values for band in coloured)


def test_the_softer_ramp_is_the_one_the_seeded_level_bands_use():
    # Materiality and Complexity feed the rating rather than being it, so they carry
    # the lighter ramp. If these ever collapse onto the main RAG hues, the heatmap
    # axes stop being distinguishable from the ratings they produce.
    assert LEVEL_COLOURS == {"Low": RAG["green-soft"], "Medium": RAG["amber-soft"],
                             "High": RAG["red-soft"]}
    assert set(LEVEL_COLOURS.values()).isdisjoint(set(RISK_RATING_COLOURS.values()))


def test_mission_criticality_seeds_map_to_named_tokens():
    assert set(MISSION_CRITICALITY_COLOURS.values()) <= set(THEME.values())
    assert UNRATED_COLOUR == RAG["grey"]


def test_no_python_source_declares_a_colour_of_its_own():
    # Delegates to the R10 gate rather than re-implementing the scan: that one strips
    # comments (naming a colour while explaining the rule is not breaking it) and sees
    # colours spelled without a "#", which is how LaTeX writes them. A second, weaker
    # copy here would pass while the real gate failed, or the reverse.
    assert colour_literal_findings() == []


def test_every_status_maps_to_a_token_that_exists():
    # These name tokens, not colours, so a typo would render nothing at all rather than
    # the wrong colour — silent, and only on the one status nobody clicked.
    unknown = {(domain, value, token)
               for domain, mapping in STATUS_COLOUR_TOKENS.items()
               for value, token in mapping.items() if token not in THEME}
    assert not unknown
    assert all(token in THEME for token in STATUS_COLOUR_DEFAULTS.values())


def test_the_domains_without_a_default_are_the_ones_that_must_show_a_dash():
    # An unknown rating or an unrated tier renders as a dash. Giving these a default
    # would paint a grey badge asserting a classification nobody made.
    # ``change_class`` takes a default because an unrecognised tier is still a
    # classification somebody recorded — the log holds it — and the honest rendering is
    # the word itself, uncoloured. That is the ``validation_question`` case, not the
    # unrated-tier case.
    assert set(STATUS_COLOUR_DEFAULTS) == {"validation_question", "mrc_state", "lifecycle",
                                           "product_status", "change_class"}
    assert {"rag", "mission_criticality", "meeting_status",
            "review_thread"}.isdisjoint(STATUS_COLOUR_DEFAULTS)


def test_theme_api_serves_tokens_and_the_status_mapping(client):
    payload = client.get("/api/theme").get_json()
    assert payload["tokens"]["accent"] == THEME["accent"]
    assert payload["status_colours"]["rag"]["Green"] == "green"
    assert payload["status_defaults"]["lifecycle"] == "grey"


def test_the_status_mapping_covers_every_value_the_console_had_a_colour_for():
    # The maps the JavaScript used to carry, by their entry counts — six found in
    # helpers.js at step 3, and two more (Product status, review threads) found in
    # product.js and inventory/review.js at step 5. A value dropped in translation
    # would render as a dash on a screen that used to colour it.
    #
    # "attention" was not translated from anything: the dashboard's four response
    # states were configured here from the start, so no screen can have lost a value
    # from it. It is counted all the same, so that dropping one later still fails.
    assert {domain: len(mapping) for domain, mapping in STATUS_COLOUR_TOKENS.items()} == {
        "rag": 3, "mission_criticality": 5, "meeting_status": 4,
        "validation_question": 4, "mrc_state": 7, "lifecycle": 4,
        "product_status": 4, "review_thread": 2, "attention": 4,
        # Configured here from the start, like "attention" — the four change tiers
        # never lived as a colour map in the JavaScript.
        "change_class": 4,
    }


def test_the_javascript_names_no_colour_of_its_own():
    # helpers.js and inventory/list.js are fully converted; the rest of the front end
    # is step 5 (docs/design/theme_config.md §5), so this is scoped to the files the
    # colour maps reached rather than asserting a clean tree it has not reached yet.
    converted = ["js/helpers.js", "js/inventory/list.js", "js/main.js"]
    offenders = {name: _HEX_COLOUR.findall((STATIC_DIR / name).read_text(encoding="utf-8"))
                 for name in converted}
    assert not any(offenders.values()), f"colour literals remain: {offenders}"


def test_the_type_spacing_and_radius_scales_are_all_consumed():
    # A scale nobody refers to is a scale that has quietly stopped being true. Every
    # rung exists because the console reaches for it; if one falls out of use, either
    # the markup regressed to a literal or the rung should go.
    referenced = set(_referenced_tokens())
    scale = {name for name in THEME
             if name.startswith(("size-", "space-", "radius-"))}
    assert scale, "the scales vanished from the theme"
    assert not scale - referenced, f"scale tokens nothing uses: {sorted(scale - referenced)}"


def test_the_typeface_is_a_token_not_a_literal():
    # The face an adopter changes first. A literal stack in app.css would mean the
    # rebrand stops at the colours.
    stylesheet = (STATIC_DIR / "css" / "app.css").read_text(encoding="utf-8")
    assert "var(--font)" in stylesheet and "var(--font-mono)" in stylesheet
    assert "Arial" not in stylesheet


def test_the_generated_documents_take_their_colours_from_the_theme():
    # The PDFs were the last surface with a palette of its own — a second brand blue
    # plus LaTeX's built-in gray and red. A report and the screen it came from can no
    # longer disagree.
    from config.reporting import (DOCUMENT_CHROME_COLOUR, DOCUMENT_CLASSIFICATION_COLOUR,
                                  DOCUMENT_LINK_COLOUR)
    from src.governance.latex import preamble
    assert DOCUMENT_LINK_COLOUR == THEME["accent"]
    assert DOCUMENT_CHROME_COLOUR == THEME["muted"]
    assert DOCUMENT_CLASSIFICATION_COLOUR == THEME["red"]
    tex = preamble("A Report", org_name="Acme")
    assert "\\definecolor{brand}{HTML}{1976D2}" in tex
    assert "mkmblue" not in tex and "textcolor{gray}" not in tex


def test_the_page_setup_is_configuration_not_source():
    from config.reporting import DOCUMENT_GEOMETRY, DOCUMENT_RULE_WIDTH
    from src.governance.latex import preamble
    tex = preamble("A Report")
    assert DOCUMENT_GEOMETRY in tex
    assert "{" + DOCUMENT_RULE_WIDTH + "}" in tex


def test_the_body_typeface_is_a_choice_the_adopter_makes():
    # Empty ships today's Computer Modern; "sans" matches the console's Arial. The
    # parameter exists so the switch is deliberate rather than a side effect.
    from src.governance.latex_style import BODY_FONT_PACKAGES
    assert "sans" in BODY_FONT_PACKAGES
    assert "helvet" in BODY_FONT_PACKAGES["sans"]


def test_an_unusable_colour_falls_back_to_the_theme_not_a_literal():
    from src.governance.latex_style import latex_hex
    assert latex_hex(None) == THEME["grey"].lstrip("#").upper()
    assert latex_hex("#1976d2") == "1976D2"


def test_the_title_page_builds_and_carries_the_theme_colours():
    # Regression: the first cut of this change left "author_line + + coloured(...)" and
    # every generated PDF raised TypeError. The preamble tests passed throughout,
    # because none of them built a title page.
    from src.governance.latex import title_page
    page = title_page("A Report", "A subtitle", org_name="Acme", date="2026-08-22",
                      author="System")
    assert page.startswith("\\begin{titlepage}")
    assert page.rstrip().endswith("\\end{titlepage}")
    assert "textcolor[HTML]{" + THEME["red"].lstrip("#").upper() + "}" in page
    assert "textcolor{red}" not in page and "textcolor{gray}" not in page
