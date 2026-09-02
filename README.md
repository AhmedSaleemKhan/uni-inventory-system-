# UAIMS — University Administration Inventory & Office Management System

A production-ready desktop application for managing university office
inventory, teacher records, printing jobs, document tracking, suppliers,
purchases, and reporting — built with **Python 3 + PySide6 + SQLAlchemy**.

---

## 1. Project Overview

UAIMS replaces manual registers with a single desktop system that lets
office staff, store keepers, printing staff, and administrators track:

- Stationery and consumable **inventory** (barcodes, QR codes, stock levels)
- **Teachers/faculty** records and assigned courses
- Items **issued** to teachers/departments and their **returns**
- **Printing jobs** (B/W, color, single/double side, cost calculation)
- **Documents** moving through the office (internship files, TA files,
  attendance sheets, exam files, etc.)
- **Suppliers** and **purchase orders** with automatic stock updates
- Role-based **users** and a full **audit trail**
- **Reports** exportable to PDF, Excel, and CSV

## 2. Features

- 🔐 Secure login with bcrypt password hashing, forced password change on
  first login, login history, and audit logging
- 🧭 Six roles with distinct permissions: Super Admin, Administrator,
  Office Staff, Store Keeper, Printing Staff, Department Staff
- 📊 Live dashboard: KPI cards, monthly chart, notifications, recent activity
- 📦 Inventory CRUD with barcode + QR code generation and low/out-of-stock detection
- 📤 Issue module with stock validation and printable PDF receipts
- 📥 Return module with overdue/late-return detection and automatic restock
- 🖨️ Printing job tracker with automatic cost calculation
- 📄 Document lifecycle tracking (Pending → Received → Approved/Rejected)
- 🚚 Supplier management with linked purchase history
- 🧾 Purchase orders with multi-line items, tax calculation, and stock receipt
- 📑 Reports Center: 9 report types, each exportable to PDF / Excel / CSV
- 👤 User management (create/deactivate/reset password) for admins
- 🌗 Light/Dark mode toggle
- 💾 Manual & automatic database backup, restore, and export

## 3. Technology Stack

| Layer          | Technology                     |
|----------------|---------------------------------|
| UI Framework   | PySide6 (Qt for Python)         |
| ORM / Database | SQLAlchemy 2.x + SQLite         |
| Security       | bcrypt password hashing         |
| PDF Reports    | ReportLab                       |
| Excel Export   | OpenPyXL                        |
| Barcodes / QR  | python-barcode, qrcode, Pillow  |
| Charts         | Matplotlib (embedded via Qt canvas) |
| Data handling  | Pandas                          |
| Packaging      | PyInstaller                     |
| Config         | python-dotenv                   |

## 4. Folder Structure

```
University_Inventory_System/
├── main.py                  # Application entry point
├── config.py                # Central configuration (paths, roles, theme)
├── requirements.txt
├── README.md
├── .env.example
├── database/
│   ├── database.py          # Engine/session setup
│   ├── models.py            # SQLAlchemy ORM models
│   ├── seed.py               # Demo/sample data seeding
│   └── inventory.db          # Created automatically on first run
├── ui/
│   ├── login.py, dashboard.py, inventory.py, issue_items.py,
│   │   return_items.py, printing.py, teachers.py, documents.py,
│   │   suppliers.py, purchases.py, reports.py, users.py, settings.py
│   ├── main_window.py        # Sidebar + top bar + page routing
│   ├── widgets/               # Reusable TablePage & FormDialog components
│   └── components/            # Theme stylesheet & stat cards
├── auth/
│   ├── authentication.py     # bcrypt hashing, login/session, audit log
│   ├── roles.py               # Role definitions
│   └── permissions.py         # Permission matrix helpers
├── utils/
│   ├── helpers.py             # IDs, barcodes, QR, formatting
│   ├── pdf_reports.py         # ReportLab PDF builders
│   └── app_logger.py          # Rotating file logger
├── assets/                    # Logo, icons, images (QR/barcode output)
├── reports/, exports/, backups/, logs/  # Runtime-generated output
└── tests/
    └── test_models.py         # Pytest unit tests
```

## 5. Installation

