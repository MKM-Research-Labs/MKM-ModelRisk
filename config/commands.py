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
"""Confirm-to-amend policy (rule R1).

Which changes are important enough to require the explicit confirmation step.
Everything not named here applies immediately — no confirmation dialog, no
recorded change reason. The confirmation is enforced server-side in
``src.command.dispatch`` so the client cannot bypass it.

Composed MRC decisions — sign-off approve / reject / revoke and closing a meeting
— run several sub-commands rather than one dispatched command, so they enforce
confirmation explicitly at their endpoints via ``require_confirmation``.
"""
from __future__ import annotations

# Whole commands that always require confirmation. Retiring is significant and
# effectively one-way — the subject becomes read-only — so both the model and the
# product retire commands are gated, and the reason is recorded on the event.
CONFIRM_REQUIRED_COMMANDS = frozenset({
    "register_model",
    "register_product",
    "retire_model",
    "retire_product",
})

# Scalar-field edits that require confirmation, keyed by the field-update command.
# Owner and risk rating are the significant model/product edits; a *meeting's*
# Status is significant, but a model/product's own Status field is not — hence the
# per-command split rather than one shared field set.
CONFIRM_REQUIRED_FIELDS = {
    "update_model_field": frozenset({"owner", "rag_rating"}),
    "update_product_field": frozenset({"owner", "rag_rating"}),
    "update_field": frozenset({"owner", "rag_rating"}),      # Subject.set_field
    "update_meeting_field": frozenset({"status"}),
}
