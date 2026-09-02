"""
ui/components/stat_card.py
A small reusable "stat card" widget used on the dashboard.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt


class StatCard(QFrame):
    def __init__(self, title: str, value: str, color: str = "#028090", parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setMinimumHeight(100)
        self.setMinimumWidth(180)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)

        bar = QFrame()
        bar.setFixedHeight(4)
        bar.setStyleSheet(f"background-color: {color}; border-radius: 2px;")

        self.value_label = QLabel(value)
        self.value_label.setObjectName("StatValue")
        self.value_label.setStyleSheet(f"color: {color};")

        title_label = QLabel(title)
        title_label.setObjectName("StatLabel")
        title_label.setWordWrap(True)

        layout.addWidget(bar)
        layout.addWidget(self.value_label)
        layout.addWidget(title_label)
        layout.addStretch()

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)