```bash
cd University_Inventory_System
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 6. Running the Application

```bash
python main.py
```

On first launch, UAIMS automatically:
1. Creates `database/inventory.db` with all tables.
2. Seeds demo data — 100 inventory items, 30 teachers, 15 suppliers,
   50 issue records, 50 printing records, 20 purchase orders, 20 document
   records, plus 5 demo user accounts (one per additional role).
3. Creates an automatic backup snapshot in `/backups`.

## 7. Default Login

| Username     | Password    | Role            |
|--------------|-------------|-----------------|
| admin        | admin123    | Super Admin     |
| storekeeper  | password123 | Store Keeper    |
| officestaff  | password123 | Office Staff    |
| printstaff   | password123 | Printing Staff  |
| deptstaff    | password123 | Department Staff|

You will be required to set a new password the first time you log in
with the `admin` account (or any account with `must_change_password`).

## 8. Database

SQLite database at `database/inventory.db`, fully normalized with foreign
keys and indexes (see `database/models.py`). Tables are created
automatically via SQLAlchemy's `Base.metadata.create_all()` — no manual
migration step is required for first run.

## 9. Packaging (optional, PyInstaller)

```bash
pyinstaller --name UAIMS --windowed --onefile --add-data "assets:assets" main.py
# Windows note: use a semicolon separator instead: --add-data "assets;assets"
```

The generated executable will be under `dist/`.

**Where packaged data lives.** When run from source (`python main.py`),
the database, backups, exports, reports, and logs live next to the
project files, as usual. When run as a packaged executable, `sys.frozen`
is detected and all of that is instead stored in a per-user data
directory so it survives restarts (a PyInstaller `--onefile` build
extracts to a temporary folder that is wiped after every run, so writing
there would silently lose all data between launches):

| OS      | Data directory                                  |
|---------|--------------------------------------------------|
| Windows | `%LOCALAPPDATA%\UAIMS`                            |
| macOS   | `~/Library/Application Support/UAIMS`             |
| Linux   | `$XDG_DATA_HOME/UAIMS` (default `~/.local/share/UAIMS`) |

**Prebuilt installers via CI.** `.github/workflows/build-installers.yml`
builds a Windows `.exe`, a Linux binary, and a macOS app on every push to
`main` (and on demand via the Actions tab's "Run workflow" button), since
PyInstaller cannot cross-compile — each platform's build must run on that
platform. Grab the artifact for your OS from the workflow run's
**Artifacts** section on GitHub and run it directly; no Python install
required on the target machine.

## 10. Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

Tests cover ORM models, password hashing, and the role/permission matrix
using an isolated in-memory SQLite database (they never touch your real
`inventory.db`).

## 11. Future Improvements

- Multi-branch/multi-campus inventory support
- Email/SMS notifications for low stock and overdue returns
- REST API layer for a companion mobile app
- Barcode scanner hardware integration for faster issue/return workflows
- Role-level custom report builder

## 12. Troubleshooting & FAQ

**Q: The app won't start / `ModuleNotFoundError`.**
A: Make sure you activated your virtual environment and ran
`pip install -r requirements.txt` inside it.

**Q: I forgot the admin password.**
A: Stop the app, delete `database/inventory.db` (this wipes all data), and
restart — a fresh database with the default `admin/admin123` login will be
recreated. For a database with existing data, log in as another Super
Admin/Administrator user and use **Users → Reset Password**.

**Q: Where are generated PDF/Excel/CSV reports saved?**
A: You choose the destination via a save dialog each time; the default
suggested folder is `exports/` (for Reports Center) or `reports/` (for
issue receipts).

**Q: How do I restore a backup?**
A: Go to **Settings → Restore From Backup** (Super Admin only), pick a
`.db` file from `backups/`, and restart the application afterward.

## 13. License

This project was built as an internal administrative tool. Adapt and
redistribute according to your institution's software policies.

## 14. Developer Guide

- All business logic lives outside the `ui/` package (in `database/`,
  `auth/`, and `utils/`) so it can be unit-tested without a Qt event loop.
- `ui/widgets/table_page.py` (`TablePage`) and `ui/widgets/form_dialog.py`
  (`FormDialog`) are the two reusable building blocks behind almost every
  CRUD screen — extend these rather than duplicating table/dialog code.
- Permissions are declared once in `auth/roles.py` (`PERMISSIONS` dict) and
  checked via `auth.permissions.has_permission(role, key)` — add new keys
  there when adding new protected features.
- New feature pages should be registered in `ui/main_window.py`
  (`NAV_ITEMS` + `_page_factories`).
