"""
main.py
Entry point for the University Administration Inventory & Office
Management System (UAIMS).

Run with:
    python main.py
"""

from __future__ import annotations

import sys
import shutil
import datetime as dt
import logging

from PySide6.QtWidgets import QApplication, QMessageBox

import config
from utils.app_logger import setup_logging
from database.database import init_db, database_is_fresh
from database.seed import seed_all
from ui.login import LoginWindow
from ui.main_window import MainWindow


logger = logging.getLogger("uaims.main")


class Application:
    """Owns the QApplication and manages switching between the login
    window and the main application window."""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName(config.APP_NAME)
        self.app.setOrganizationName(config.ORG_NAME)

        self.login_window: LoginWindow | None = None
        self.main_window: MainWindow | None = None

    def start(self) -> int:
        self._bootstrap_database()
        self._auto_backup()
        self.show_login()
        return self.app.exec()

    def _bootstrap_database(self):
        fresh = database_is_fresh()
        init_db()
        if fresh:
            logger.info("Fresh database detected. Seeding demo data...")
        seed_all()

    def _auto_backup(self):
        try:
            if config.DATABASE_PATH.exists():
                timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = config.BACKUPS_DIR / f"auto_backup_{timestamp}.db"
                shutil.copy2(config.DATABASE_PATH, backup_path)
                # Keep only the most recent 10 automatic backups
                auto_backups = sorted(config.BACKUPS_DIR.glob("auto_backup_*.db"))
                for old in auto_backups[:-10]:
                    old.unlink(missing_ok=True)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Automatic backup failed: %s", exc)

    def show_login(self):
        self.login_window = LoginWindow(on_login_success=self._on_login_success)
        self.login_window.show()

    def _on_login_success(self, session_user):
        if self.login_window:
            self.login_window.close()
            self.login_window = None
        self.main_window = MainWindow(session_user, on_logout=self._on_logout)
        self.main_window.show()

    def _on_logout(self):
        if self.main_window:
            self.main_window.close()
            self.main_window = None
        self.show_login()


def main() -> int:
    setup_logging()
    logger.info("Starting %s", config.APP_NAME)
    try:
        application = Application()
        return application.start()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Fatal error during startup")
        try:
            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(None, "Fatal Error", f"UAIMS failed to start:\n\n{exc}")
        except Exception:
            print(f"Fatal error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
