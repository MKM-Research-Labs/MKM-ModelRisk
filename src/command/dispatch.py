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
"""The command dispatch seam — confirm-to-amend, actor attribution, authz hook.

Every mutating command goes through ``dispatch``. It enforces three things in
one place:

1. **Confirm-to-amend** — refuses to run unless the context is confirmed, so the
   UI confirmation dialog cannot be bypassed.
2. **Actor attribution** — threads the resolved principal's ``actor`` and the
   change ``reason`` into the handler, which records them on the event.
3. **Authorization** — calls ``authorize`` (a no-op today): the single seam where
   future role rules would live. All authenticated users may amend for now.
"""
from __future__ import annotations

from typing import Any, Callable

from config.commands import CONFIRM_REQUIRED_COMMANDS, CONFIRM_REQUIRED_FIELDS
from src.command._context import CommandContext
from src.identity import Principal, assert_recognised, resolve_principal


class ConfirmationRequired(RuntimeError):
    """Raised when a mutating command is dispatched without confirmation."""


class AuthorizationError(RuntimeError):
    """Raised by ``authorize`` when a principal may not run a command."""


def authorize(principal: Principal, command_name: str) -> None:
    """May this principal run this command?

    Phase P1 answers only "is the author somebody the institution registered". Every
    mutating command passes through here, so a new endpoint cannot forget to ask — the
    same reason R6 puts database access behind one door. Roles and segregation of duties
    (docs/permissions_design.md P2-P5) extend this function; they do not add a second gate.
    """
    assert_recognised(principal.actor)


def context_from_headers(
    headers, *, confirmed: bool, reason: str | None = None, allow_fallback: bool = True
) -> CommandContext:
    """Build a ``CommandContext`` from request headers and the confirm flag."""
    principal = resolve_principal(headers, allow_fallback=allow_fallback)
    return CommandContext(principal=principal, confirmed=confirmed, reason=reason)


def _requires_confirmation(command_name: str, kwargs: dict[str, Any]) -> bool:
    """Whether this command needs the explicit confirmation step (rule R1 policy
    in ``config.commands``). Non-critical changes apply without a confirmation."""
    if command_name in CONFIRM_REQUIRED_COMMANDS:
        return True
    critical_fields = CONFIRM_REQUIRED_FIELDS.get(command_name)
    return bool(critical_fields) and kwargs.get("field") in critical_fields


def require_confirmation(command_name: str, context: CommandContext) -> None:
    """Explicit confirm gate for composed operations (MRC sign-off / reject /
    revoke, close meeting) that run several sub-commands rather than one
    dispatched command. Raises before any of them mutate."""
    if not context.confirmed:
        raise ConfirmationRequired(
            f"command '{command_name}' requires explicit confirmation"
        )


def dispatch(
    command_name: str,
    handler: Callable[..., Any],
    *,
    context: CommandContext,
    **kwargs: Any,
) -> Any:
    """Run a mutating command handler within ``context``.

    The handler must accept ``actor`` and ``reason`` keyword arguments. Commands
    the confirm-to-amend policy deems important refuse to run unconfirmed;
    everything else applies immediately.
    """
    if _requires_confirmation(command_name, kwargs) and not context.confirmed:
        raise ConfirmationRequired(
            f"command '{command_name}' requires explicit confirmation"
        )
    authorize(context.principal, command_name)
    return handler(
        actor=context.principal.actor, reason=context.reason, **kwargs
    )
