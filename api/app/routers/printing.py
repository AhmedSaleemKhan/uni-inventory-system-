from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import db_dependency
from ..models import PrintingRecord, Teacher
from ..schemas import PrintingIn, PrintingOut
from ..security import require_permission, log_audit, CurrentUser

router = APIRouter(prefix="/api/printing", tags=["printing"])

COST_PER_PAGE_BW = 5.0
COST_PER_PAGE_COLOR = 15.0


@router.get("", response_model=list[PrintingOut])
def list_printing(db: Session = Depends(db_dependency), _u: CurrentUser = Depends(require_permission("manage_printing"))):
    return db.query(PrintingRecord).order_by(PrintingRecord.id.desc()).all()


@router.post("", response_model=PrintingOut)
def create_printing(payload: PrintingIn, db: Session = Depends(db_dependency),
                     user: CurrentUser = Depends(require_permission("manage_printing"))):
    per_page = COST_PER_PAGE_COLOR if payload.color_mode == "Color" else COST_PER_PAGE_BW
    cost = payload.pages * payload.copies * per_page
    teacher = db.query(Teacher).filter(Teacher.name == payload.teacher).first() if payload.teacher else None

    record = PrintingRecord(
        teacher_id=teacher.id if teacher else None,
        teacher_name=payload.teacher if payload.teacher else "Walk-in / Office",
        department=payload.department, course=payload.course, document_name=payload.document_name,
        color_mode=payload.color_mode, side_mode=payload.side_mode, pages=payload.pages, copies=payload.copies,
        cost=cost, printed_by=user.full_name, print_date=dt.date.today(), status="Completed",
    )
    db.add(record)
    db.flush()
    log_audit(db, user.id, "PRINTING_JOB_CREATED", entity="PrintingRecord", entity_id=record.id)
    db.refresh(record)
    return record
