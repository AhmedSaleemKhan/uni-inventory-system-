from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import db_dependency
from ..models import User
from ..schemas import UserIn, UserOut
from ..security import require_permission, log_audit, hash_password, CurrentUser

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(db_dependency), _u: CurrentUser = Depends(require_permission("manage_users"))):
    return db.query(User).order_by(User.id.desc()).all()


@router.post("", response_model=UserOut)
def create_user(payload: UserIn, db: Session = Depends(db_dependency),
                 user: CurrentUser = Depends(require_permission("manage_users"))):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "A user with this username already exists.")
    new_user = User(username=payload.username, password_hash=hash_password(payload.password or "password123"),
                     full_name=payload.full_name, role=payload.role, email=payload.email, phone=payload.phone,
                     must_change_password=True)
    db.add(new_user)
    db.flush()
    log_audit(db, user.id, "USER_CREATED", entity="User", entity_id=new_user.id)
    db.refresh(new_user)
    return new_user


@router.post("/{user_id}/toggle-active", response_model=UserOut)
def toggle_active(user_id: int, db: Session = Depends(db_dependency),
                   user: CurrentUser = Depends(require_permission("manage_users"))):
    if user_id == user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot deactivate your own account.")
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    target.is_active = not target.is_active
    db.flush()
    log_audit(db, user.id, "USER_TOGGLED_ACTIVE", entity="User", entity_id=user_id)
    db.refresh(target)
    return target


@router.post("/{user_id}/reset-password")
def reset_password(user_id: int, db: Session = Depends(db_dependency),
                    user: CurrentUser = Depends(require_permission("manage_users"))):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    target.password_hash = hash_password("password123")
    target.must_change_password = True
    log_audit(db, user.id, "USER_PASSWORD_RESET", entity="User", entity_id=user_id)
    return {"ok": True, "message": "Password reset to 'password123'. User must change it at next login."}
