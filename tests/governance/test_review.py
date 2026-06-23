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
"""Unit tests for model review-status classification (pure)."""
from __future__ import annotations

import pytest

from src.governance.model_inventory.review import compute_review_status

AS_OF = "2026-06-22"


@pytest.mark.parametrize(
    "next_review,expected",
    [
        (None, "Not Scheduled"),
        ("2026-06-01", "Overdue"),     # in the past
        ("2026-07-10", "Due Soon"),    # 18 days
        ("2026-08-30", "Upcoming"),    # 69 days
        ("2027-06-22", "On Track"),    # 365 days
    ],
)
def test_review_status(next_review, expected):
    assert compute_review_status(next_review, AS_OF) == expected
