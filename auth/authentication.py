"""
auth/authentication.py
Secure authentication: bcrypt hashing, login/logout, session state,
and audit / login-history logging.
"""

from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from typing import Optional

import bcrypt

from database.database import get_session
from database.models import User, LoginHistory, AuditLog

logger = logging.getLogger("uaims.auth")


@dataclass
class SessionUser:
    """In-memory representation of the currently authenticated user."""
    id: int
    username: str
    full_name: str
    role: str
    must_change_password: bool

    def has_role(self, *roles: str) -> bool:
        return self.role in roles


class SessionManager:
    """Simple in-memory session holder (single desktop session)."""
    _current_user: Optional[SessionUser] = None
    _login_history_id: Optional[int] = None

    @classmethod
    def login(cls, user: SessionUser, login_history_id: Optional[int]) -> None:
        cls._current_user = user
        cls._login_history_id = login_history_id

    @classmethod
    def logout(cls) -> None:
        if cls._login_history_id is not None:
            with get_session() as session:
                record = session.get(LoginHistory, cls._login_history_id)
                if record:
                    record.logout_time = dt.datetime.now()
        cls._current_user = None
        cls._login_history_id = None

    @classmethod
    def current_user(cls) -> Optional[SessionUser]:
        return cls._current_user

    @classmethod
    def is_authenticated(cls) -> bool:
        return cls._current_user is not None


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def authenticate(username: str, password: str) -> tuple[Optional[SessionUser], str]:
    """
    Attempt to authenticate a user.
    Returns (SessionUser or None, message).
    """
    with get_session() as session:
        user = session.query(User).filter(User.username == username.strip()).first()

        if user is None or not verify_password(password, user.password_hash):
            _record_login_attempt(session, user.id if user else None, success=False)
            log_audit(None, "LOGIN_FAILED", details=f"username={username}")
            return None, "Invalid username or password."

        if not user.is_active:
            _record_login_attempt(session, user.id, success=False)
            return None, "This account has been deactivated. Contact your administrator."

        user.last_login = dt.datetime.now()
        history_id = _record_login_attempt(session, user.id, success=True)

        session_user = SessionUser(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            must_change_password=user.must_change_password,
        )
        session.flush()

    SessionManager.login(session_user, history_id)
    log_audit(session_user.id, "LOGIN_SUCCESS", details=f"username={username}")
    return session_user, "Login successful."


def _record_login_attempt(session, user_id: Optional[int], success: bool) -> Optional[int]:
    if user_id is None:
        return None
    record = LoginHistory(user_id=user_id, success=success)
    session.add(record)
    session.flush()
    return record.id


def change_password(user_id: int, new_password: str) -> None:
    with get_session() as session:
        user = session.get(User, user_id)
        if user is None:
            raise ValueError("User not found.")
        user.password_hash = hash_password(new_password)
        user.must_change_password = False
    log_audit(user_id, "PASSWORD_CHANGED")


def log_audit(user_id: Optional[int], action: str, entity: Optional[str] = None,
              entity_id: Optional[int] = None, details: Optional[str] = None) -> None:
    try:
        with get_session() as session:
            session.add(AuditLog(
                user_id=user_id, action=action, entity=entity,
                entity_id=entity_id, details=details,
            ))
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to write audit log: %s", exc)
