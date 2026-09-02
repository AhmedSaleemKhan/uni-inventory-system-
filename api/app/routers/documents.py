from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import db_dependency
from ..models import DocumentRecord, Teacher
from ..schemas import DocumentIn, DocumentOut
from ..security import require_permission, log_audit, CurrentUser

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(db_dependency), _u: CurrentUser = Depends(require_permission("manage_documents"))):
    return db.query(DocumentRecord).order_by(DocumentRecord.id.desc()).all()


@router.post("", response_model=DocumentOut)
def create_document(payload: DocumentIn, db: Session = Depends(db_dependency),
                     user: CurrentUser = Depends(require_permission("manage_documents"))):
    teacher = db.query(Teacher).filter(Teacher.name == payload.submitted_by).first() if payload.submitted_by else None
    record = DocumentRecord(
        document_type=payload.document_type, title=payload.title, teacher_id=teacher.id if teacher else None,
        department=payload.department, submitted_by=payload.submitted_by, received_date=dt.date.today(),
        status=payload.status, remarks=payload.remarks,
    )
    db.add(record)
    db.flush()
    log_audit(db, user.id, "DOCUMENT_ADDED", entity="DocumentRecord", entity_id=record.id)
    db.refresh(record)
    return record


@router.post("/{document_id}/status/{new_status}", response_model=DocumentOut)
def update_status(document_id: int, new_status: str, db: Session = Depends(db_dependency),
                   user: CurrentUser = Depends(require_permission("manage_documents"))):
    record = db.get(DocumentRecord, document_id)
    if not record:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    if new_status not in ("Pending", "Received", "Approved", "Rejected"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid status")
    record.status = new_status
    if new_status == "Approved":
        record.approved_by = user.full_name
    db.flush()
    log_audit(db, user.id, f"DOCUMENT_{new_status.upper()}", entity="DocumentRecord", entity_id=document_id)
    db.refresh(record)
    return record
