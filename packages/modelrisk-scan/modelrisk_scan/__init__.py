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
"""modelrisk-scan: producer-side client for feeding a ModelRisk collector.

Install into any repo that produces governance scans; build a provenance block,
then push artifacts to the collector::

    from modelrisk_scan import IngestClient, build_provenance

    client = IngestClient("https://modelrisk.internal", token=TOKEN)
    prov = build_provenance(
        source_repo="PhysicalRisk", producer="modelrisk-scan/data-lineage",
        producer_version="0.1.0",
    )
    result = client.push("data-lineage", manifest, prov)
    print(result.created)  # True stored, False idempotent
"""
from modelrisk_scan.client import IngestClient, IngestError, IngestResult
from modelrisk_scan.provenance import build_provenance

__all__ = ["IngestClient", "IngestError", "IngestResult", "build_provenance"]
