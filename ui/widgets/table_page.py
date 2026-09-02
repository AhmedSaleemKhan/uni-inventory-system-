"""
ui/widgets/table_page.py
Base class providing the common "title + search + add button + table"
layout used by Inventory, Teachers, Suppliers, Printing, Documents,
Purchases, and Users pages.
"""

from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QComboBox
)
from PySide6.QtCore import Qt


class TablePage(QWidget):
    def __init__(self, title: str, columns: list[str], add_label: str = "+ Add New",
                 show_add_button: bool = True, extra_filter_options: Optional[list[str]] = None,
                 parent=None):
        super().__init__(parent)
        self.columns = columns
        self._build_ui(title, add_label, show_add_button, extra_filter_options)

    def _build_ui(self, title, add_label, show_add_button, extra_filter_options):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        header_row = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("PageTitle")
        header_row.addWidget(title_label)
        header_row.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.setMaximumWidth(260)
        self.search_input.textChanged.connect(self.on_search)
        header_row.addWidget(self.search_input)

        self.filter_combo = None
        if extra_filter_options is not None:
            self.filter_combo = QComboBox()
            self.filter_combo.addItems(["All"] + extra_filter_options)
            self.filter_combo.currentTextChanged.connect(self.on_search)
            header_row.addWidget(self.filter_combo)

        if show_add_button:
            self.add_button = QPushButton(add_label)
            self.add_button.clicked.connect(self.on_add_clicked)
            header_row.addWidget(self.add_button)

        layout.addLayout(header_row)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

    def set_rows(self, rows: list[list[str]]):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for r, row_data in enumerate(rows):
            for c, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, c, item)
        self.table.setSortingEnabled(True)

    def selected_row_index(self) -> Optional[int]:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        return rows[0].row()

    def on_search(self, *_args):
        """Override in subclass to filter and re-populate rows."""
        pass

    def on_add_clicked(self):
        """Override in subclass to open the add dialog."""
        pass
