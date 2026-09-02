"""
ui/main_window.py
Main application shell: sidebar navigation, top toolbar, and a
QStackedWidget hosting all feature pages. Applies role-based access
by only showing sidebar entries the current user is permitted to use.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QStackedWidget, QButtonGroup, QMessageBox
)
from PySide6.QtCore import Qt

import config
from auth.authentication import SessionManager
from auth.permissions import has_permission
from ui.components.theme import get_stylesheet

from ui.dashboard import DashboardPage
from ui.inventory import InventoryPage
from ui.issue_items import IssueItemsPage
from ui.return_items import ReturnItemsPage
from ui.printing import PrintingPage
from ui.teachers import TeachersPage
from ui.documents import DocumentsPage
from ui.suppliers import SuppliersPage
from ui.purchases import PurchasesPage
from ui.reports import ReportsPage
from ui.users import UsersPage
from ui.settings import SettingsPage


NAV_ITEMS = [
    ("dashboard", "🏠  Dashboard", "view_dashboard"),
    ("inventory", "📦  Inventory", "view_inventory"),
    ("issue", "📤  Issue Items", "issue_items"),
    ("return", "📥  Return Items", "return_items"),
    ("printing", "🖨️  Printing", "manage_printing"),
    ("teachers", "🎓  Teachers", "manage_teachers"),
    ("documents", "📄  Documents", "manage_documents"),
    ("suppliers", "🚚  Suppliers", "manage_suppliers"),
    ("purchases", "🧾  Purchases", "manage_purchases"),
    ("reports", "📊  Reports", "view_reports"),
    ("users", "👤  Users", "manage_users"),
    ("settings", "⚙️  Settings", "manage_settings"),
]


class MainWindow(QMainWindow):
    def __init__(self, session_user, on_logout):
        super().__init__()
        self.session_user = session_user
        self.on_logout = on_logout
        self.theme_mode = config.DEFAULT_THEME_MODE
        self.setWindowTitle(config.APP_NAME)
        self.resize(1280, 800)

        self._build_ui()
        self.apply_theme(self.theme_mode)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer_layout = QHBoxLayout(central)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # ---------------- Sidebar ----------------
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        brand_label = QLabel("UAIMS")
        brand_label.setStyleSheet("color: white; font-size: 22px; font-weight: 800; padding: 24px 18px 8px 18px;")
        sidebar_layout.addWidget(brand_label)

        role_label = QLabel(self.session_user.role)
        role_label.setStyleSheet("color: #B7DEE2; font-size: 11px; padding: 0px 18px 20px 18px;")
        sidebar_layout.addWidget(role_label)

        self.nav_buttons = {}
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        self.stack = QStackedWidget()
        self.page_indices = {}

        for key, label, permission in NAV_ITEMS:
            if not has_permission(self.session_user.role, permission):
                continue
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, k=key: self._navigate(k))
            sidebar_layout.addWidget(btn)
            self.nav_group.addButton(btn)
            self.nav_buttons[key] = btn

        sidebar_layout.addStretch()

        logout_btn = QPushButton("🚪  Logout")
        logout_btn.setStyleSheet("margin: 16px 12px; background-color: #023E47;")
        logout_btn.clicked.connect(self._handle_logout)
        sidebar_layout.addWidget(logout_btn)

        outer_layout.addWidget(sidebar)

        # ---------------- Main content ----------------
        content_wrapper = QWidget()
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Top bar
        top_bar = QWidget()
        top_bar.setObjectName("TopBar")
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(20, 0, 20, 0)
        self.page_title_label = QLabel("")
        self.page_title_label.setStyleSheet("font-weight: 600; font-size: 14px;")
        top_bar_layout.addWidget(self.page_title_label)
        top_bar_layout.addStretch()
        welcome_label = QLabel(f"{self.session_user.full_name}")
        welcome_label.setStyleSheet("color: #5A6B70;")
        top_bar_layout.addWidget(welcome_label)

        content_layout.addWidget(top_bar)
        content_layout.addWidget(self.stack)
        outer_layout.addWidget(content_wrapper)

        self._register_pages()

        if self.nav_buttons:
            first_key = list(self.nav_buttons.keys())[0]
            self._navigate(first_key)

    def _register_pages(self):
        self._page_factories = {
            "dashboard": lambda: DashboardPage(self.session_user),
            "inventory": lambda: InventoryPage(),
            "issue": lambda: IssueItemsPage(),
            "return": lambda: ReturnItemsPage(),
            "printing": lambda: PrintingPage(),
            "teachers": lambda: TeachersPage(),
            "documents": lambda: DocumentsPage(),
            "suppliers": lambda: SuppliersPage(),
            "purchases": lambda: PurchasesPage(),
            "reports": lambda: ReportsPage(),
            "users": lambda: UsersPage(),
            "settings": lambda: SettingsPage(self.apply_theme, self.theme_mode),
        }
        self._loaded_pages = {}

    def _navigate(self, key: str):
        if key not in self._loaded_pages:
            page = self._page_factories[key]()
            self.stack.addWidget(page)
            self._loaded_pages[key] = page
        else:
            page = self._loaded_pages[key]
            if hasattr(page, "refresh"):
                page.refresh()

        self.stack.setCurrentWidget(page)
        if key in self.nav_buttons:
            self.nav_buttons[key].setChecked(True)

        label_map = dict((k, label.split("  ", 1)[-1]) for k, label, _ in NAV_ITEMS)
        self.page_title_label.setText(label_map.get(key, ""))

    def apply_theme(self, mode: str):
        self.theme_mode = mode
        self.setStyleSheet(get_stylesheet(mode))

    def _handle_logout(self):
        confirm = QMessageBox.question(self, "Confirm Logout", "Are you sure you want to logout?")
        if confirm == QMessageBox.Yes:
            SessionManager.logout()
            self.on_logout()
