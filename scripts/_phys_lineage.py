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
"""Handed-off fields that the consumer binds under a different name.

The source chain declares one name per field, from the giver's side, so by default
provider and consumer field are the same. That is usually right, but not always:
where the consuming model reads the field and immediately binds it to a different
symbol, the lineage should say so, because that rename is exactly what a reviewer
needs to follow the data across the handoff.

Each entry below was confirmed by reading the *consuming* model's source, and
carries the file:line so the MRC can check it. Nothing is inferred from prose: the
descriptions also hint at renames for MKM-GH-001's exceedance probabilities and
MKM-BRI-001's flood score, but those name a computation or a config lookup table
rather than a receiver field, and are deliberately excluded.
"""

# (producer, consumer) -> {provider_field: (consumer_field, evidence)}
FIELD_RENAMES = {
    ("MKM-SI-001", "MKM-SG-001"): {
        # precip_factor = storm['effective_precipitation_mm'] / 35.0
        "effective_precipitation_mm": ("precip_factor",
                                       "src/models/hazard/response_model.py:96"),
        # duration_factor = min(2.0, storm['duration_hours'] / 24.0)
        "duration_hours": ("duration_factor", "src/models/hazard/response_model.py:97"),
    },
    ("MKM-PV-001", "MKM-MP-001"): {
        # The pricer's API takes property_value throughout; weaker evidence than the
        # two above, since it is a parameter name rather than a direct field read.
        "value": ("property_value", "src/models/loan/pricer/credit.py:73"),
    },
}


def apply_field_renames(actor: str, config=None) -> int:
    """Record the confirmed renames onto the handoffs' field lineage, appending the
    evidence to each note. Idempotent: a field already renamed is left alone."""
    from src.governance.model_handoff import get_handoff_for_edge, rebuild_handoff_view
    from src.governance.model_handoff.commands import update_collection_item

    applied = 0
    for (producer, consumer), renames in FIELD_RENAMES.items():
        handoff = get_handoff_for_edge(producer, consumer, config=config)
        if handoff is None:
            continue
        for item in handoff["data"].get("field_lineage") or []:
            target = renames.get(item.get("provider_field"))
            if target is None or item.get("consumer_field") == target[0]:
                continue
            name, evidence = target
            note = f"{(item.get('note') or '').rstrip()} [Consumer binds this as {name} - {evidence}]"
            update_collection_item(
                handoff_id=handoff["handoff_id"], collection="field_lineage",
                item_id=item["item_id"], actor=actor, config=config,
                fields={"consumer_field": name, "note": note.strip()})
            applied += 1
    rebuild_handoff_view(config=config)
    return applied
