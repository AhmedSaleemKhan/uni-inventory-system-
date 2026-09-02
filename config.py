"""
config.py
Central configuration for the University Administration Inventory
& Office Management System (UAIMS).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "inventory.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")

ASSETS_DIR = BASE_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
IMAGES_DIR = ASSETS_DIR / "images"
LOGO_PATH = ASSETS_DIR / "logo.png"

REPORTS_DIR = BASE_DIR / "reports"
EXPORTS_DIR = BASE_DIR / "exports"
BACKUPS_DIR = BASE_DIR / "backups"
LOGS_DIR = BASE_DIR / "logs"

for folder in (REPORTS_DIR, EXPORTS_DIR, BACKUPS_DIR, LOGS_DIR, ICONS_DIR, IMAGES_DIR):
    folder.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
APP_NAME = "UAIMS - University Administration Inventory & Office Management System"
APP_VERSION = "1.0.0"
ORG_NAME = os.getenv("ORG_NAME", "PAF-IAST")

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"

LOW_STOCK_MULTIPLIER = 1.0  # quantity <= minimum_quantity * multiplier -> low stock

# ---------------------------------------------------------------------------
# Roles
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

# ---------------------------------------------------------------------------
# UI Theme
# ---------------------------------------------------------------------------
THEME_PRIMARY = "#028090"
THEME_PRIMARY_DARK = "#023E47"
THEME_ACCENT = "#F0A202"
THEME_DANGER = "#D64545"
THEME_SUCCESS = "#2E8B57"

DEFAULT_THEME_MODE = "light"  # or "dark"
