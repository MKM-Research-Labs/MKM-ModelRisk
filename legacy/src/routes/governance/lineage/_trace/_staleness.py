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

"""Per-step freshness/staleness checks against the lineage manifest + disk."""

import os
from datetime import datetime, timedelta

from config.port import LINEAGE_STALE_HOURS as _STALE_HOURS

from ._steps import _PIPELINE_STEPS


def _check_staleness(lineage):
    """Check each pipeline step for freshness. Returns list of step statuses."""
    from config import config

    input_dir = str(config.get_input_dir())
    now = datetime.now()
    results = []

    for step_def in _PIPELINE_STEPS:
        path = os.path.join(input_dir, step_def["output"])
        step_info = {
            "step": step_def["step"],
            "generator": step_def["generator"],
            "path": step_def["output"],
            "last_run": None,
            "status": "missing",
            "issues": [],
        }

        # Check if lineage manifest has a recorded run
        if lineage:
            manifest_steps = lineage.get("steps", {})
            manifest_entry = manifest_steps.get(step_def["step"], {})
            if manifest_entry.get("last_run"):
                step_info["last_run"] = manifest_entry["last_run"]

        # Check filesystem
        try:
            if os.path.isdir(path):
                # For directories, check most recent file
                mtime = max(
                    os.path.getmtime(os.path.join(path, f))
                    for f in os.listdir(path) if not f.startswith(".")
                ) if os.listdir(path) else 0
            elif os.path.isfile(path):
                mtime = os.path.getmtime(path)
            else:
                mtime = 0
        except (OSError, ValueError):
            mtime = 0

        if mtime > 0:
            last_modified = datetime.fromtimestamp(mtime)
            if not step_info["last_run"]:
                step_info["last_run"] = last_modified.isoformat()
            age = now - last_modified
            if age > timedelta(hours=_STALE_HOURS):
                step_info["status"] = "stale"
                step_info["issues"].append(
                    f"Last modified {age.days}d {age.seconds // 3600}h ago"
                )
            else:
                step_info["status"] = "fresh"
        else:
            step_info["status"] = "missing"
            step_info["issues"].append("Output not found on disk")

        results.append(step_info)

    return results
