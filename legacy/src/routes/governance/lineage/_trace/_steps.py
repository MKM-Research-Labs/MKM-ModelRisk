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

"""Pipeline-step descriptors derived from the lineage registry."""


def _build_pipeline_steps():
    """Derive pipeline-step descriptors from the lineage registry so the
    governance staleness route stays in sync with DEPENDENCY_GRAPH /
    STEP_IO automatically. Steps are emitted in topological order; the
    representative output is the first declared in STEP_IO."""
    from graphlib import TopologicalSorter

    from lineage.manifest import DEPENDENCY_GRAPH, STEP_IO

    topo_order = list(TopologicalSorter(DEPENDENCY_GRAPH).static_order())
    steps: list[dict] = []
    for i, step_name in enumerate(topo_order, start=1):
        io = STEP_IO.get(step_name)
        if io is None or not io["outputs"]:
            continue
        steps.append({
            "step": step_name,
            "generator": f"port (step {i})",
            "output": io["outputs"][0],
        })
    return steps


_PIPELINE_STEPS = _build_pipeline_steps()
