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
"""Shipped defaults for generated documents, overridden by the adopting institution.

Every PDF the platform generates goes through the shared LaTeX house style. The
classification banner, the author line and the legal notice below are one
institution's words rather than platform constants, so they are settings: an
adopter records its own in **Admin > Misc**, which re-labels every document at
once. The values here are what a fresh install prints until it does — the wording
that ships, not the wording that is fixed.
"""

from config.theme import BRAND, RAG, SURFACE, TEXT

# --- How a generated document looks (coding rule R10) -----------------------------
# The PDFs are the most externally visible thing the platform produces — a committee
# and, at one adopter, a regulator read them — and until now they carried their own
# colours: a second brand blue (#1565C0 against the console's #1976d2), plus LaTeX's
# built-in ``gray`` and ``red``. They draw from the same tokens the console does now,
# so a report and the screen it came from cannot disagree.
DOCUMENT_LINK_COLOUR = BRAND["accent"]
DOCUMENT_CHROME_COLOUR = TEXT["muted"]
DOCUMENT_CLASSIFICATION_COLOUR = RAG["red"]

# What a band with no colour of its own falls back to, in the risk-policy tables.
DOCUMENT_UNRATED_COLOUR = RAG["grey"]

# The colour names the standalone integration guide (docs/integration_guide.tex)
# defines for itself, and the document colour each one takes. That guide is a
# hand-written LaTeX file rather than a document assembled from ``preamble()`` --
# it has to build outside the app too -- so the platform hands it these
# definitions at generation time and the copy it publishes carries the adopter's
# brand rather than the values typed into its source (rule R10). ``mkmwash`` and
# ``mkmline`` are the note panel and the hairline down a listing; no other
# document draws either, which is why they are named here and not above.
STANDALONE_DOCUMENT_COLOURS = {
    "mkmblue": DOCUMENT_LINK_COLOUR,
    "mkmchrome": DOCUMENT_CHROME_COLOUR,
    "mkmred": DOCUMENT_CLASSIFICATION_COLOUR,
    "mkmwash": BRAND["accent-wash"],
    "mkmline": SURFACE["line"],
}

# The file those definitions are written to beside the source. The guide inputs it
# when it is present, so the name is spelled the same way in both places.
DOCUMENT_COLOUR_INCLUDE = "theme_colours.tex"

# Page setup, from the ``docs/Swaption.tex`` house template: 170mm of text with a
# 20mm top, and a 25mm bottom so the footer rule the template omits has room.
DOCUMENT_BASE_FONT_SIZE = "11pt"
DOCUMENT_GEOMETRY = "a4paper, left=20mm, right=20mm, top=20mm, bottom=25mm"
DOCUMENT_LINE_SPACING = "onehalfspacing"
DOCUMENT_RULE_WIDTH = "0.4pt"

# The template's large title fonts, used on the title page only.
DOCUMENT_TITLE_FONT = "cmr12"
DOCUMENT_TITLE_SIZE = "35pt"
DOCUMENT_SUBTITLE_SIZE = "25pt"

# The body typeface. Empty is the LaTeX default — Computer Modern, the serif face
# every document has printed in to date. "sans" loads Helvetica and makes it the
# default family, matching the console's Arial and closing the last divergence
# between the screen and the page. That is a visible change to every generated
# document, so it is a decision an adopter makes rather than a side effect of
# putting the parameter in one place.
DOCUMENT_BODY_FONT = ""

# The classification banner stamped on the title page and page footer of every
# generated document. Adopters to date have kept "CONFIDENTIAL".
DEFAULT_CLASSIFICATION = "CONFIDENTIAL — PROPRIETARY"

# Fallback organisation name for document headers/title pages when the singleton
# MRC settings ``org_name`` has not been set.
DEFAULT_ORG = "MKM Research Labs"

# "Prepared by" line on generated title pages. These documents are produced by the
# platform rather than a named person, so the author is the system by default.
DEFAULT_AUTHOR = "MKM-ModelRisk"

# The legal notice printed on the title page of every generated document. It covers
# the *contents* of the document -- the models, methodology and calculations it
# describes -- and says nothing about the software that produced it, which is
# MIT-licensed (see LICENSE). This wording asserts MKM Research Labs' rights; an
# institution asserting rights over its own model documentation replaces it in
# Admin > Misc, as with the classification banner. Paragraphs are one per entry
# here and separated by a blank line in the setting.
DEFAULT_LEGAL_NOTICE = (
    "PROPRIETARY AND CONFIDENTIAL",
    "This document, including all algorithms, models, methodology, formulas, "
    "calculations, and intellectual concepts contained herein, constitutes the "
    "exclusive intellectual property and confidential trade secrets of MKM Research "
    'Labs ("MKM").',
    "Any usage, reproduction, distribution, modification, or disclosure of this "
    "document or any portion thereof, without the express prior written "
    "authorisation from MKM Research Labs is strictly prohibited and constitutes an "
    "infringement of intellectual property rights.",
    'The document is provided on an "as is" basis. MKM Research Labs makes no '
    "representations or warranties of any kind, express or implied, regarding its "
    "accuracy, reliability, or suitability for any particular purpose.",
    "All rights reserved. © 2021–2026 MKM Research Labs.",
    "Governed by the laws of the United Kingdom.",
)
