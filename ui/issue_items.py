"""
ui/issue_items.py
Records items issued to teachers/departments, decrements stock,
and generates an issue receipt (PDF).
"""

from __future__ import annotations

import datetime as dt

from PySide6.QtWidgets import QMessageBox, QPushButton, QHBoxLayout, QFileDialog

from database.database import get_session
from database.models import IssueRecord, Teacher, Item
from ui.widgets.table_page import TablePage
from ui.widgets.form_dialog import FormDialog, FieldSpec
from utils.helpers import format_date, current_time_str
from utils.pdf_reports import generate_issue_receipt
from auth.authentication import SessionManager, log_audit
from auth.permissions import has_permission
import config

COLUMNS = ["ID", "Teacher", "Item", "Qty", "Issue Date", "Department", "Return Required", "Expected Return", "Status"]


class IssueItemsPage(TablePage):
    def __init__(self, parent=None):
        self.can_manage = has_permission(SessionManager.current_user().role, "issue_items")
        super().__init__("Inventory Issue", COLUMNS, add_label="+ Issue Item",
                          show_add_button=self.can_manage,
                          extra_filter_options=["Issued", "Returned", "Overdue"], parent=parent)
        self._add_action_buttons()
        self.refresh()

    def _add_action_buttons(self):
        row = QHBoxLayout()
        receipt_btn = QPushButton("Print Receipt")
        receipt_btn.setObjectName("SecondaryButton")
        receipt_btn.clicked.connect(self._print_receipt)
        row.addWidget(receipt_btn)
        row.addStretch()
        self.layout().insertLayout(1, row)

    def refresh(self):
        self._all_rows = []
        with get_session() as session:
            for r in session.query(IssueRecord).order_by(IssueRecord.id.desc()).all():
                self._all_rows.append([
                    r.id, r.teacher.name if r.teacher else "-",
                    r.item.name if r.item else "-", r.quantity,
                    format_date(r.issue_date), r.department or "-",
                    "Yes" if r.return_required else "No",
                    format_date(r.expected_return_date), r.status,
                ])
        self.set_rows(self._all_rows)

    def on_search(self, *_args):
        query = self.search_input.text().lower().strip()
        status_filter = self.filter_combo.currentText() if self.filter_combo else "All"
        filtered = [
            row for row in self._all_rows
            if ((not query) or any(query in str(c).lower() for c in row))
            and (status_filter == "All" or row[8] == status_filter)
        ]
        self.set_rows(filtered)

    def on_add_clicked(self):
        with get_session() as session:
            teachers = [t.name for t in session.query(Teacher).order_by(Teacher.name).all()]
            items = [i.name for i in session.query(Item).filter(Item.current_quantity > 0).order_by(Item.name).all()]

        if not teachers or not items:
            QMessageBox.warning(self, "Not Available", "No teachers or in-stock items found.")
            return

        fields = [
            FieldSpec("teacher", "Teacher", kind="combo", options=teachers, required=True),
            FieldSpec("item", "Item", kind="combo", options=items, required=True),
            FieldSpec("quantity", "Quantity", kind="int", minimum=1, maximum=100000, default=1),
            FieldSpec("department", "Department"),
            FieldSpec("remarks", "Remarks", kind="textarea"),
            FieldSpec("return_required", "Return Required", kind="checkbox"),
            FieldSpec("expected_return_date", "Expected Return Date", kind="date"),
        ]
        dialog = FormDialog("Issue Item", fields, parent=self)
        if dialog.exec():
            self._save_issue(dialog.values)

    def _save_issue(self, values):
        with get_session() as session:
            teacher = session.query(Teacher).filter(Teacher.name == values["teacher"]).first()
            item = session.query(Item).filter(Item.name == values["item"]).first()
            if not teacher or not item:
                QMessageBox.warning(self, "Error", "Selected teacher or item not found.")
                return
            qty = values.get("quantity", 1)
            if item.current_quantity < qty:
                QMessageBox.warning(self, "Insufficient Stock",
                                     f"Only {item.current_quantity} units of '{item.name}' available.")
                return

            record = IssueRecord(
                teacher_id=teacher.id,
                item_id=item.id,
                quantity=qty,
                issue_date=dt.date.today(),
                issue_time=current_time_str(),
                issued_by=SessionManager.current_user().full_name,
                department=values.get("department") or teacher.department,
                remarks=values.get("remarks", ""),
                return_required=values.get("return_required", False),
                expected_return_date=values.get("expected_return_date") if values.get("return_required") else None,
                status="Issued",
            )
            item.current_quantity -= qty
            session.add(record)

        log_audit(SessionManager.current_user().id, "ITEM_ISSUED", entity="IssueRecord")
        self.refresh()
        QMessageBox.information(self, "Success", "Item issued and stock updated.")

    def _print_receipt(self):
        row_idx = self.selected_row_index()
        if row_idx is None:
            QMessageBox.information(self, "No Selection", "Please select an issue record to print.")
            return
        issue_id = int(self.table.item(row_idx, 0).text())
        with get_session() as session:
            record = session.get(IssueRecord, issue_id)
            if not record:
                return
            data = {
                "id": record.id,
                "teacher": record.teacher.name if record.teacher else "-",
                "department": record.department or "-",
                "item": record.item.name if record.item else "-",
                "quantity": record.quantity,
                "issue_date": format_date(record.issue_date),
                "issued_by": record.issued_by or "-",
                "expected_return": format_date(record.expected_return_date),
                "remarks": record.remarks or "-",
            }

        default_path = str(config.REPORTS_DIR / f"issue_receipt_{issue_id}.pdf")
        path, _ = QFileDialog.getSaveFileName(self, "Save Issue Receipt", default_path, "PDF Files (*.pdf)")
        if not path:
            return
        generate_issue_receipt(data, path)
        QMessageBox.information(self, "Receipt Generated", f"Receipt saved to:\n{path}")
