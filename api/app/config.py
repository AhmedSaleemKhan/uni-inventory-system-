"""
app/config.py
Central configuration for the UAIMS web backend. Reads DATABASE_URL from
the environment so the exact same code runs against a local SQLite file
(no setup needed) or a hosted Postgres database (Neon, Supabase, etc.) -
just set the env var, nothing else changes.
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
# No DATABASE_URL set -> local SQLite file next to this package. Vercel's
# serverless filesystem is read-only outside /tmp, so when frozen there we
# fall back to /tmp (ephemeral - fine only until DATABASE_URL is set to a
# real hosted database, which is the point: this unblocks "runs today").
_default_sqlite_path = "/tmp/uaims_web.db" if os.getenv("VERCEL") else "./uaims_web.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_default_sqlite_path}")

# A bare "postgresql://" (or Heroku-style "postgres://") URL - exactly what
# Neon/Supabase/etc. hand you to copy-paste - makes SQLAlchemy default to
# the psycopg2 driver. This project installs psycopg (v3) instead, so an
# unmodified URL fails at engine-creation time with "No module named
# 'psycopg2'" (crashing every request, since this runs at app startup).
# Rewriting the scheme to explicitly request psycopg makes the pasted URL
# work as-is instead of requiring anyone to know to edit it by hand.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len("postgres://"):]
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len("postgresql://"):]

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
APP_NAME = "UAIMS - University Administration Inventory & Office Management System"
ORG_NAME = os.getenv("ORG_NAME", "PAF-IAST")
ORG_FULL_NAME = os.getenv("ORG_FULL_NAME", "Pak-Austria Fachhochschule: Institute of Applied Sciences & Technology")
ORG_ADDRESS = os.getenv("ORG_ADDRESS", "Mang, Haripur, Khyber Pakhtunkhwa")

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"

CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]

# ---------------------------------------------------------------------------
# Roles & permissions (same matrix as the desktop app)
# ---------------------------------------------------------------------------
ROLE_SUPER_ADMIN = "Super Admin"
ROLE_ADMINISTRATOR = "Administrator"
ROLE_OFFICE_STAFF = "Office Staff"
ROLE_STORE_KEEPER = "Store Keeper"
ROLE_PRINTING_STAFF = "Printing Staff"
ROLE_DEPARTMENT_STAFF = "Department Staff"

ALL_ROLES = [
    ROLE_SUPER_ADMIN,
    ROLE_ADMINISTRATOR,
    ROLE_OFFICE_STAFF,
    ROLE_STORE_KEEPER,
    ROLE_PRINTING_STAFF,
    ROLE_DEPARTMENT_STAFF,
]

PERMISSIONS: dict[str, list[str]] = {
    "view_dashboard": ALL_ROLES,
    "manage_inventory": [ROLE_SUPER_ADMIN, ROLE_ADMINISTRATOR, ROLE_STORE_KEEPER],
    "view_inventory": ALL_ROLES,
    "issue_items": [ROLE_SUPER_ADMIN, ROLE_ADMINISTRATOR, ROLE_STORE_KEEPER, ROLE_OFFICE_STAFF],
    "return_items": [ROLE_SUPER_ADMIN, ROLE_ADMINISTRATOR, ROLE_STORE_KEEPER, ROLE_OFFICE_STAFF],
    "manage_printing": [ROLE_SUPER_ADMIN, ROLE_ADMINISTRATOR, ROLE_PRINTING_STAFF],
    "manage_teachers": [ROLE_SUPER_ADMIN, ROLE_ADMINISTRATOR, ROLE_OFFICE_STAFF],
    "manage_documents": [ROLE_SUPER_ADMIN, ROLE_ADMINISTRATOR, ROLE_OFFICE_STAFF, ROLE_DEPARTMENT_STAFF],
    "view_reports": [ROLE_SUPER_ADMIN, ROLE_ADMINISTRATOR, ROLE_OFFICE_STAFF, ROLE_STORE_KEEPER],
    "manage_users": [ROLE_SUPER_ADMIN, ROLE_ADMINISTRATOR],
    "manage_settings": [ROLE_SUPER_ADMIN, ROLE_ADMINISTRATOR],
}


def has_permission(role: str, permission_key: str) -> bool:
    return role in PERMISSIONS.get(permission_key, [])
