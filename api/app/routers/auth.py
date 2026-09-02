from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import db_dependency
from ..models import User, LoginHistory
from ..schemas import LoginIn, LoginOut, MeOut, ChangePasswordIn
from ..security import verify_password, hash_password, create_access_token, get_current_user, CurrentUser, log_audit

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn, db: Session = Depends(db_dependency)):
    user = db.query(User).filter(User.username == payload.username.strip()).first()

    if user is None or not verify_password(payload.password, user.password_hash):
        if user is not None:
            db.add(LoginHistory(user_id=user.id, success=False))
        log_audit(db, user.id if user else None, "LOGIN_FAILED", details=f"username={payload.username}")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password.")

    if not user.is_active:
        db.add(LoginHistory(user_id=user.id, success=False))
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been deactivated. Contact your administrator.")

    user.last_login = dt.datetime.now()
    db.add(LoginHistory(user_id=user.id, success=True))
    log_audit(db, user.id, "LOGIN_SUCCESS", details=f"username={payload.username}")
    db.flush()

    token = create_access_token(user)
    return LoginOut(
        token=token,
        user=MeOut(id=user.id, username=user.username, full_name=user.full_name,
                    role=user.role, must_change_password=user.must_change_password),
    )


@router.get("/me", response_model=MeOut)
def me(current: CurrentUser = Depends(get_current_user), db: Session = Depends(db_dependency)):
    user = db.get(User, current.id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return MeOut(id=user.id, username=user.username, full_name=user.full_name,
                 role=user.role, must_change_password=user.must_change_password)


@router.post("/change-password")
def change_password(payload: ChangePasswordIn, current: CurrentUser = Depends(get_current_user),
                     db: Session = Depends(db_dependency)):
    if len(payload.new_password) < 6:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password must be at least 6 characters long.")
    user = db.get(User, current.id)
    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = False
    log_audit(db, current.id, "PASSWORD_CHANGED")
    return {"ok": True}
