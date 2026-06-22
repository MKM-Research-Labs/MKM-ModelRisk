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

from src.command._context import CommandContext
from src.identity import Principal, resolve_principal


class ConfirmationRequired(RuntimeError):
    """Raised when a mutating command is dispatched without confirmation."""


class AuthorizationError(RuntimeError):
    """Raised by ``authorize`` when a principal may not run a command."""


def authorize(principal: Principal, command_name: str) -> None:
    """Authorization hook. No-op today; the seam for future RBAC rules."""
    return None


def context_from_headers(
    headers, *, confirmed: bool, reason: str | None = None, allow_fallback: bool = True
) -> CommandContext:
    """Build a ``CommandContext`` from request headers and the confirm flag."""
    principal = resolve_principal(headers, allow_fallback=allow_fallback)
    return CommandContext(principal=principal, confirmed=confirmed, reason=reason)


def dispatch(
    command_name: str,
    handler: Callable[..., Any],
    *,
    context: CommandContext,
    **kwargs: Any,
) -> Any:
    """Run a mutating command handler within ``context``.

    The handler must accept ``actor`` and ``reason`` keyword arguments.
    """
    if not context.confirmed:
        raise ConfirmationRequired(
            f"command '{command_name}' requires explicit confirmation"
        )
    authorize(context.principal, command_name)
    return handler(
        actor=context.principal.actor, reason=context.reason, **kwargs
    )
