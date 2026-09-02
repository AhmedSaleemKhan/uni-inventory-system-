"""
ui/return_items.py
Tracks returned items, restocks inventory, flags overdue/late returns.
"""

from __future__ import annotations

import datetime as dt

from PySide6.QtWidgets import QMessageBox, QPushButton, QHBoxLayout

from database.database import get_session
from database.models import IssueRecord, ReturnRecord
from ui.widgets.table_page import TablePage
from ui.widgets.form_dialog import FormDialog, FieldSpec
from utils.helpers import format_date
from auth.authentication import SessionManager, log_audit
from auth.permissions import has_permission

COLUMNS = ["Issue ID", "Teacher", "Item", "Qty Issued", "Issue Date", "Expected Return", "Status"]


class ReturnItemsPage(TablePage):
    def __init__(self, parent=None):
        self.can_manage = has_permission(SessionManager.current_user().role, "return_items")
        super().__init__("Return Management", COLUMNS, add_label="+ Record Return",
                          show_add_button=self.can_manage,
                          extra_filter_options=["Issued", "Returned", "Overdue"], parent=parent)
        self.refresh()

    def refresh(self):
        # Update overdue status first
        today = dt.date.today()
        with get_session() as session:
            pending = session.query(IssueRecord).filter(
                IssueRecord.return_required == True,  # noqa: E712
                IssueRecord.status == "Issued",
            ).all()
            for r in pending:
                if r.expected_return_date and r.expected_return_date < today:
                    r.status = "Overdue"

        self._all_rows = []
        with get_session() as session:
            records = session.query(IssueRecord).filter(
                IssueRecord.return_required == True  # noqa: E712
            ).order_by(IssueRecord.id.desc()).all()
            for r in records:
                self._all_rows.append([
                    r.id, r.teacher.name if r.teacher else "-",
                    r.item.name if r.item else "-", r.quantity,
                    format_date(r.issue_date), format_date(r.expected_return_date), r.status,
                ])
        self.set_rows(self._all_rows)

    def on_search(self, *_args):
        query = self.search_input.text().lower().strip()
        status_filter = self.filter_combo.currentText() if self.filter_combo else "All"
        filtered = [
            row for row in self._all_rows
            if ((not query) or any(query in str(c).lower() for c in row))
            and (status_filter == "All" or row[6] == status_filter)
        ]
        self.set_rows(filtered)

    def on_add_clicked(self):
        row_idx = self.selected_row_index()
        if row_idx is None:
            QMessageBox.information(self, "No Selection", "Select an 'Issued' or 'Overdue' record to return.")
            return
        issue_id = int(self.table.item(row_idx, 0).text())

        with get_session() as session:
            record = session.get(IssueRecord, issue_id)
            if not record or record.status == "Returned":
                QMessageBox.warning(self, "Invalid", "This record is already returned or invalid.")
                return
            issued_quantity = record.quantity

        fields = [
            FieldSpec("returned_quantity", "Returned Quantity", kind="int", minimum=1, maximum=100000, default=issued_quantity),
            FieldSpec("condition", "Condition", kind="combo", options=["Good", "Damaged", "Partially Used"]),
            FieldSpec("remarks", "Remarks", kind="textarea"),
        ]
        dialog = FormDialog("Record Return", fields, parent=self)
        if dialog.exec():
            self._save_return(issue_id, dialog.values)

    def _save_return(self, issue_id: int, values: dict):
        with get_session() as session:
            record = session.get(IssueRecord, issue_id)
            if not record:
                return
            return_date = dt.date.today()
            is_late = bool(record.expected_return_date and return_date > record.expected_return_date)

            return_record = ReturnRecord(
                issue_id=record.id,
                returned_quantity=values.get("returned_quantity", record.quantity),
                return_date=return_date,
                condition=values.get("condition", "Good"),
                received_by=SessionManager.current_user().full_name,
                remarks=values.get("remarks", ""),
                is_late=is_late,
            )
            session.add(return_record)
            record.status = "Returned"

            item = record.item
            if item and values.get("condition") != "Damaged":
                item.current_quantity += values.get("returned_quantity", record.quantity)

        log_audit(SessionManager.current_user().id, "ITEM_RETURNED", entity="ReturnRecord", entity_id=issue_id)
        self.refresh()
        QMessageBox.information(self, "Success", "Return recorded and stock updated." + (" (Late return)" if is_late else ""))
