from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..database import db_dependency
from ..models import Item, Teacher, PrintingRecord, IssueRecord, ReturnRecord, DocumentRecord
from ..security import require_permission, CurrentUser

router = APIRouter(prefix="/api/reports", tags=["reports"])

REPORT_TYPES = [
    "Inventory Report", "Low Stock Report", "Teacher Report",
    "Printing Report", "Issue Report", "Return Report", "Pending Documents Report",
]


def _build(report_type: str, db: Session) -> tuple[list[str], list[list]]:
    if report_type == "Inventory Report":
        headers = ["ID", "Barcode", "Category", "Name", "Qty", "Min Qty", "Unit", "Status"]
        rows = [[i.id, i.barcode, i.category.name if i.category else "-", i.name,
                 i.current_quantity, i.minimum_quantity, i.unit, i.status]
                for i in db.query(Item).all()]
    elif report_type == "Low Stock Report":
        headers = ["ID", "Name", "Category", "Current Qty", "Minimum Qty"]
        rows = [[i.id, i.name, i.category.name if i.category else "-", i.current_quantity, i.minimum_quantity]
                for i in db.query(Item).all() if i.is_low_stock]
    elif report_type == "Teacher Report":
        headers = ["ID", "Employee ID", "Name", "Department", "Designation", "Status"]
        rows = [[t.id, t.employee_id, t.name, t.department, t.designation, t.status]
                for t in db.query(Teacher).all()]
    elif report_type == "Printing Report":
        headers = ["ID", "Teacher", "Document", "Mode", "Pages", "Copies", "Cost", "Date"]
        rows = [[p.id, p.teacher_name, p.document_name, p.color_mode, p.pages, p.copies,
                 p.cost, p.print_date] for p in db.query(PrintingRecord).all()]
    elif report_type == "Issue Report":
        headers = ["ID", "Teacher", "Item", "Qty", "Issue Date", "Status"]
        rows = [[r.id, r.teacher.name if r.teacher else "-", r.item.name if r.item else "-",
                 r.quantity, r.issue_date, r.status] for r in db.query(IssueRecord).all()]
    elif report_type == "Return Report":
        headers = ["Issue ID", "Returned Qty", "Return Date", "Condition", "Late?"]
        rows = [[rr.issue_id, rr.returned_quantity, rr.return_date, rr.condition, "Yes" if rr.is_late else "No"]
                for rr in db.query(ReturnRecord).all()]
    elif report_type == "Pending Documents Report":
        headers = ["ID", "Type", "Title", "Department", "Received Date"]
        rows = [[d.id, d.document_type, d.title, d.department or "-", d.received_date]
                for d in db.query(DocumentRecord).filter(DocumentRecord.status == "Pending").all()]
    else:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown report type")
    return headers, [[str(c) for c in row] for row in rows]


@router.get("/types")
def list_report_types(_u: CurrentUser = Depends(require_permission("view_reports"))):
    return REPORT_TYPES


@router.get("/{report_type}")
def get_report(report_type: str, db: Session = Depends(db_dependency),
                _u: CurrentUser = Depends(require_permission("view_reports"))):
    headers, rows = _build(report_type, db)
    return {"headers": headers, "rows": rows}


@router.get("/{report_type}/export/csv")
def export_csv(report_type: str, db: Session = Depends(db_dependency),
                _u: CurrentUser = Depends(require_permission("view_reports"))):
    headers, rows = _build(report_type, db)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    writer.writerows(rows)
    filename = report_type.lower().replace(" ", "_") + ".csv"
    return Response(content=buf.getvalue(), media_type="text/csv",
                     headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/{report_type}/export/xlsx")
def export_xlsx(report_type: str, db: Session = Depends(db_dependency),
                 _u: CurrentUser = Depends(require_permission("view_reports"))):
    import openpyxl
    headers, rows = _build(report_type, db)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = report_type[:31]
    ws.append(headers)
    for row in rows:
        ws.append(row)
    for col_cells in ws.columns:
        max_len = max((len(str(c.value)) for c in col_cells if c.value is not None), default=10)
        ws.column_dimensions[col_cells[0].column_letter].width = min(max(max_len + 2, 10), 40)
    buf = io.BytesIO()
    wb.save(buf)
    filename = report_type.lower().replace(" ", "_") + ".xlsx"
    return Response(content=buf.getvalue(),
                     media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/{report_type}/export/pdf")
def export_pdf(report_type: str, db: Session = Depends(db_dependency),
                _u: CurrentUser = Depends(require_permission("view_reports"))):
    import datetime as dt
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from .. import config

    headers, rows = _build(report_type, db)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=25 * mm, bottomMargin=18 * mm)
    styles = getSampleStyleSheet()
    primary_dark = colors.HexColor("#023E47")
    title_style = ParagraphStyle("Title2", parent=styles["Title"], textColor=primary_dark, fontSize=18)
    sub_style = ParagraphStyle("Sub2", parent=styles["Normal"], textColor=colors.grey, fontSize=9)

    elements = [
        Paragraph(config.ORG_NAME, sub_style),
        Paragraph(report_type, title_style),
        Paragraph(f"Generated on {dt.datetime.now().strftime('%d-%b-%Y %I:%M %p')}", sub_style),
        Spacer(1, 14),
    ]
    table = Table([headers] + rows, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), primary_dark),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EAF4F5")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(table)
    doc.build(elements)

    filename = report_type.lower().replace(" ", "_") + ".pdf"
    return Response(content=buf.getvalue(), media_type="application/pdf",
                     headers={"Content-Disposition": f'attachment; filename="{filename}"'})
