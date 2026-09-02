from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import db_dependency
from ..models import Teacher
from ..schemas import TeacherIn, TeacherOut
from ..security import require_permission, log_audit, CurrentUser
from ..helpers import generate_employee_id

router = APIRouter(prefix="/api/teachers", tags=["teachers"])


@router.get("", response_model=list[TeacherOut])
def list_teachers(db: Session = Depends(db_dependency), _u: CurrentUser = Depends(require_permission("view_dashboard"))):
    return db.query(Teacher).order_by(Teacher.id.desc()).all()


@router.post("", response_model=TeacherOut)
def create_teacher(payload: TeacherIn, db: Session = Depends(db_dependency),
                    user: CurrentUser = Depends(require_permission("manage_teachers"))):
    teacher = Teacher(employee_id=generate_employee_id(), **payload.model_dump())
    db.add(teacher)
    db.flush()
    log_audit(db, user.id, "TEACHER_SAVED", entity="Teacher", entity_id=teacher.id)
    db.refresh(teacher)
    return teacher


@router.put("/{teacher_id}", response_model=TeacherOut)
def update_teacher(teacher_id: int, payload: TeacherIn, db: Session = Depends(db_dependency),
                    user: CurrentUser = Depends(require_permission("manage_teachers"))):
    teacher = db.get(Teacher, teacher_id)
    if not teacher:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Teacher not found")
    for key, value in payload.model_dump().items():
        setattr(teacher, key, value)
    db.flush()
    log_audit(db, user.id, "TEACHER_SAVED", entity="Teacher", entity_id=teacher_id)
    db.refresh(teacher)
    return teacher


@router.delete("/{teacher_id}")
def delete_teacher(teacher_id: int, db: Session = Depends(db_dependency),
                    user: CurrentUser = Depends(require_permission("manage_teachers"))):
    teacher = db.get(Teacher, teacher_id)
    if not teacher:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Teacher not found")
    try:
        db.delete(teacher)
        db.flush()
    except IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT,
                             "This teacher cannot be deleted because they have existing issue, printing, or document records.")
    log_audit(db, user.id, "TEACHER_DELETED", entity="Teacher", entity_id=teacher_id)
    return {"ok": True}
