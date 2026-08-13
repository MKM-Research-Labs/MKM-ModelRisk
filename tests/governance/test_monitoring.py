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
"""Reading the port output, and the monitoring report built from it."""
from __future__ import annotations

import json

from src.governance.monitoring.portfolio import catchments, summary
from src.governance.monitoring.report import build_monitoring_tex

SETTINGS = {"fields": {"org_name": "Test Org"}}
AS_OF = "2026-07-24"


def _catchment(root, name, **files):
    directory = root / name
    directory.mkdir(parents=True)
    for filename, payload in files.items():
        (directory / f"{filename}.json").write_text(json.dumps(payload))
    return directory


def _model(**data):
    base = {"name": "Alpha", "model_weaknesses": [], "limitations": []}
    base.update(data)
    return {"model_id": "M1", "data": base}


# --- reading the port output -----------------------------------------------

def test_counts_records_from_a_bare_list(tmp_path):
    _catchment(tmp_path, "thames", property=[{"id": 1}, {"id": 2}])
    found = catchments(tmp_path)
    assert found[0]["catchment"] == "thames"
    assert found[0]["records"] == 2


def test_counts_records_from_a_wrapped_list(tmp_path):
    """Portfolio files are not uniformly shaped; the population is the longest
    contained list, not the number of top-level keys."""
    _catchment(tmp_path, "thames",
               property={"metadata": {"run": 1}, "properties": [{}, {}, {}]})
    assert catchments(tmp_path)[0]["records"] == 3


def test_empty_catchment_is_reported_not_dropped(tmp_path):
    """An empty catchment is an observation. Dropping it would leave a reader
    unable to tell it from one that was never run."""
    (tmp_path / "rhine").mkdir()
    found = catchments(tmp_path)
    assert [c["catchment"] for c in found] == ["rhine"]
    assert found[0]["populations"] == []
    assert found[0]["last_built"] == ""


def test_derived_variants_are_not_counted(tmp_path):
    """A catchment holds per-model views of the same population (propertybri,
    propertybaw). Counting those would report one portfolio several times."""
    _catchment(tmp_path, "thames", property=[{}, {}],
               propertybri=[{}, {}], propertybaw=[{}, {}])
    assert catchments(tmp_path)[0]["records"] == 2


def test_unreadable_file_is_skipped_rather_than_fatal(tmp_path):
    directory = tmp_path / "thames"
    directory.mkdir()
    (directory / "property.json").write_text("{not json")
    (directory / "gauge.json").write_text(json.dumps([{}, {}]))
    found = catchments(tmp_path)
    assert found[0]["records"] == 2
    assert [p["label"] for p in found[0]["populations"]] == ["Gauges"]


def test_missing_root_yields_nothing(tmp_path):
    assert catchments(tmp_path / "absent") == []


def test_summary_counts_only_populated_catchments(tmp_path):
    _catchment(tmp_path, "thames", property=[{}, {}])
    (tmp_path / "rhine").mkdir()
    totals = summary(catchments(tmp_path))
    assert totals == {"catchments": 2, "populated": 1, "records": 2,
                      "last_built": totals["last_built"]}
    assert totals["last_built"]


# --- the document -----------------------------------------------------------

def test_document_states_the_weaknesses_it_monitors():
    model = _model(model_weaknesses=[
        {"item_id": "MW-001", "description": "Short records", "impact": "Medium"}])
    tex = build_monitoring_tex(model, SETTINGS, AS_OF, found=[])
    assert "MW-001" in tex
    assert "Short records" in tex


def test_document_prints_the_monitoring_trigger_for_a_limitation():
    """The trigger is the monitoring rule, printed even though nothing can breach
    it yet — it is what the document will report against in production."""
    model = _model(limitations=[
        {"item_id": "LM-001", "description": "Thames only",
         "impact": "High", "monitoring_trigger": "Portfolio outside catchment"}])
    tex = build_monitoring_tex(model, SETTINGS, AS_OF, found=[])
    assert "Portfolio outside catchment" in tex


