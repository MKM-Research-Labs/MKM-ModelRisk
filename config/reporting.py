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
DEFAULT_CLASSIFICATION = "CONFIDENTIAL"

# Fallback organisation name for document headers/title pages when the singleton
# MRC settings ``org_name`` has not been set.
DEFAULT_ORG = "MKM Research Labs"
