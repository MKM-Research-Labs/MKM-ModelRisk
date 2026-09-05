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
"""What a lineage node can be.

The chain was a string of pearls between models, and every node in it was one. That was
true when the estate was models; it is not true of a system whose harness calls an ML
Application as a tool, runs on a foundation model somebody else versions, and reaches an
MCP server outside the firm. Those are the things a dependency actually points at, and a
graph that can only say "model" describes them all as the same kind of thing.

**Two of these five are not governed records, and that is the point.** A foundation
model and an MCP server are dependencies the institution does not own and cannot
review — which is exactly why they have to appear. A supply chain you cannot draw is
one nobody notices until it moves under you.

Nothing here restricts which kind may depend on which. It was tempting to say a
foundation model has no dependencies of its own, and it is wrong: a firm hosting one
privately may well record what it was fine-tuned from. The graph records what somebody
declares; the acyclicity rule is the only structural claim it makes.
"""
from __future__ import annotations

NODE_MODEL = "MODEL"
NODE_ML_APPLICATION = "ML_APPLICATION"
NODE_AI_SYSTEM = "AI_SYSTEM"
NODE_FOUNDATION_MODEL = "FOUNDATION_MODEL"
NODE_MCP_SERVER = "MCP_SERVER"

NODE_KINDS = (NODE_MODEL, NODE_ML_APPLICATION, NODE_AI_SYSTEM,
              NODE_FOUNDATION_MODEL, NODE_MCP_SERVER)

# A node with no declared kind is a model. Every chain pushed before this existed is a
# graph of models, and re-ingesting one must not turn its nodes into "unknown".
DEFAULT_NODE_KIND = NODE_MODEL

NODE_KIND_LABELS = {
    NODE_MODEL: "Model",
    NODE_ML_APPLICATION: "ML Application",
    NODE_AI_SYSTEM: "AI System",
    NODE_FOUNDATION_MODEL: "Foundation model",
    NODE_MCP_SERVER: "MCP server",
}

# Which node kinds correspond to a record this platform governs, and under which
# ``Subject.kind``. The other two resolve to nothing on purpose: a node the firm does
# not own has no record to open, and a screen offering a link to one would be lying.
NODE_KIND_RECORD_TYPES = {
    NODE_MODEL: "model",
    NODE_ML_APPLICATION: "ml_application",
    NODE_AI_SYSTEM: "ai_system",
    NODE_FOUNDATION_MODEL: None,
    NODE_MCP_SERVER: None,
}

# The kinds the institution does not own. Named rather than derived from the map above
# so a coverage report can ask the question directly: how much of this chain is outside
# the perimeter?
EXTERNAL_NODE_KINDS = tuple(k for k, v in NODE_KIND_RECORD_TYPES.items() if v is None)


def node_kind(node: dict) -> str:
    """A node's kind, defaulting for anything that does not declare one."""
    declared = str((node or {}).get("kind") or "").strip().upper()
    return declared if declared in NODE_KINDS else DEFAULT_NODE_KIND


def is_governed(kind: str) -> bool:
    """Whether this kind is a record the platform holds, rather than a dependency
    outside the firm that can only be named."""
    return NODE_KIND_RECORD_TYPES.get(kind) is not None


__all__ = ["DEFAULT_NODE_KIND", "EXTERNAL_NODE_KINDS", "NODE_AI_SYSTEM",
           "NODE_FOUNDATION_MODEL", "NODE_KINDS", "NODE_KIND_LABELS",
           "NODE_KIND_RECORD_TYPES", "NODE_MCP_SERVER", "NODE_ML_APPLICATION",
           "NODE_MODEL", "is_governed", "node_kind"]
