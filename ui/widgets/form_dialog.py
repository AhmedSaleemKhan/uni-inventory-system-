"""
ui/widgets/form_dialog.py
A generic, dynamically-built form dialog used to add/edit records
across the Inventory, Teachers, Suppliers, Printing, Documents,
Purchases, and Users modules.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QDateEdit, QSpinBox,
    QDoubleSpinBox, QTextEdit, QPushButton, QHBoxLayout, QLabel, QMessageBox,
    QCheckBox
)
from PySide6.QtCore import QDate


@dataclass
class FieldSpec:
    key: str
    label: str
    kind: str = "text"  # text, textarea, combo, date, int, float, checkbox
    options: list[str] = field(default_factory=list)
    required: bool = False
    default: Any = None
    minimum: float = 0
    maximum: float = 1_000_000


class FormDialog(QDialog):
    """Builds input widgets from a list of FieldSpec and returns collected values."""

    def __init__(self, title: str, fields: list[FieldSpec], initial: Optional[dict] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        self.field_specs = fields
        self.inputs: dict[str, Any] = {}
        initial = initial or {}

        layout = QFormLayout(self)

        for spec in fields:
            widget = self._build_widget(spec, initial.get(spec.key, spec.default))
            self.inputs[spec.key] = widget
            label_text = spec.label + (" *" if spec.required else "")
            layout.addRow(label_text, widget)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("SecondaryButton")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addRow(btn_row)

        self.values: dict[str, Any] = {}

    def _build_widget(self, spec: FieldSpec, value: Any):
        if spec.kind == "combo":
            combo = QComboBox()
            combo.addItems(spec.options)
            if value is not None and value in spec.options:
                combo.setCurrentText(str(value))
            return combo
        if spec.kind == "date":
            date_edit = QDateEdit()
            date_edit.setCalendarPopup(True)
            if isinstance(value, (dt.date, dt.datetime)):
                date_edit.setDate(QDate(value.year, value.month, value.day))
            else:
                date_edit.setDate(QDate.currentDate())
            return date_edit
        if spec.kind == "int":
            spin = QSpinBox()
            spin.setMinimum(int(spec.minimum))
            spin.setMaximum(int(spec.maximum))
            spin.setValue(int(value) if value is not None else 0)
            return spin
        if spec.kind == "float":
            dspin = QDoubleSpinBox()
            dspin.setMinimum(spec.minimum)
            dspin.setMaximum(spec.maximum)
            dspin.setDecimals(2)
            dspin.setValue(float(value) if value is not None else 0.0)
            return dspin
        if spec.kind == "textarea":
            text_edit = QTextEdit()
            text_edit.setPlainText(str(value) if value else "")
            text_edit.setMaximumHeight(80)
            return text_edit
        if spec.kind == "checkbox":
            checkbox = QCheckBox()
            checkbox.setChecked(bool(value))
            return checkbox
        # default: text
        line = QLineEdit()
        line.setText(str(value) if value is not None else "")
        return line

    def _on_save(self):
        result = {}
        for spec in self.field_specs:
            widget = self.inputs[spec.key]
            if spec.kind == "combo":
                val = widget.currentText()
            elif spec.kind == "date":
                qd = widget.date()
                val = dt.date(qd.year(), qd.month(), qd.day())
            elif spec.kind in ("int",):
                val = widget.value()
            elif spec.kind == "float":
                val = widget.value()
            elif spec.kind == "textarea":
                val = widget.toPlainText().strip()
            elif spec.kind == "checkbox":
                val = widget.isChecked()
            else:
                val = widget.text().strip()

            if spec.required and (val == "" or val is None):
                QMessageBox.warning(self, "Missing Field", f"'{spec.label}' is required.")
                return
            result[spec.key] = val

        self.values = result
        self.accept()
