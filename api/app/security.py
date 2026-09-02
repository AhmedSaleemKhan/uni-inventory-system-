"""
app/security.py
bcrypt password hashing, JWT issuing/verification, and FastAPI
dependencies for "who is logged in" and "are they allowed to do this".
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from . import config
from .database import db_dependency
from .models import User
from sqlalchemy.orm import Session

_bearer = HTTPBearer(auto_error=False)


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "full_name": user.full_name,
        "exp": dt.datetime.utcnow() + dt.timedelta(minutes=config.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


@dataclass
class CurrentUser:
    id: int
    username: str
    full_name: str
    role: str


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    return CurrentUser(
        id=int(payload["sub"]),
        username=payload["username"],
        full_name=payload["full_name"],
        role=payload["role"],
    )


def require_permission(permission_key: str):
    """Returns a FastAPI dependency that 403s unless the caller's role has this permission."""

    def _check(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not config.has_permission(user.role, permission_key):
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Role '{user.role}' cannot '{permission_key}'")
        return user

    return _check


def log_audit(db: Session, user_id: Optional[int], action: str, entity: Optional[str] = None,
              entity_id: Optional[int] = None, details: Optional[str] = None) -> None:
    from .models import AuditLog
    db.add(AuditLog(user_id=user_id, action=action, entity=entity, entity_id=entity_id, details=details))
