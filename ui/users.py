"""
ui/users.py
User account management: create staff accounts, assign roles,
activate/deactivate, reset passwords. Restricted to Super Admin /
Administrator roles.
"""

from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QPushButton, QHBoxLayout

import config
from database.database import get_session
from database.models import User
from ui.widgets.table_page import TablePage
from ui.widgets.form_dialog import FormDialog, FieldSpec
from auth.authentication import SessionManager, log_audit, hash_password
from auth.permissions import has_permission

COLUMNS = ["ID", "Username", "Full Name", "Role", "Email", "Active", "Last Login"]


class UsersPage(TablePage):
    def __init__(self, parent=None):
        self.can_manage = has_permission(SessionManager.current_user().role, "manage_users")
        super().__init__("User Management", COLUMNS, add_label="+ Add User",
                          show_add_button=self.can_manage,
                          extra_filter_options=config.ALL_ROLES, parent=parent)
        self._add_action_buttons()
        self.refresh()

    def _add_action_buttons(self):
        if not self.can_manage:
            return
        row = QHBoxLayout()
        toggle_btn = QPushButton("Toggle Active/Inactive")
        toggle_btn.setObjectName("SecondaryButton")
        toggle_btn.clicked.connect(self._toggle_active)
        reset_btn = QPushButton("Reset Password")
        reset_btn.setObjectName("DangerButton")
        reset_btn.clicked.connect(self._reset_password)
        row.addWidget(toggle_btn)
        row.addWidget(reset_btn)
        row.addStretch()
        self.layout().insertLayout(1, row)

    def refresh(self):
        self._all_rows = []
        with get_session() as session:
            for u in session.query(User).order_by(User.id.desc()).all():
                self._all_rows.append([
                    u.id, u.username, u.full_name, u.role, u.email or "-",
                    "Yes" if u.is_active else "No",
                    u.last_login.strftime("%d-%b-%Y %I:%M %p") if u.last_login else "Never",
                ])
        self.set_rows(self._all_rows)

    def on_search(self, *_args):
        query = self.search_input.text().lower().strip()
        role_filter = self.filter_combo.currentText() if self.filter_combo else "All"
        filtered = [
            row for row in self._all_rows
            if ((not query) or any(query in str(c).lower() for c in row))
            and (role_filter == "All" or row[3] == role_filter)
        ]
        self.set_rows(filtered)

    def on_add_clicked(self):
        fields = [
            FieldSpec("username", "Username", required=True),
            FieldSpec("full_name", "Full Name", required=True),
            FieldSpec("role", "Role", kind="combo", options=config.ALL_ROLES, required=True),
            FieldSpec("email", "Email"),
            FieldSpec("phone", "Phone"),
            FieldSpec("password", "Temporary Password", default="password123", required=True),
        ]
        dialog = FormDialog("Add User", fields, parent=self)
        if dialog.exec():
            self._save_user(dialog.values)

    def _save_user(self, values):
        with get_session() as session:
            existing = session.query(User).filter(User.username == values["username"]).first()
            if existing:
                QMessageBox.warning(self, "Duplicate Username", "A user with this username already exists.")
                return
            user = User(
                username=values["username"],
                password_hash=hash_password(values.get("password") or "password123"),
                full_name=values["full_name"],
                role=values["role"],
                email=values.get("email", ""),
                phone=values.get("phone", ""),
                must_change_password=True,
            )
            session.add(user)
        log_audit(SessionManager.current_user().id, "USER_CREATED", entity="User")
        self.refresh()

    def _toggle_active(self):
        row_idx = self.selected_row_index()
        if row_idx is None:
            QMessageBox.information(self, "No Selection", "Please select a user.")
            return
        user_id = int(self.table.item(row_idx, 0).text())
        if user_id == SessionManager.current_user().id:
            QMessageBox.warning(self, "Not Allowed", "You cannot deactivate your own account.")
            return
        with get_session() as session:
            user = session.get(User, user_id)
            if user:
                user.is_active = not user.is_active
        log_audit(SessionManager.current_user().id, "USER_TOGGLED_ACTIVE", entity="User", entity_id=user_id)
        self.refresh()

    def _reset_password(self):
        row_idx = self.selected_row_index()
        if row_idx is None:
            QMessageBox.information(self, "No Selection", "Please select a user.")
            return
        user_id = int(self.table.item(row_idx, 0).text())
        with get_session() as session:
            user = session.get(User, user_id)
            if user:
                user.password_hash = hash_password("password123")
                user.must_change_password = True
        log_audit(SessionManager.current_user().id, "USER_PASSWORD_RESET", entity="User", entity_id=user_id)
        QMessageBox.information(self, "Password Reset", "Password reset to 'password123'. User must change it at next login.")
        self.refresh()
