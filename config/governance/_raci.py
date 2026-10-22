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
"""The RACI operating model's vocabulary (coding rule R1).

Two things, and only one of them is the institution's to change. The four
accountabilities -- Responsible, Accountable, Consulted, Informed -- ARE the method; a
fifth would not be RACI. The roles that hold them are not: one institution's
"Model user" is another's "Front Office", so the roles are an admin list.

The list is a status vocabulary with one extra column. ``value`` is what a model's or
a Product's RACI entry stores, ``label`` is what a screen shows, and ``raci`` is the
accountability a new Product is scaffolded with that role for. Renaming a role edits
its label and moves nothing on record; removing one stops it being offered, while
the entries that already carry it go on displaying the word they hold.
"""
from __future__ import annotations

from config.governance._vocabulary import status_vocabulary_spec

RACI_ROLE_LIST = "raci_role"

# The four RACI accountabilities, defining who does what for a product's use of
# models in production (the RACI operating model, held at the product level).
VALID_RACI_CODES = ("Responsible", "Accountable", "Consulted", "Informed")

# What the role list ships with: (raci code, role) -- the four every model in the
# estate already carries, so the list starts as the words on record. A product's RACI
# is complete only with all four, so registration scaffolds one entry per role marked
# with an accountability -- the way a model's SR 26-2 questions are seeded on
# registration. These are the SEED, not the vocabulary: once the list exists,
# registration reads it.
DEFAULT_RACI = (
    ("Responsible", "Operations Lead"),
    ("Accountable", "Model Owner"),
    ("Consulted", "Independent Validator"),
    ("Informed", "MRC"),
)

_RACI_ROLE_SPEC = status_vocabulary_spec(
    "RACI", "RR",
    "The roles a model's or Product's RACI is assigned to. <b>Seeded as</b> is "
    "the accountability a newly registered Product is given this role for; leave it "
    "blank for a role that is offered but not scaffolded.")
_RACI_ROLE_SPEC["fields"].append(
    {"key": "raci", "label": "Seeded as", "type": "choice", "options": VALID_RACI_CODES})

RACI_REFERENCE_LISTS = (RACI_ROLE_LIST,)
RACI_REFERENCE_SPECS = {RACI_ROLE_LIST: _RACI_ROLE_SPEC}
