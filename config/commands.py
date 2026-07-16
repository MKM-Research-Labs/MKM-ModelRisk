# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
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
