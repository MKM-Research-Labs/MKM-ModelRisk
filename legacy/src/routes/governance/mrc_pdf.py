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

#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""MRC meeting pack PDF generation route."""

import io
from datetime import datetime

from flask import jsonify, send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from . import governance_bp
from ._helpers import _load_meetings


def _build_meeting_pdf(meeting):
    """Generate a meeting pack PDF and return it as a BytesIO buffer."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=25 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "MeetingTitle",
        parent=styles["Title"],
        fontSize=18,
        spaceAfter=6,
        textColor=colors.HexColor("#1565c0"),
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=13,
        spaceBefore=16,
        spaceAfter=8,
        textColor=colors.HexColor("#1565c0"),
        borderWidth=0,
        borderPadding=0,
    )
    body_style = ParagraphStyle(
        "MeetingBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=4,
    )
    small_style = ParagraphStyle(
        "SmallText",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#555555"),
    )

    def _styled_table(table_data, col_widths):
        """Create a table with standard MRC styling and trailing spacer."""
        t = Table(table_data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1565c0")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        return [t, Spacer(1, 8)]

    elements = []

    # Title
    elements.append(Paragraph(meeting.get("title", "MRC Meeting"), title_style))
    info_parts = []
    if meeting.get("date"):
        info_parts.append(f"Date: {meeting['date']}")
    if meeting.get("time"):
        info_parts.append(f"Time: {meeting['time']}")
    if meeting.get("location"):
        info_parts.append(f"Location: {meeting['location']}")
    if meeting.get("status"):
        info_parts.append(f"Status: {meeting['status']}")
    if meeting.get("chair"):
        info_parts.append(f"Chair: {meeting['chair']}")
    elements.append(Paragraph(" | ".join(info_parts), small_style))
    elements.append(Spacer(1, 10))

    # Participants
    participants = meeting.get("participants", [])
    if participants:
        elements.append(Paragraph("Participants", heading_style))
        table_data = [["Name", "Role", "Organisation", "Status"]]
        for p in participants:
            table_data.append([
                p.get("name", ""),
                p.get("role", ""),
                p.get("organisation", ""),
                p.get("status", ""),
            ])
        elements.extend(_styled_table(table_data, [45 * mm, 40 * mm, 45 * mm, 30 * mm]))

    # Agenda
    agenda = meeting.get("agenda", [])
    if agenda:
        elements.append(Paragraph("Agenda", heading_style))
        table_data = [["#", "Title", "Presenter", "Status"]]
        for a in agenda:
            table_data.append([
                str(a.get("item", "")),
                Paragraph(a.get("title", ""), body_style),
                a.get("presenter", ""),
                a.get("status", ""),
            ])
        elements.extend(_styled_table(table_data, [10 * mm, 95 * mm, 35 * mm, 25 * mm]))

    # Minutes
    minutes = meeting.get("minutes", [])
    if isinstance(minutes, list) and minutes:
        elements.append(Paragraph("Minutes", heading_style))
        for m in minutes:
            item_title = f"{m.get('item', '')}. {m.get('title', '')}"
            if m.get("presenter"):
                item_title += f" ({m['presenter']})"
            elements.append(Paragraph(f"<b>{item_title}</b>", body_style))
            text = (m.get("text", "") or "").replace("\n", "<br/>")
            if text:
                elements.append(Paragraph(text, small_style))
            elements.append(Spacer(1, 6))

    # Decisions
    decisions = meeting.get("decisions", [])
    if decisions:
        elements.append(Paragraph("Decisions", heading_style))
        table_data = [["ID", "Description", "Date"]]
        for d in decisions:
            table_data.append([
                d.get("id", ""),
                Paragraph(d.get("description", ""), body_style),
                d.get("date", ""),
            ])
        elements.extend(_styled_table(table_data, [15 * mm, 120 * mm, 25 * mm]))

    # Actions
    actions = meeting.get("actions", [])
    if actions:
        elements.append(Paragraph("Actions", heading_style))
        table_data = [["ID", "Action", "Owner", "Target", "Status"]]
        for a in actions:
            table_data.append([
                a.get("id", ""),
                Paragraph(a.get("description", ""), body_style),
                a.get("owner", ""),
                a.get("target_date", ""),
                a.get("status", ""),
            ])
        elements.extend(_styled_table(table_data, [15 * mm, 75 * mm, 30 * mm, 22 * mm, 20 * mm]))

    # Footer
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | MKM Research Labs — Model Risk Committee",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey),
    ))

    doc.build(elements)
    buf.seek(0)
    return buf


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/pdf", methods=["GET"])
def get_meeting_pdf(meeting_id):
    """Generate and serve a meeting pack PDF."""
    meetings = _load_meetings()
    meeting = next((m for m in meetings if m["id"] == meeting_id), None)
    if not meeting:
        return jsonify({"status": "error", "message": f"Meeting {meeting_id} not found"}), 404

    buf = _build_meeting_pdf(meeting)
    safe_title = meeting.get("title", "meeting").replace(" ", "_").lower()
    filename = f"mrc_{safe_title}_{meeting.get('date', 'undated')}.pdf"

    return send_file(
        buf,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=filename,
    )
