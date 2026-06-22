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

"""Per-field edit specs derived from the CDM schema.

``field_spec`` turns a single schema descriptor into an editor spec (input
kind, options, numeric bounds). ``schema_specs`` walks a whole asset schema and
returns ``{dotted_path: spec}`` for every leaf field, keyed from the record
root so it lines up with the paths the editor renders. ``descriptor_at`` is the
inverse lookup used when validating an incoming change.
"""

from ._rules import TYPE_INPUT, numeric_bounds


def _is_field(node):
    return (
        isinstance(node, dict)
        and isinstance(node.get("type"), str)
    )


def field_spec(path, descriptor):
    """Editor spec for one leaf field descriptor at ``path``."""
    cdm_type = descriptor.get("type")
    spec = {
        "type": cdm_type,
        "input": TYPE_INPUT.get(cdm_type, "text"),
        "description": descriptor.get("description"),
    }
    if cdm_type == "menu":
        spec["options"] = list(descriptor.get("options", []))
    if spec["input"] == "number":
        lo, hi, step = numeric_bounds(path, cdm_type)
        spec["min"] = lo
        spec["max"] = hi
        spec["step"] = step
    return spec


def schema_specs(schema, root=""):
    """{dotted_path: field_spec} for every leaf field under ``schema``.

    ``root`` seeds the path (the section name when called per record section).
    """
    out = {}
    if not isinstance(schema, dict):
        return out
    for key, node in schema.items():
        path = root + "." + key if root else key
        if _is_field(node):
            out[path] = field_spec(path, node)
        elif isinstance(node, dict):
            out.update(schema_specs(node, path))
    return out


def descriptor_at(schema, path):
    """The schema descriptor for a dotted path, or None if it is not a field."""
    node = schema
    for seg in path.split("."):
        if not isinstance(node, dict) or seg not in node:
            return None
        node = node[seg]
    return node if _is_field(node) else None
