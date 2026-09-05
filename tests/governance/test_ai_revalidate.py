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
"""Revalidation: the release manifest, and the risks that never close.

Two ideas, and both are about what cannot be adjusted afterwards. A manifest is worth
something only because it cannot be edited once somebody asks what was in the release.
The standing register is worth something only because it reads the same everywhere —
a shorter list in one deployment is a risk somebody has been told does not apply to
them.
"""
from __future__ import annotations

import pytest

from config.governance._change import CHANGE_CLASSES
from config.governance._ml_application import ML_APPLICATION_COLLECTION_SPECS
from config.governance._standing_risks import (STANDING_RISK_IDS, STANDING_RISKS,
                                               STANDING_REVIEW_POINTS)
from src.governance.ai_system import (get_ai_system, rebuild_ai_system_view,
                                      rebuild_standing_risk_register_view,
                                      record_variability_envelope,
                                      rebuild_configuration_snapshot_view,
                                      register_ai_system, seal_release_manifest,
                                      set_trigger_threshold, standing_risks,
                                      take_configuration_snapshot,
                                      update_ai_system_field)
from src.governance.ai_system._rules import manifest_digest, manifest_intact
from src.governance.change._rules import classify
from src.governance.errors import DomainError

_MINIMUM = {"name": "Claims triage agent", "division": "Risk", "owner": "A",
            "use_case": "Triages claims.", "deployment_pattern": "Agentic (tool-using)",
            "pinned_version": "claude-opus-4"}


def _ready(ai_system_id="AIS-1"):
    register_ai_system(ai_system_id=ai_system_id, fields=dict(_MINIMUM), actor="admin")
    rebuild_ai_system_view()
    take_configuration_snapshot(ai_system_id=ai_system_id, actor="admin")
    rebuild_configuration_snapshot_view()
    return ai_system_id


def _manifests(ai_system_id="AIS-1"):
    rebuild_ai_system_view()
    return get_ai_system(ai_system_id)["data"]["release_manifests"]


# --- 5.1 The release manifest --------------------------------------------------

def test_finos_version_bump_classifies_as_measurement():
    """The four-tier engine applied to its primary use. A taxonomy version bump is a
    Measurement-class change against the mapping engine, not a Material one against
    every record the engine mapped."""
    assert classify(subject_type="ai_system", before={}, after={},
                    affected_artifacts=["finos_taxonomy"]) == "Measurement"


def test_a_manifest_records_the_tier_that_authorised_the_release():
    """So somebody can later ask "this was Material; where is the evidence it was
    revalidated" without reconstructing the answer from three registers."""
    _ready()
    seal_release_manifest(ai_system_id="AIS-1", release="2026.09.1",
                          change_class="Material", actor="admin")
    sealed = _manifests()[0]
    assert sealed["change_class"] == "Material"
    assert sealed["release"] == "2026.09.1"


def test_a_manifest_seals_the_configuration_the_envelope_and_the_bars():
    _ready()
    set_trigger_threshold(ai_system_id="AIS-1", property_name="robustness",
                          threshold=0.99, fallback="Suspend the system", actor="admin")
    record_variability_envelope(ai_system_id="AIS-1",
                                scores=[0.8 + (i % 5) / 100 for i in range(20)],
                                actor="admin")
    seal_release_manifest(ai_system_id="AIS-1", release="2026.09.1",
                          change_class="Bounded", actor="admin")

    contents = _manifests()[0]["contents"]
    assert contents["config_version"] == 1
    assert contents["configuration"]["pinned_version"] == "claude-opus-4"
    assert contents["thresholds"]["robustness"] == 0.99
    assert contents["envelope"]["runs"] == 20


def test_a_sealed_manifest_is_tamper_evident():
    """Immutability in an append-only log means nothing can be edited in place; the
    digest is what makes an alteration in transit or in a copy detectable."""
    _ready()
    seal_release_manifest(ai_system_id="AIS-1", release="r1", change_class="Bounded",
                          actor="admin")
    sealed = _manifests()[0]
    assert manifest_intact(sealed)

    altered = {**sealed, "contents": {**sealed["contents"], "config_version": 99}}
    assert not manifest_intact(altered)
    assert manifest_digest(sealed["contents"]) == sealed["digest"]


