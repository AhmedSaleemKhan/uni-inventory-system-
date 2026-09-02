"""
config.py
Central configuration for the University Administration Inventory
& Office Management System (UAIMS).
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# When packaged with PyInstaller, BASE_DIR resolves to a temporary bundle
# extraction folder that is wiped after every run. Writable/persistent data
# (database, backups, exports, reports, logs, generated QR/barcode images)
# must live in a real per-user data directory instead, or a packaged build
# would silently lose all data on every restart.
IS_FROZEN = getattr(sys, "frozen", False)


def _user_data_dir(app_name: str) -> Path:
    if sys.platform == "win32":
        base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or str(Path.home())
        return Path(base) / app_name
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / app_name
    base = os.getenv("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / app_name


DATA_DIR = _user_data_dir("UAIMS") if IS_FROZEN else BASE_DIR

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATABASE_DIR = DATA_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "inventory.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")

ASSETS_DIR = BASE_DIR / "assets"  # bundled read-only resources (logo, icons)
ICONS_DIR = ASSETS_DIR / "icons"
IMAGES_DIR = DATA_DIR / "assets" / "images"  # generated QR/barcode images
LOGO_PATH = ASSETS_DIR / "logo.png"

REPORTS_DIR = DATA_DIR / "reports"
EXPORTS_DIR = DATA_DIR / "exports"
BACKUPS_DIR = DATA_DIR / "backups"
LOGS_DIR = DATA_DIR / "logs"

for folder in (DATABASE_DIR, REPORTS_DIR, EXPORTS_DIR, BACKUPS_DIR, LOGS_DIR, ICONS_DIR, IMAGES_DIR):
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
