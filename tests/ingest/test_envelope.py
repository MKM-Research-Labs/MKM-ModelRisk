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
"""Pure tests for content hashing and the synthetic ingest principal."""
from __future__ import annotations

from src.identity import ingest_principal
from src.identity._principal import SOURCE_INGEST
from src.ingest._envelope import content_hash


def test_content_hash_is_order_independent():
    a = {"runs": {"r1": ["s1"]}, "steps": {"s1": {"type": "file"}}}
    b = {"steps": {"s1": {"type": "file"}}, "runs": {"r1": ["s1"]}}
    assert content_hash(a) == content_hash(b)


def test_content_hash_changes_with_content():
    a = {"runs": {"r1": ["s1"]}}
    b = {"runs": {"r1": ["s2"]}}
    assert content_hash(a) != content_hash(b)


def test_content_hash_is_hex_sha256():
    digest = content_hash({"x": 1})
    assert len(digest) == 64 and int(digest, 16) >= 0


def test_ingest_principal_actor_and_source():
    prov = {"source_repo": "PhysicalRisk", "producer": "modelrisk-scan/data-lineage"}
    principal = ingest_principal(prov)
    assert principal.actor == "ingest:PhysicalRisk"
    assert principal.display_name == "modelrisk-scan/data-lineage"
    assert principal.source == SOURCE_INGEST


def test_ingest_principal_defaults_producer_to_repo():
    principal = ingest_principal({"source_repo": "PhysicalRisk"})
    assert principal.display_name == "PhysicalRisk"
