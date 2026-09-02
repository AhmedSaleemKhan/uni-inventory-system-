"""
auth/permissions.py
Runtime permission-checking helpers bound to the currently logged-in user.
"""

from __future__ import annotations
from auth.roles import PERMISSIONS


def has_permission(role: str, permission_key: str) -> bool:
    """Check whether a role is allowed to perform the given permission."""
    allowed_roles = PERMISSIONS.get(permission_key, [])
    return role in allowed_roles


class PermissionDenied(Exception):
    """Raised when a user attempts an action they are not authorized for."""
    pass


def require_permission(role: str, permission_key: str) -> None:
    if not has_permission(role, permission_key):
        raise PermissionDenied(f"Role '{role}' is not authorized for '{permission_key}'.")
