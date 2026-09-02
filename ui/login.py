"""
ui/login.py
Login window for UAIMS. Handles authentication, forced password change
on first login, and hand-off to the main window.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QFrame, QDialog, QFormLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

import config
from auth.authentication import authenticate, change_password


class ChangePasswordDialog(QDialog):
    """Forces a password change on first login."""

    def __init__(self, user_id: int, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle("Change Password Required")
        self.setModal(True)
        self.setMinimumWidth(360)

        layout = QFormLayout(self)

        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)

        layout.addRow(QLabel("For security, please set a new password before continuing."))
        layout.addRow("New Password:", self.new_password)
        layout.addRow("Confirm Password:", self.confirm_password)

        submit_btn = QPushButton("Set New Password")
        submit_btn.clicked.connect(self._submit)
        layout.addRow(submit_btn)

    def _submit(self):
        pwd = self.new_password.text()
        confirm = self.confirm_password.text()
        if len(pwd) < 6:
            QMessageBox.warning(self, "Weak Password", "Password must be at least 6 characters long.")
            return
        if pwd != confirm:
            QMessageBox.warning(self, "Mismatch", "Passwords do not match.")
            return
        change_password(self.user_id, pwd)
        QMessageBox.information(self, "Success", "Password updated successfully.")
        self.accept()


class LoginWindow(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.setWindowTitle(config.APP_NAME)
        self.resize(920, 560)
        self._build_ui()

    def _build_ui(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Left brand panel
        brand_panel = QFrame()
        brand_panel.setStyleSheet(
            f"background-color: {config.THEME_PRIMARY_DARK};"
        )
        brand_layout = QVBoxLayout(brand_panel)
        brand_layout.setAlignment(Qt.AlignCenter)
        brand_layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("UAIMS")
        title.setStyleSheet("color: white; font-size: 42px; font-weight: 800;")
        subtitle = QLabel("University Administration\nInventory & Office\nManagement System")
        subtitle.setStyleSheet("color: #CFE9EC; font-size: 15px;")
        org = QLabel(config.ORG_NAME)
        org.setStyleSheet("color: #90C6CB; font-size: 13px; margin-top: 24px;")

        brand_layout.addWidget(title)
        brand_layout.addWidget(subtitle)
        brand_layout.addStretch()
        brand_layout.addWidget(org)

        # Right login form panel
        form_panel = QFrame()
        form_layout = QVBoxLayout(form_panel)
        form_layout.setAlignment(Qt.AlignCenter)
        form_layout.setContentsMargins(60, 60, 60, 60)
        form_layout.setSpacing(14)

        heading = QLabel("Sign in to your account")
        heading.setObjectName("PageTitle")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self._attempt_login)

        login_btn = QPushButton("Login")
        login_btn.setMinimumHeight(40)
        login_btn.clicked.connect(self._attempt_login)

        hint = QLabel("Default: admin / admin123")
        hint.setStyleSheet("color: #8A9AA0; font-size: 11px;")

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {config.THEME_DANGER};")
        self.status_label.setWordWrap(True)

        form_layout.addWidget(heading)
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(self.status_label)
        form_layout.addWidget(login_btn)
        form_layout.addWidget(hint)

        outer.addWidget(brand_panel, 1)
        outer.addWidget(form_panel, 1)

    def _attempt_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self.status_label.setText("Please enter both username and password.")
            return

        user, message = authenticate(username, password)
        if user is None:
            self.status_label.setText(message)
            return

        self.status_label.setText("")

        if user.must_change_password:
            dialog = ChangePasswordDialog(user.id, self)
            if dialog.exec() != QDialog.Accepted:
                return  # user cancelled, stay on login

        self.on_login_success(user)
