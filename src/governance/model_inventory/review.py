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
"""Model review status derived from the next-review date (pure)."""
from __future__ import annotations

from datetime import date

from config.governance import REVIEW_DUE_SOON_DAYS, REVIEW_UPCOMING_DAYS


def compute_review_status(next_review_date: str | None, as_of: str) -> str:
    """Classify a model's review currency relative to ``as_of`` (ISO dates)."""
    if not next_review_date:
        return "Not Scheduled"
    days = (date.fromisoformat(next_review_date) - date.fromisoformat(as_of)).days
    if days < 0:
        return "Overdue"
    if days <= REVIEW_DUE_SOON_DAYS:
        return "Due Soon"
    if days <= REVIEW_UPCOMING_DAYS:
        return "Upcoming"
    return "On Track"
