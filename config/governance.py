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
"""Model-governance domain vocabulary and validation choices (coding rule R1).

Generic, model-agnostic. These are the editable scalar fields of a model
inventory entry and the closed value sets a client's governance team works with.
"""

# Scalar fields a model inventory entry exposes for editing.
EDITABLE_FIELDS = (
    "name",
    "short_name",
    "description",
    "category",
    "tier",
    "materiality",
    "complexity",
    "status",
    "lifecycle_stage",
    "version",
    "owner",
    "peer_reviewer",
    "validation_status",
    "rag_rating",
    "review_frequency",
)

VALID_RAG_RATINGS = ("Green", "Amber", "Red")
VALID_VALIDATION_STATUSES = (
    "Pending",
    "In Review",
    "Validated",
    "Conditionally Approved",
    "Rejected",
)
VALID_MATERIALITY = ("Low", "Medium", "High")
VALID_COMPLEXITY = ("Low", "Medium", "High")
VALID_LIFECYCLE_STAGES = ("Development", "Validation", "Production", "Retired")

TIER_MIN = 1
TIER_MAX = 5

# Fields constrained to a closed set of values.
FIELD_CHOICES = {
    "rag_rating": VALID_RAG_RATINGS,
    "validation_status": VALID_VALIDATION_STATUSES,
    "materiality": VALID_MATERIALITY,
    "complexity": VALID_COMPLEXITY,
    "lifecycle_stage": VALID_LIFECYCLE_STAGES,
}

# --- Model Risk Committee (MRC) meetings ---

# Editable scalar fields of a meeting.
MEETING_FIELDS = ("title", "date", "time", "location", "chair", "status")

VALID_MEETING_STATUSES = ("Scheduled", "In Progress", "Held", "Cancelled")
DEFAULT_MEETING_STATUS = "Scheduled"

VALID_ACTION_STATUSES = ("Open", "In Progress", "Closed")
DEFAULT_ACTION_STATUS = "Open"
