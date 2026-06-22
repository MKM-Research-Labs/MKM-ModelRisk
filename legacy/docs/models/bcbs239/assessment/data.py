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

"""BCBS 239 assessment data loading and score utilities."""

import json
import os


_project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
# Governance metadata is version-controlled repo content under
# docs/models/governance_data/, not shared data/.
_data_path = os.path.join(
    _project_root, 'docs', 'models', 'governance_data', 'bcbs239_assessment.json')


def load_assessment():
    """Load assessment data from JSON."""
    with open(_data_path, 'r') as f:
        return json.load(f)


def score_label(score):
    """Return human-readable label for a score."""
    return {
        1: 'Non-compliant',
        2: 'Materially Non-compliant',
        3: 'Largely Compliant',
        4: 'Fully Compliant',
    }.get(score, 'Unknown')


def score_color(score):
    """Return LaTeX colour command for a score."""
    return {
        1: r'\textcolor{red}',
        2: r'\textcolor{orange}',
        3: r'\textcolor{blue}',
        4: r'\textcolor{green!60!black}',
    }.get(score, '')
