from __future__ import annotations

import datetime as dt
import io
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..database import db_dependency
from ..models import IssueRecord, ReturnRecord, Teacher, Item
from ..schemas import IssueIn, IssueOut, ReturnIn, ReturnOut
from ..security import require_permission, log_audit, CurrentUser

router = APIRouter(tags=["issues"])

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


def _issue_out(r: IssueRecord) -> IssueOut:
    return IssueOut(id=r.id, teacher=r.teacher.name if r.teacher else "-", item=r.item.name if r.item else "-",
                     quantity=r.quantity, issue_date=r.issue_date, department=r.department,
                     return_required=r.return_required, expected_return_date=r.expected_return_date, status=r.status)


@router.get("/api/issues", response_model=list[IssueOut])
def list_issues(db: Session = Depends(db_dependency), _u: CurrentUser = Depends(require_permission("issue_items"))):
    return [_issue_out(r) for r in db.query(IssueRecord).order_by(IssueRecord.id.desc()).all()]


@router.post("/api/issues", response_model=IssueOut)
def create_issue(payload: IssueIn, db: Session = Depends(db_dependency),
                  user: CurrentUser = Depends(require_permission("issue_items"))):
    teacher = db.query(Teacher).filter(Teacher.name == payload.teacher).first()
    item = db.query(Item).filter(Item.name == payload.item).first()
    if not teacher or not item:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Selected teacher or item not found.")
    if item.current_quantity < payload.quantity:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Only {item.current_quantity} units of '{item.name}' available.")

    record = IssueRecord(
        teacher_id=teacher.id, item_id=item.id, quantity=payload.quantity, issue_date=dt.date.today(),
        issue_time=dt.datetime.now().strftime("%I:%M %p"), issued_by=user.full_name,
        department=payload.department or teacher.department, remarks=payload.remarks,
        return_required=payload.return_required,
        expected_return_date=payload.expected_return_date if payload.return_required else None,
        status="Issued",
    )
    item.current_quantity -= payload.quantity
    db.add(record)
    db.flush()
    log_audit(db, user.id, "ITEM_ISSUED", entity="IssueRecord", entity_id=record.id)
    db.refresh(record)
    return _issue_out(record)


