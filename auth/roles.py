"""
auth/roles.py
Role definitions and the permission matrix for UAIMS.
"""

from __future__ import annotations
import config

# Each permission maps to the list of roles allowed to perform it.
PERMISSIONS: dict[str, list[str]] = {
    "view_dashboard": config.ALL_ROLES,
    "manage_inventory": [config.ROLE_SUPER_ADMIN, config.ROLE_ADMINISTRATOR, config.ROLE_STORE_KEEPER],
    "view_inventory": config.ALL_ROLES,
    "issue_items": [config.ROLE_SUPER_ADMIN, config.ROLE_ADMINISTRATOR, config.ROLE_STORE_KEEPER, config.ROLE_OFFICE_STAFF],
    "return_items": [config.ROLE_SUPER_ADMIN, config.ROLE_ADMINISTRATOR, config.ROLE_STORE_KEEPER, config.ROLE_OFFICE_STAFF],
    "manage_printing": [config.ROLE_SUPER_ADMIN, config.ROLE_ADMINISTRATOR, config.ROLE_PRINTING_STAFF],
    "manage_teachers": [config.ROLE_SUPER_ADMIN, config.ROLE_ADMINISTRATOR, config.ROLE_OFFICE_STAFF],
    "manage_documents": [config.ROLE_SUPER_ADMIN, config.ROLE_ADMINISTRATOR, config.ROLE_OFFICE_STAFF, config.ROLE_DEPARTMENT_STAFF],
    "manage_suppliers": [config.ROLE_SUPER_ADMIN, config.ROLE_ADMINISTRATOR, config.ROLE_STORE_KEEPER],
    "manage_purchases": [config.ROLE_SUPER_ADMIN, config.ROLE_ADMINISTRATOR, config.ROLE_STORE_KEEPER],
    "view_reports": [config.ROLE_SUPER_ADMIN, config.ROLE_ADMINISTRATOR, config.ROLE_OFFICE_STAFF, config.ROLE_STORE_KEEPER],
    "manage_users": [config.ROLE_SUPER_ADMIN, config.ROLE_ADMINISTRATOR],
    "manage_settings": [config.ROLE_SUPER_ADMIN, config.ROLE_ADMINISTRATOR],
    "manage_backup": [config.ROLE_SUPER_ADMIN],
}


def get_role_permissions(role: str) -> list[str]:
    """Return the list of permission keys granted to a given role."""
    return [perm for perm, roles in PERMISSIONS.items() if role in roles]
