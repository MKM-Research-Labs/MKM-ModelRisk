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

"""Data retention policy and remediation guidance report sections."""

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table

from ._constants import GREEN, AMBER, RED, STALE_HOURS, RETENTION_DAYS, FAILURE_METADATA
from .collect import _compute_verdict
from .styles import _header_style, _section_rule


def _build_retention_policy(data: dict, story: list, S: dict):
    """Section 6: Data Retention Policy."""
    story.append(Paragraph("6. Data Retention Policy", S['h2']))
    _section_rule(story)

    story.append(Paragraph(
        "<b>Regulatory Requirement (FCA/PRA):</b> "
        "Data used in risk model calibration and pricing must be retained "
        "for a minimum period to support audit, backtesting, and regulatory "
        "review. The following policy applies to all data artefacts "
        "in the Physical Risk portfolio system.",
        S['body']))
    story.append(Spacer(1, 0.1 * inch))

    policy_data = [
        ['Data Category', 'Retention Period', 'Storage', 'Policy Basis'],
        ['Pipeline source data\n(gauge, property, mortgage)',
         f'{RETENTION_DAYS} days\n(minimum)',
         'data/input/<catchment>/',
         'FCA SYSC 9 — adequate records'],
        ['Model calibration outputs\n(hazard curves, stress models)',
         f'{RETENTION_DAYS} days\n(minimum)',
         'data/input/<catchment>/',
         'SS1/23 §5.7 — model outputs'],
        ['Trade blotter & PRS\n(pricing, counterparty data)',
         '5 years\n(minimum)',
         'data/input/<catchment>/prs/',
         'FCA COBS 9A — suitability records'],
        ['EOD snapshots\n(daily P&L, market state)',
         '5 years\n(minimum)',
         'data/input/<catchment>/blotter/eod/',
         'FCA SUP 17 — transaction reporting'],
        ['Lineage manifest\n(data_lineage.json)',
         f'{RETENTION_DAYS} days\n(minimum)',
         'data/',
         'BCBS 239 P6 — timeliness evidence'],
        ['Audit evidence\n(test reports, coverage)',
         '3 years\n(minimum)',
         'data/output/audit/',
         'SS1/23 §5.14 — validation evidence'],
        ['Classifier models\n(*.joblib, training summaries)',
         'Model lifetime\n+ 1 year',
         'data/input/<catchment>/classifiers/',
         'SR 11-7 — model inventory'],
    ]

    tbl = Table(policy_data,
                colWidths=[1.7 * inch, 1.2 * inch, 1.7 * inch, 1.9 * inch])
    tbl.setStyle(_header_style())
    story.append(tbl)

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        "<b>Implementation Notes:</b>", S['h3']))
    story.append(Paragraph(
        "&bull; The lineage manifest records SHA-256 hashes and timestamps "
        "for every pipeline execution, providing immutable evidence of "
        "data provenance.<br/>"
        "&bull; EOD snapshots include a full market state snapshot "
        "(hazard term structures, yield curve, gauge adjustments) enabling "
        "point-in-time reconstruction of risk calculations.<br/>"
        "&bull; The <i>--strict</i> CLI flag refuses pipeline execution if "
        "upstream data is stale, enforcing the staleness threshold of "
        f"{STALE_HOURS} hours.<br/>"
        "&bull; All data files use JSON format with structured schemas "
        "(CDM layer), enabling automated validation and migration.",
        S['body']))

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        "<b>BCBS 239 Principle 5/6 — Reproducibility:</b> "
        "The retention policy ensures that all data inputs, model outputs, "
        "and lineage records are preserved for a sufficient period to "
        "reproduce historical risk reports on demand, satisfying the BCBS 239 "
        "requirement for timely and accurate risk data aggregation.",
        S['body']))

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        "<b>Archival Procedure:</b> Pipeline data older than the retention "
        "period should be archived to a separate read-only store. The "
        "lineage manifest preserves the SHA-256 hash of archived data, "
        "enabling integrity verification on retrieval. Archival is currently "
        "a manual process; automated archival with configurable retention "
        "windows is on the development roadmap.",
        S['body']))


