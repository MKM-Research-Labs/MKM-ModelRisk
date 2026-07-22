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
"""Defaults for generated documents, meant to be edited by an adopting institution.

Every PDF the platform generates goes through the shared LaTeX house style, which
reads these values. The classification banner is deliberately generic — an adopter
(inside their own governance framework) changes it here to re-label every document
at once, rather than hunting through the code.
"""

# The classification banner stamped on the title page and page footer of every
# generated document. Adopters to date have kept "CONFIDENTIAL"; change it here.
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
# MIT-licensed (see LICENSE). An adopting institution asserting rights over its own
# model documentation changes the wording here, as with the classification banner.
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
