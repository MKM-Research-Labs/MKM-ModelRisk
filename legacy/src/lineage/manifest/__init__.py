# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Data lineage manifest — records pipeline step execution with content hashes.

Each step records its inputs, outputs, parameters, and timing so that
downstream consumers can verify data freshness (BCBS 239 Principle 3).
"""

from ._core import (
    LINEAGE_PATH,
    hash_file,
    hash_directory,
    load_manifest,
    save_manifest,
    get_current_run_id,
    _hash_artifact,
    pre_hash_inputs,
    record_step,
    repair_manifest,
)
from ._topology import (
    DEPENDENCY_GRAPH,
    EXTERNAL_INPUTS,
    OPTIONAL_STEPS,
    STEP_IO,
)

__all__ = [
    "LINEAGE_PATH",
    "hash_file",
    "hash_directory",
    "load_manifest",
    "save_manifest",
    "get_current_run_id",
    "_hash_artifact",
    "pre_hash_inputs",
    "record_step",
    "repair_manifest",
    "DEPENDENCY_GRAPH",
    "EXTERNAL_INPUTS",
    "OPTIONAL_STEPS",
    "STEP_IO",
]
