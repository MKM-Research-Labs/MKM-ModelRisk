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
Data lineage tracking for BCBS 239 compliance.

Provides manifest recording, staleness validation, and provenance queries
for the portfolio generation pipeline.
"""

from lineage.manifest import (
    DEPENDENCY_GRAPH,
    STEP_IO,
    hash_file,
    hash_directory,
    load_manifest,
    save_manifest,
    get_current_run_id,
    record_step,
)
from lineage.validation import (
    check_inputs_fresh,
    check_pipeline_complete,
    check_step_prerequisites,
    get_stale_downstream,
    resolve_prerequisites,
    validate_full_chain,
)
from lineage.query import (
    trace_data_point,
    get_file_lineage,
    get_step_lineage,
)

__all__ = [
    "DEPENDENCY_GRAPH",
    "STEP_IO",
    "hash_file",
    "hash_directory",
    "load_manifest",
    "save_manifest",
    "get_current_run_id",
    "record_step",
    "check_inputs_fresh",
    "check_pipeline_complete",
    "check_step_prerequisites",
    "get_stale_downstream",
    "resolve_prerequisites",
    "validate_full_chain",
    "trace_data_point",
    "get_file_lineage",
    "get_step_lineage",
]
