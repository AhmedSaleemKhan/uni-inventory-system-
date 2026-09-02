"""
utils/pdf_reports.py
ReportLab-based PDF generation: issue receipts, and tabular reports
(inventory, teachers, printing, issues, returns, purchases, suppliers).
"""

from __future__ import annotations

import datetime as dt
from typing import Sequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)

import config

PRIMARY = colors.HexColor(config.THEME_PRIMARY)
PRIMARY_DARK = colors.HexColor(config.THEME_PRIMARY_DARK)


def _header_style():
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "UAIMSTitle", parent=styles["Title"], textColor=PRIMARY_DARK, fontSize=18
    )
    sub_style = ParagraphStyle(
        "UAIMSSub", parent=styles["Normal"], textColor=colors.grey, fontSize=9
    )
    return styles, title_style, sub_style


def generate_issue_receipt(data: dict, output_path: str) -> str:
    """Generate a single-page issue receipt PDF."""
    doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=30 * mm, bottomMargin=20 * mm)
    styles, title_style, sub_style = _header_style()
    elements = []

    elements.append(Paragraph(f"{config.ORG_NAME} — Inventory Issue Receipt", title_style))
    elements.append(Paragraph(f"Generated on {dt.datetime.now().strftime('%d-%b-%Y %I:%M %p')}", sub_style))
    elements.append(Spacer(1, 14))

    rows = [
        ["Receipt No.", str(data.get("id", "-"))],
        ["Teacher", data.get("teacher", "-")],
        ["Department", data.get("department", "-")],
        ["Item Issued", data.get("item", "-")],
        ["Quantity", str(data.get("quantity", "-"))],
        ["Issue Date", data.get("issue_date", "-")],
        ["Issued By", data.get("issued_by", "-")],
        ["Expected Return Date", data.get("expected_return", "-")],
        ["Remarks", data.get("remarks", "-")],
    ]
    table = Table(rows, colWidths=[150, 300])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), PRIMARY),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("Received By: ____________________________", styles["Normal"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Store Keeper Signature: ____________________________", styles["Normal"]))

    doc.build(elements)
    return output_path


def generate_tabular_report(title: str, headers: Sequence[str], rows: Sequence[Sequence],
                             output_path: str, subtitle: str = "") -> str:
    """Generate a generic tabular PDF report (used across all Reports module exports)."""
    doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=25 * mm, bottomMargin=18 * mm)
    styles, title_style, sub_style = _header_style()
    elements = []

    elements.append(Paragraph(f"{config.ORG_NAME}", sub_style))
    elements.append(Paragraph(title, title_style))
    if subtitle:
        elements.append(Paragraph(subtitle, sub_style))
    elements.append(Paragraph(f"Generated on {dt.datetime.now().strftime('%d-%b-%Y %I:%M %p')}", sub_style))
    elements.append(Spacer(1, 14))

    table_data = [list(headers)] + [list(map(str, row)) for row in rows]
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EAF4F5")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(table)

    doc.build(elements)
    return output_path
