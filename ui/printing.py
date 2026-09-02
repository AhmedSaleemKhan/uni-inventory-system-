"""
ui/printing.py
Tracks every printing request: teacher, course, document, color/side mode,
pages, copies, cost, and status.
"""

from __future__ import annotations

import datetime as dt

from PySide6.QtWidgets import QMessageBox

from database.database import get_session
from database.models import PrintingRecord, Teacher
from ui.widgets.table_page import TablePage
from ui.widgets.form_dialog import FormDialog, FieldSpec
from utils.helpers import format_date, format_currency
from auth.authentication import SessionManager, log_audit
from auth.permissions import has_permission

COLUMNS = ["ID", "Teacher", "Department", "Course", "Document", "Mode", "Sides", "Pages", "Copies", "Cost", "Date", "Status"]

COST_PER_PAGE_BW = 5.0
COST_PER_PAGE_COLOR = 15.0


class PrintingPage(TablePage):
    def __init__(self, parent=None):
        self.can_manage = has_permission(SessionManager.current_user().role, "manage_printing")
        super().__init__("Printing Management", COLUMNS, add_label="+ New Printing Job",
                          show_add_button=self.can_manage,
                          extra_filter_options=["Black & White", "Color"], parent=parent)
        self.refresh()

    def refresh(self):
        self._all_rows = []
        with get_session() as session:
            for r in session.query(PrintingRecord).order_by(PrintingRecord.id.desc()).all():
                self._all_rows.append([
                    r.id, r.teacher_name, r.department or "-", r.course or "-",
                    r.document_name, r.color_mode, r.side_mode, r.pages, r.copies,
                    format_currency(r.cost), format_date(r.print_date), r.status,
                ])
        self.set_rows(self._all_rows)

    def on_search(self, *_args):
        query = self.search_input.text().lower().strip()
        mode_filter = self.filter_combo.currentText() if self.filter_combo else "All"
        filtered = [
            row for row in self._all_rows
            if ((not query) or any(query in str(c).lower() for c in row))
            and (mode_filter == "All" or row[5] == mode_filter)
        ]
        self.set_rows(filtered)

    def on_add_clicked(self):
        with get_session() as session:
            teachers = [t.name for t in session.query(Teacher).order_by(Teacher.name).all()]

        fields = [
            FieldSpec("teacher", "Teacher", kind="combo", options=["-"] + teachers),
            FieldSpec("department", "Department"),
            FieldSpec("course", "Course"),
            FieldSpec("document_name", "Document Name", required=True),
            FieldSpec("color_mode", "Color Mode", kind="combo", options=["Black & White", "Color"]),
            FieldSpec("side_mode", "Side Mode", kind="combo", options=["Single Side", "Double Side"]),
            FieldSpec("pages", "Pages", kind="int", minimum=1, maximum=10000, default=1),
            FieldSpec("copies", "Copies", kind="int", minimum=1, maximum=10000, default=1),
        ]
        dialog = FormDialog("New Printing Job", fields, parent=self)
        if dialog.exec():
            self._save_printing(dialog.values)

    def _save_printing(self, values):
        per_page = COST_PER_PAGE_COLOR if values["color_mode"] == "Color" else COST_PER_PAGE_BW
        cost = values["pages"] * values["copies"] * per_page
        teacher_obj = None

        with get_session() as session:
            if values.get("teacher") and values["teacher"] != "-":
                teacher_obj = session.query(Teacher).filter(Teacher.name == values["teacher"]).first()

            record = PrintingRecord(
                teacher_id=teacher_obj.id if teacher_obj else None,
                teacher_name=values.get("teacher") if values.get("teacher") != "-" else "Walk-in / Office",
                department=values.get("department", ""),
                course=values.get("course", ""),
                document_name=values["document_name"],
                color_mode=values["color_mode"],
                side_mode=values["side_mode"],
                pages=values["pages"],
                copies=values["copies"],
                cost=cost,
                printed_by=SessionManager.current_user().full_name,
                print_date=dt.date.today(),
                status="Completed",
            )
            session.add(record)

        log_audit(SessionManager.current_user().id, "PRINTING_JOB_CREATED", entity="PrintingRecord")
        self.refresh()
        QMessageBox.information(self, "Success", f"Printing job recorded. Cost: {format_currency(cost)}")
