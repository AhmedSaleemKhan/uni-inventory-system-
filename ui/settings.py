"""
ui/settings.py
Application settings: dark/light mode toggle, manual/automatic backup,
restore, database export/import, and account profile info.
"""

from __future__ import annotations

import shutil
import datetime as dt

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QFileDialog, QMessageBox, QCheckBox
)

import config
from auth.authentication import SessionManager, log_audit
from auth.permissions import has_permission


class SettingsPage(QWidget):
    def __init__(self, on_theme_toggle, current_theme: str, parent=None):
        super().__init__(parent)
        self.on_theme_toggle = on_theme_toggle
        self.current_theme = current_theme
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)

        title = QLabel("Settings")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        # Profile card
        profile_card = QFrame()
        profile_card.setObjectName("Card")
        profile_layout = QVBoxLayout(profile_card)
        user = SessionManager.current_user()
        profile_layout.addWidget(QLabel(f"<b>Logged in as:</b> {user.full_name} ({user.username})"))
        profile_layout.addWidget(QLabel(f"<b>Role:</b> {user.role}"))
        layout.addWidget(profile_card)

        # Appearance card
        appearance_card = QFrame()
        appearance_card.setObjectName("Card")
        appearance_layout = QVBoxLayout(appearance_card)
        appearance_layout.addWidget(QLabel("<b>Appearance</b>"))
        self.dark_mode_checkbox = QCheckBox("Enable Dark Mode")
        self.dark_mode_checkbox.setChecked(self.current_theme == "dark")
        self.dark_mode_checkbox.stateChanged.connect(self._toggle_theme)
        appearance_layout.addWidget(self.dark_mode_checkbox)
        layout.addWidget(appearance_card)

        # Backup card
        if has_permission(user.role, "manage_backup"):
            backup_card = QFrame()
            backup_card.setObjectName("Card")
            backup_layout = QVBoxLayout(backup_card)
            backup_layout.addWidget(QLabel("<b>Database Backup & Restore</b>"))

            btn_row = QHBoxLayout()
            manual_backup_btn = QPushButton("Create Manual Backup")
            manual_backup_btn.clicked.connect(self._manual_backup)
            restore_btn = QPushButton("Restore From Backup")
            restore_btn.setObjectName("DangerButton")
            restore_btn.clicked.connect(self._restore_backup)
            export_btn = QPushButton("Export Database")
            export_btn.setObjectName("SecondaryButton")
            export_btn.clicked.connect(self._export_database)

            btn_row.addWidget(manual_backup_btn)
            btn_row.addWidget(restore_btn)
            btn_row.addWidget(export_btn)
            backup_layout.addLayout(btn_row)

            note = QLabel(
                "Automatic backups are created every time the application starts. "
                "Manual backups and restores are logged in the audit trail."
            )
            note.setWordWrap(True)
            note.setStyleSheet("color: #7A8A8F; font-size: 11px;")
            backup_layout.addWidget(note)

            layout.addWidget(backup_card)

        layout.addStretch()

    def _toggle_theme(self):
        new_theme = "dark" if self.dark_mode_checkbox.isChecked() else "light"
        self.current_theme = new_theme
        self.on_theme_toggle(new_theme)

    def _manual_backup(self):
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = config.BACKUPS_DIR / f"manual_backup_{timestamp}.db"
        try:
            shutil.copy2(config.DATABASE_PATH, backup_path)
            log_audit(SessionManager.current_user().id, "MANUAL_BACKUP_CREATED", details=str(backup_path))
            QMessageBox.information(self, "Backup Created", f"Backup saved to:\n{backup_path}")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Backup Failed", f"Could not create backup:\n{exc}")

    def _restore_backup(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Backup File", str(config.BACKUPS_DIR), "SQLite DB (*.db)")
        if not path:
            return
        confirm = QMessageBox.question(
            self, "Confirm Restore",
            "Restoring will overwrite the current database. The application must be restarted afterward. Continue?"
        )
        if confirm != QMessageBox.Yes:
            return
        try:
            shutil.copy2(path, config.DATABASE_PATH)
            log_audit(SessionManager.current_user().id, "DATABASE_RESTORED", details=path)
            QMessageBox.information(self, "Restore Complete", "Database restored. Please restart the application.")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Restore Failed", f"Could not restore backup:\n{exc}")

    def _export_database(self):
        default_path = str(config.EXPORTS_DIR / f"uaims_export_{dt.date.today()}.db")
        path, _ = QFileDialog.getSaveFileName(self, "Export Database", default_path, "SQLite DB (*.db)")
        if not path:
            return
        try:
            shutil.copy2(config.DATABASE_PATH, path)
            QMessageBox.information(self, "Export Complete", f"Database exported to:\n{path}")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Export Failed", f"Could not export database:\n{exc}")