def _build_remediation(data: dict, story: list, S: dict):
    """Section 7: Remediation Guidance."""
    story.append(Paragraph("7. Remediation Guidance", S['h2']))
    _section_rule(story)

    chain = data['chain_result']
    lr = data.get('lineage_results', {})
    verdict = _compute_verdict(chain, lr)
    tests_failed = lr.get('failed', 0)
    tests_skipped = lr.get('skipped', 0)

    # Overall BCBS 239 assessment
    story.append(Paragraph(
        "<b>Overall BCBS 239 Data Lineage Assessment</b>", S['h3']))

    verdict_col = (GREEN if verdict == 'COMPLIANT' else
                   AMBER if verdict == 'PARTIALLY COMPLIANT' else RED)
    story.append(Paragraph(
        f"<b>Status: <font color='{verdict_col.hexval()}'>"
        f"{verdict}</font></b>", S['body']))
    story.append(Spacer(1, 0.08 * inch))

    # Strengths
    story.append(Paragraph(
        "<b>Strengths:</b> Complete pipeline topology with declared "
        "dependencies, SHA-256 hash-based provenance at every boundary, "
        f"automated staleness threshold ({STALE_HOURS}h), "
        "deterministic ID generation, data retention policy aligned with "
        "FCA/PRA requirements.",
        S['body']))
    story.append(Spacer(1, 0.06 * inch))

    # Weaknesses (only if any)
    weaknesses = []
    if chain.get('stale_steps'):
        weaknesses.append(
            f"{len(chain['stale_steps'])} stale-input failure(s): "
            f"{', '.join(chain['stale_steps'])}")
    if chain.get('missing_steps'):
        weaknesses.append(
            f"{len(chain['missing_steps'])} unrecorded step(s): "
            f"{', '.join(chain['missing_steps'])}")
    if tests_failed > 0:
        weaknesses.append(
            f"{tests_failed} reconciliation test failure(s)")
    if tests_skipped > 0:
        weaknesses.append(
            f"{tests_skipped} skipped check(s)")

    if weaknesses:
        story.append(Paragraph(
            "<b>Weaknesses:</b> " + '; '.join(weaknesses) + '.',
            S['body']))
        story.append(Spacer(1, 0.06 * inch))

    # Run-specific conclusion
    story.append(Spacer(1, 0.08 * inch))
    story.append(Paragraph(
        "<b>Run-Specific Conclusion</b>", S['h3']))

    if verdict == 'COMPLIANT':
        story.append(Paragraph(
            "All pipeline steps are recorded, content hashes are consistent, "
            "and all reconciliation tests pass. This run is suitable for "
            "regulatory risk reporting.",
            S['body']))
        return

    story.append(Paragraph(
        "<b>This run is not suitable for regulatory risk reporting</b> "
        "until the issues below are resolved and all checks pass.",
        S['body']))
    story.append(Spacer(1, 0.1 * inch))

    # Concrete remediation steps
    story.append(Paragraph(
        "<b>Remediation Steps</b>", S['h3']))

    steps = []
    if chain.get('missing_steps'):
        steps.append(
            f"<b>[P1 — High] Missing steps ({len(chain['missing_steps'])}):"
            f"</b> Run the pipeline for: "
            f"{', '.join(chain['missing_steps'])}. "
            f"Use <i>python app.py port</i> with the appropriate flags.")

    if chain.get('stale_steps'):
        steps.append(
            f"<b>[P1 — High] Stale data ({len(chain['stale_steps'])}):</b> "
            f"Regenerate: {', '.join(chain['stale_steps'])}. "
            f"Upstream inputs have changed since these steps were last run. "
            f"Use <i>python app.py port --strict</i> to enforce freshness.")

    if chain.get('details'):
        for step_name, issues in chain['details'].items():
            for issue in issues:
                steps.append(f"<b>[P2 — Medium] {step_name}:</b> {issue}")

    if tests_failed > 0:
        failures = lr.get('failures', [])
        for f in failures[:10]:
            name = f.get('name', 'unknown')
            meta = FAILURE_METADATA.get(name)
            if meta:
                steps.append(
                    f"<b>[P2 — Medium] {name} ({meta['principle']}):</b> "
                    f"{meta['remediation']}")

    steps.append(
        "<b>[P3 — Verify] Re-run validation:</b> Execute "
        "<i>python app.py test --audit</i> to regenerate this report and "
        "confirm all checks pass.")

    for step in steps:
        story.append(Paragraph(f"&bull; {step}", S['body']))
        story.append(Spacer(1, 0.06 * inch))
