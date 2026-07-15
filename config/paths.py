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
"""Filesystem path parameters (coding rule R1 — paths defined only in config).

The single home for repository-relative paths used by the migration runner and
the demo seed/export scripts, so no source or script module walks the tree with
``Path(__file__)`` itself.
"""
from __future__ import annotations

from pathlib import Path

from config.files import UPLOAD_DIR

# Repository root (config/ lives directly under it).
_REPO_ROOT = Path(__file__).resolve().parents[1]

# Schema migration SQL, applied in lexical order by the migration runner.
MIGRATIONS_DIR = _REPO_ROOT / "src" / "database" / "migrations"

# Demo seed data + branded assets: read when seeding, written by the exporter.
DEMO_DATA_PATH = _REPO_ROOT / "scripts" / "demo_data.json"
DEMO_ASSETS_DIR = _REPO_ROOT / "scripts" / "demo_assets"
DEMO_LOGO_PATH = _REPO_ROOT / "docs" / "shared" / "moodys.jpeg"

# Live committee Terms-of-Reference uploads, copied back out by the exporter.
UPLOADS_MRC_DIR = UPLOAD_DIR / "mrc"
