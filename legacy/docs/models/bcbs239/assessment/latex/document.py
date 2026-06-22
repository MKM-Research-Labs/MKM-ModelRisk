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

"""Assemble the BCBS 239 self-assessment LaTeX document (date/data-aware)."""

from datetime import datetime

from ._summary import build_summary
from ._detail import build_principle_sections, build_roadmap_and_appendix


def generate_document(data):
    """Generate the BCBS 239 self-assessment LaTeX document."""
    today = datetime.now().strftime('%d-%B-%Y')
    principles = data.get('principles', [])

    total_score = sum(p['score'] for p in principles)
    total_max = sum(p['max_score'] for p in principles)
    pct = round(total_score / total_max * 100) if total_max > 0 else 0

    categories = [
        ('Governance and Infrastructure', [1, 2]),
        ('Risk Data Aggregation', [3, 4, 5, 6]),
        ('Risk Reporting Practices', [7, 8, 9, 10, 11]),
        ('Supervisory Review', [12, 13, 14]),
    ]

    return (
        build_summary(data, principles, total_score, total_max, pct, categories, today)
        + build_principle_sections(principles, categories)
        + build_roadmap_and_appendix(principles, data, today)
    )
