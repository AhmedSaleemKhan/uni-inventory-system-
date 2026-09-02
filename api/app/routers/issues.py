from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import db_dependency
from ..models import IssueRecord, ReturnRecord, Teacher, Item
from ..schemas import IssueIn, IssueOut, ReturnIn, ReturnOut
from ..security import require_permission, log_audit, CurrentUser

router = APIRouter(tags=["issues"])


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