@router.get("/api/issues/{issue_id}/requisition")
def generate_requisition(issue_id: int, db: Session = Depends(db_dependency),
                          _u: CurrentUser = Depends(require_permission("issue_items"))):
    """Render the Internal Department Requisition form (Store Section) for one
    issue record as a PDF, matching the institute's paper template exactly."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable,
    )
    from .. import config

    record = db.get(IssueRecord, issue_id)
    if not record:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Issue record not found.")

    teacher = record.teacher
    item = record.item
    dark = colors.HexColor("#023E47")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=14 * mm, bottomMargin=16 * mm,
                             leftMargin=18 * mm, rightMargin=18 * mm)
    styles = getSampleStyleSheet()

    org_style = ParagraphStyle("ReqOrg", parent=styles["Normal"], alignment=TA_CENTER,
                                fontName="Helvetica-Bold", fontSize=12.5, textColor=dark, leading=15)
    addr_style = ParagraphStyle("ReqAddr", parent=styles["Normal"], alignment=TA_CENTER,
                                 fontSize=9, textColor=colors.grey)
    dept_style = ParagraphStyle("ReqDept", parent=styles["Normal"], fontSize=10.5,
                                 fontName="Helvetica-Bold", spaceAfter=4)
    title_style = ParagraphStyle("ReqTitle", parent=styles["Normal"], alignment=TA_CENTER,
                                  fontName="Times-Bold", fontSize=14, spaceBefore=4, spaceAfter=14)
    field_style = ParagraphStyle("ReqField", parent=styles["Normal"], fontSize=10.5, spaceAfter=7)
    sign_style = ParagraphStyle("ReqSign", parent=styles["Normal"], fontSize=10.5)

    elements = []

    logo_path = ASSETS_DIR / "paf_iast_logo.jpg"
    if logo_path.exists():
        logo = Image(str(logo_path), width=18 * mm, height=18 * mm)
        logo.hAlign = "CENTER"
        elements.append(logo)
        elements.append(Spacer(1, 4))
    elements.append(Paragraph(config.ORG_FULL_NAME, org_style))
    elements.append(Paragraph(config.ORG_ADDRESS, addr_style))
    elements.append(Spacer(1, 6))
    elements.append(HRFlowable(width="100%", thickness=1.2, color=dark))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Department of {teacher.department if teacher else '-'}", dept_style))
    elements.append(Paragraph("<u>Store Section (Form for Internal Department Requisition)</u>", title_style))

    elements.append(Paragraph(f"Date: {record.issue_date.strftime('%d-%b-%Y')}", field_style))
    elements.append(Paragraph(f"Serial No: {record.id}", field_style))
    elements.append(Paragraph(f"Name Of Staff / Faculty Member: {teacher.name if teacher else '-'}", field_style))
    elements.append(Spacer(1, 6))

    header_style = ParagraphStyle("ReqTblHead", parent=styles["Normal"], fontName="Helvetica-Bold",
                                   fontSize=9, alignment=TA_CENTER, textColor=colors.white, leading=11)
    cell_style = ParagraphStyle("ReqTblCell", parent=styles["Normal"], fontSize=9.5)

    table_data = [[
        Paragraph("S.No.", header_style), Paragraph("Description", header_style),
        Paragraph("Quantity", header_style), Paragraph("Only use for Store Section", header_style),
    ], [
        "1", Paragraph(item.name if item else "-", cell_style), str(record.quantity), "",
    ]]
    for i in range(2, 21):
        table_data.append([str(i), "", "", ""])

    col_ratio = [718, 3736, 1060, 4477]
    col_widths = [doc.width * r / sum(col_ratio) for r in col_ratio]

    req_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    req_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), dark),
        ("GRID", (0, 0), (-1, -1), 0.6, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("FONTSIZE", (0, 1), (-1, -1), 9.5),
        ("TOPPADDING", (0, 1), (-1, -1), 3.4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 3.4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5FAFA")]),
    ]))
    elements.append(req_table)
    elements.append(Spacer(1, 16))

    sign_table = Table(
        [[Paragraph("Store In-Charge: ______________________________", sign_style),
          Paragraph("HOD: ______________________________", sign_style)]],
        colWidths=[doc.width / 2, doc.width / 2],
    )
    sign_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    elements.append(sign_table)
    elements.append(Spacer(1, 16))
    elements.append(Paragraph("Received By: ______________________________", sign_style))

    doc.build(elements)

    filename = f"internal_requisition_{record.id}.pdf"
    return Response(content=buf.getvalue(), media_type="application/pdf",
                     headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/api/returns", response_model=list[ReturnOut])
def list_returnable(db: Session = Depends(db_dependency), _u: CurrentUser = Depends(require_permission("return_items"))):
    today = dt.date.today()
    pending = db.query(IssueRecord).filter(IssueRecord.return_required == True, IssueRecord.status == "Issued").all()  # noqa: E712
    for r in pending:
        if r.expected_return_date and r.expected_return_date < today:
            r.status = "Overdue"
    db.flush()

    records = db.query(IssueRecord).filter(IssueRecord.return_required == True).order_by(IssueRecord.id.desc()).all()  # noqa: E712
    return [
        ReturnOut(issue_id=r.id, teacher=r.teacher.name if r.teacher else "-", item=r.item.name if r.item else "-",
                  quantity=r.quantity, issue_date=r.issue_date, expected_return_date=r.expected_return_date, status=r.status)
        for r in records
    ]


@router.post("/api/returns/{issue_id}")
def record_return(issue_id: int, payload: ReturnIn, db: Session = Depends(db_dependency),
                   user: CurrentUser = Depends(require_permission("return_items"))):
    record = db.get(IssueRecord, issue_id)
    if not record or record.status == "Returned":
        raise HTTPException(status.HTTP_409_CONFLICT, "This record is already returned or invalid.")

    return_date = dt.date.today()
    is_late = bool(record.expected_return_date and return_date > record.expected_return_date)

    db.add(ReturnRecord(issue_id=record.id, returned_quantity=payload.returned_quantity, return_date=return_date,
                         condition=payload.condition, received_by=user.full_name, remarks=payload.remarks,
                         is_late=is_late))
    record.status = "Returned"
    if record.item and payload.condition != "Damaged":
        record.item.current_quantity += payload.returned_quantity

    log_audit(db, user.id, "ITEM_RETURNED", entity="ReturnRecord", entity_id=issue_id)
    return {"ok": True, "is_late": is_late}
