# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
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
