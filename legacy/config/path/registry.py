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

"""Canonical registry of first-party filesystem path roots.

This module is the declared single source of truth for *where* path
definitions are allowed to live and *which* directory names count as
project-owned filesystem roots. It carries no resolution logic — the live
accessors are the methods on :class:`ConfigPaths` / :class:`PortfolioPaths`
(``get_project_root``, ``get_input_dir``, ``get_output_dir``,
``get_results_dir``, …). This file only *names* the roots so the path policy
is data rather than scattered string matching.

It backs the path-definition audit
(``docs/models/full_audit/sections_tests/path_definitions.py``): any module
outside the sanctioned :data:`SANCTIONED_PACKAGE` that hand-builds one of these
roots from a literal — instead of importing the corresponding ``config``
accessor — is flagged. Adding a new data sub-tree means giving it an accessor
on the path mixins and listing its segment here, in one place.
"""

# Top-level project directory that is a genuine filesystem root owned by the
# config package. A literal path that starts here (e.g. "data/output",
# "data/input/<catchment>") must be obtained from a config accessor, never
# written inline.
PROJECT_ROOT_DIRS = (
    "data",
)

# Sub-trees under data/ that each have a dedicated config accessor. These are
# the high-signal segments the audit keys on.
DATA_SUBDIRS = (
    "input",
    "output",
    "results",
    "catch",
)

# Package (relative to the repo root) that is the sanctioned home for *all*
# path construction. Modules under here are exempt from the audit — this is
# the one place path literals and project-root derivation are allowed to live.
SANCTIONED_PACKAGE = "config"

__all__ = ["PROJECT_ROOT_DIRS", "DATA_SUBDIRS", "SANCTIONED_PACKAGE"]
