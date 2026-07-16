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
"""Tests for the command dispatch seam (confirm-to-amend + actor attribution)."""
from __future__ import annotations

import pytest

from src.command import (
    CommandContext,
    ConfirmationRequired,
    authorize,
    context_from_headers,
    dispatch,
)
from src.database import read_stream
from src.governance.model_inventory import AGGREGATE_TYPE, get_model, register_model
from src.identity import Principal


def _ctx(confirmed: bool, reason=None) -> CommandContext:
    principal = Principal(actor="alice@corp", display_name="Alice", source="sso-header")
    return CommandContext(principal=principal, confirmed=confirmed, reason=reason)


def test_dispatch_without_confirmation_writes_nothing():
    with pytest.raises(ConfirmationRequired):
        dispatch(
            "register_model", register_model,
            context=_ctx(confirmed=False), model_id="M1", name="Alpha",
        )
    assert read_stream(aggregate_type=AGGREGATE_TYPE, aggregate_id="M1") == []


def test_dispatch_with_confirmation_records_actor_and_reason():
    event = dispatch(
        "register_model", register_model,
        context=_ctx(confirmed=True, reason="onboarding"),
        model_id="M1", name="Alpha",
    )
    assert event.actor == "alice@corp"
    assert event.reason == "onboarding"
    assert get_model("M1") is None  # projection not rebuilt yet; event is recorded


def test_context_from_headers_threads_sso_actor_into_event():
    context = context_from_headers(
        {"X-Auth-Request-User": "carol@corp"}, confirmed=True, reason="created"
    )
    event = dispatch(
        "register_model", register_model,
        context=context, model_id="M2", name="Beta",
    )
    assert event.actor == "carol@corp"


def test_authorize_hook_allows_by_default():
    # All authenticated users may amend today; the hook is a no-op seam.
    principal = Principal(actor="x", display_name="x", source="sso-header")
    assert authorize(principal, "register_model") is None