def test_document_says_so_when_nothing_is_recorded():
    """Absent material is stated, not omitted: a reader must be able to see that
    no weaknesses are recorded, which an omitted section would hide."""
    tex = build_monitoring_tex(_model(), SETTINGS, AS_OF, found=[])
    assert tex.count("None recorded") == 2


def test_document_reports_an_empty_estate_without_claiming_activity():
    # ``configured`` is stated rather than left to the environment: unset, it
    # resolves the producing repo's portfolio directory off disk, so the estate
    # section a checkout gets depends on whether that sibling repo is present.
    tex = build_monitoring_tex(_model(), SETTINGS, AS_OF, found=[], configured=True)
    assert "\\textbf{0} of \\textbf{0} catchments" in tex
    assert "never" in tex


def test_document_reports_observed_portfolio_activity(tmp_path):
    _catchment(tmp_path, "thames", property=[{}, {}], gauge=[{}])
    tex = build_monitoring_tex(_model(), SETTINGS, AS_OF,
                               found=catchments(tmp_path), configured=True)
    assert "thames" in tex
    assert "\\textbf{1} of \\textbf{1} catchments" in tex
    assert "\\textbf{3}" in tex


def test_document_is_explicit_that_portfolios_are_not_client_business():
    """The whole document rests on this distinction; if it ever stops being said
    the report starts reading as production assurance it cannot give."""
    tex = build_monitoring_tex(_model(), SETTINGS, AS_OF, found=[])
    assert "not client business" in tex


def test_unrecognised_payload_shape_counts_as_no_records(tmp_path):
    """A portfolio file that is neither a list nor an object holds no population.
    Reporting a count for it would invent activity that never happened."""
    _catchment(tmp_path, "thames")
    (tmp_path / "thames" / "property.json").write_text(json.dumps("not a portfolio"))
    assert catchments(tmp_path)[0]["records"] == 0


def test_document_names_a_catchment_that_holds_no_portfolio(tmp_path):
    """The empty-catchment row must carry the standing statement, not a blank
    cell: a blank reads as missing data rather than as a deliberate observation."""
    (tmp_path / "rhine").mkdir()
    tex = build_monitoring_tex(_model(), SETTINGS, AS_OF,
                               found=catchments(tmp_path), configured=True)
    assert "rhine" in tex
    assert "No portfolio has been generated" in tex


def test_render_compiles_the_document_to_pdf(monkeypatch):
    """The render entry point wires the LaTeX through the shared compiler; the
    compile itself is stubbed so the test does not depend on a TeX install."""
    from src.governance.monitoring import report as module

    captured = {}

    def _fake_compile(tex, assets=None):
        captured["tex"] = tex
        return b"%PDF stub"

    monkeypatch.setattr(module.pack, "compile_tex", _fake_compile)
    monkeypatch.setattr(module, "logo_asset", lambda settings: {})
    pdf = module.render_monitoring_pdf(_model(), SETTINGS, AS_OF, found=[])
    assert pdf == b"%PDF stub"
    assert "Ongoing Monitoring Report" in captured["tex"]


def test_unconfigured_source_is_reported_as_such_not_as_an_empty_estate():
    """"We never looked" and "we looked and found nothing" are different findings.
    An adopter who has not pointed the platform at a generator must be told so,
    not handed a document reporting nought catchments as though that were news."""
    tex = build_monitoring_tex(_model(), SETTINGS, AS_OF, found=[], configured=False)
    assert "No portfolio source is configured" in tex
    assert "catchments" not in tex.split("Monitoring position")[0].split(
        "Portfolio activity")[1]


def test_configured_but_empty_source_still_reports_the_estate():
    tex = build_monitoring_tex(_model(), SETTINGS, AS_OF, found=[], configured=True)
    assert "No portfolio source is configured" not in tex
    assert "\\textbf{0} of \\textbf{0} catchments" in tex


def test_source_presence_follows_the_configured_location(tmp_path):
    from src.governance.monitoring.portfolio import source_present
    assert source_present(tmp_path) is True
    assert source_present(tmp_path / "absent") is False
