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
"""The data-source seed: the feeds a record draws its inputs from.

Its own module rather than another entry in ``_reference.py``, which sits one line
under R2's limit -- and because the catalogue is the sort of thing that grows.

**Data Source is not Vendor**, and the two are confused often enough to be worth
stating plainly. A data source is where the DATA comes from: Bloomberg, ICE, the Met
Office, NOAA, a client's own file. A vendor is who supplies the MODEL: the firm whose
analytics you licensed, or "In-house". Bloomberg can be both, on two different records,
and answering "who supplies this?" with a data feed is how a model's provenance stops
being traceable.

**Specific names, not categories.** "Market data" as a data source tells a reviewer
nothing; "ICE" tells them which contract governs it, which desk pays for it and who to
ask when it stops arriving. The point of the list being strict is that two records
naming the same feed match on a defined id rather than on spelling, and that only pays
if the entries are the actual feeds.

``kind`` is seeded because whether a feed originates outside the institution is a fact
about the feed. ``sensitivity`` and ``egress`` are NOT seeded: what a firm considers
confidential, and what its contract permits leaving, are its own judgements -- the same
reason the estimator seed carries no versions.

Nothing here is a recommendation to subscribe to anything. It is a starting menu an
adopter trims to the feeds it actually runs; the lists seed a vacuum and never
reconcile a curated one, so anything deleted in Admin stays deleted.
"""
from __future__ import annotations

_EXTERNAL = "External"
_INTERNAL = "Internal"

# Market, reference and credit data.
_MARKET = ("Bloomberg", "ICE", "Reuters", "LSEG", "S&P Global", "MSCI",
           "Moody's Analytics")

# Weather, climate and natural-hazard data. Present because physical-risk models are a
# first-class use of this platform and their inputs come from meteorological and
# geological agencies rather than from market-data desks -- a catalogue that stops at
# Bloomberg cannot describe a flood model's provenance.
_HAZARD = ("Met Office", "NOAA", "ECMWF", "Copernicus", "Environment Agency",
           "USGS", "JBA Risk Management")

# Public, statistical and registry data.
_PUBLIC = ("ONS", "Eurostat", "HM Land Registry", "Ordnance Survey")

# The institution's own data. "Simulated" and "Manual" are first-class entries, not
# placeholders for a real feed somebody has yet to name -- a stochastic event set IS
# the input to a catastrophe model, and a hand-maintained assumption table IS where a
# pricing model's inputs come from. On this estate they are the common case. Recording
# them honestly is what lets a reviewer ask the question that matters about simulated
# input, which is what generated it and whether that generator is itself governed.
_INTERNAL_SOURCES = ("Simulated", "Manual", "Internal data warehouse",
                     "Client-supplied")

# Ordered as the Admin list shows them: external providers first, grouped by what they
# supply, then the institution's own. "Other" last, because a catch-all offered early
# is the one people pick.
DEFAULT_DATA_SOURCES: tuple[dict[str, str], ...] = tuple(
    [{"value": name, "kind": _EXTERNAL} for name in _MARKET + _HAZARD + _PUBLIC]
    + [{"value": name, "kind": _INTERNAL} for name in _INTERNAL_SOURCES]
    + [{"value": "Other", "kind": _EXTERNAL}]
)

__all__ = ["DEFAULT_DATA_SOURCES"]