def test_sealing_the_same_release_twice_is_refused():
    """A second manifest for one release is two answers to "what was in it"."""
    _ready()
    seal_release_manifest(ai_system_id="AIS-1", release="r1", change_class="Bounded",
                          actor="admin")
    with pytest.raises(DomainError, match="already sealed"):
        seal_release_manifest(ai_system_id="AIS-1", release="r1",
                              change_class="Bounded", actor="admin")


def test_a_release_cannot_be_sealed_without_a_configuration():
    """A manifest that could not say what was configured would be a release note."""
    register_ai_system(ai_system_id="AIS-2", fields=dict(_MINIMUM), actor="admin")
    rebuild_ai_system_view()
    with pytest.raises(DomainError, match="snapshot first"):
        seal_release_manifest(ai_system_id="AIS-2", release="r1",
                              change_class="Bounded", actor="admin")


def test_the_manifest_names_a_tier_the_engine_knows():
    _ready()
    with pytest.raises(DomainError, match="change class must be one of"):
        seal_release_manifest(ai_system_id="AIS-1", release="r1",
                              change_class="Cosmetic", actor="admin")
    assert "Material" in CHANGE_CLASSES


def test_an_earlier_manifest_is_untouched_by_a_later_release():
    _ready()
    seal_release_manifest(ai_system_id="AIS-1", release="r1", change_class="Bounded",
                          actor="admin")
    first = _manifests()[0]

    update_ai_system_field(ai_system_id="AIS-1", field="pinned_version",
                           value="claude-opus-5", actor="admin")
    rebuild_ai_system_view()
    take_configuration_snapshot(ai_system_id="AIS-1", actor="admin")
    rebuild_configuration_snapshot_view()
    seal_release_manifest(ai_system_id="AIS-1", release="r2", change_class="Material",
                          actor="admin")

    assert _manifests()[0] == first, "sealing r2 altered r1"
    assert _manifests()[1]["contents"]["configuration"]["pinned_version"] \
        == "claude-opus-5"


# --- 5.2 The standing risk register --------------------------------------------

def test_register_absent_from_ml_applications():
    """Spec §7: an ML Application's bias and IP questions are answered inside its
    training and validation record, not carried as standing exposures of a model
    somebody else trained."""
    assert "standing_risks" not in ML_APPLICATION_COLLECTION_SPECS
    assert "standing_risk_register" not in ML_APPLICATION_COLLECTION_SPECS


def test_row_set_identical_under_both_deployment_configurations():
    """Spec §10: no entry muted or filtered per deployment. The register is built from
    config with no deployment input at all, so there is nowhere for a deployment to
    change it — asserted by rebuilding twice and comparing, and by there being no
    parameter that could vary."""
    import inspect
    from src.governance.ai_system.registers import rebuild_standing_risk_register_view

    rebuild_standing_risk_register_view()
    first = [r["risk_id"] for r in standing_risks()]
    rebuild_standing_risk_register_view()
    assert [r["risk_id"] for r in standing_risks()] == first

    signature = inspect.signature(rebuild_standing_risk_register_view)
    assert set(signature.parameters) == {"config"}, \
        "a parameter that could vary the register per deployment appeared"
    assert first == list(STANDING_RISK_IDS)


def test_every_standing_risk_says_why_it_stands_outside_the_lifecycle():
    """A register of risks with no reason each is standing is a list of risks."""
    for ref, title, why in STANDING_RISKS:
        assert ref.startswith("AIR-"), "identifiers are the FINOS catalogue's own"
        assert title.strip() and len(why.strip()) > 40, f"{ref} is not explained"


def test_the_standing_risks_are_real_catalogue_entries():
    """A register entry naming a risk the catalogue does not define could not be
    evidenced against it. The spec names six; this catalogue defines five, and no sixth
    is invented."""
    from config.governance._finos import FINOS_RISK_CATALOGUE
    known = {ref for ref, _, _, _ in FINOS_RISK_CATALOGUE}
    assert set(STANDING_RISK_IDS) <= known


def test_the_review_points_are_events_not_a_schedule():
    """A standing risk reviewed quarterly regardless of what changed is a diary entry."""
    assert set(STANDING_REVIEW_POINTS) == {"onboarding", "material revalidation"}
