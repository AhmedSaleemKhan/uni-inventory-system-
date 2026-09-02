"""
ui/documents.py
Tracks institutional documents (internship files, TA files, attendance
sheets, official letters, purchase requests, exam/course files, etc.)
through their lifecycle: Pending -> Received -> Approved/Rejected.
"""

from __future__ import annotations

import datetime as dt

from PySide6.QtWidgets import QMessageBox, QPushButton, QHBoxLayout

from database.database import get_session
from database.models import DocumentRecord, Teacher
from ui.widgets.table_page import TablePage
from ui.widgets.form_dialog import FormDialog, FieldSpec
from utils.helpers import format_date
from auth.authentication import SessionManager, log_audit
from auth.permissions import has_permission

COLUMNS = ["ID", "Type", "Title", "Department", "Submitted By", "Received Date", "Status"]

DOCUMENT_TYPES = [
    "Internship Files", "TA Files", "Attendance Sheets", "Official Letters",
    "Purchase Requests", "Exam Files", "Course Files", "Office Files",
    "Teacher Documents",
]
STATUSES = ["Pending", "Received", "Approved", "Rejected"]


class DocumentsPage(TablePage):
    def __init__(self, parent=None):
        self.can_manage = has_permission(SessionManager.current_user().role, "manage_documents")
        super().__init__("Document Tracking", COLUMNS, add_label="+ Add Document",
                          show_add_button=self.can_manage,
                          extra_filter_options=STATUSES, parent=parent)
        self._add_action_buttons()
        self.refresh()

    def _add_action_buttons(self):
        if not self.can_manage:
            return
        row = QHBoxLayout()
        approve_btn = QPushButton("Approve Selected")
        approve_btn.setObjectName("SuccessButton")
        approve_btn.clicked.connect(lambda: self._update_status("Approved"))
        reject_btn = QPushButton("Reject Selected")
        reject_btn.setObjectName("DangerButton")
        reject_btn.clicked.connect(lambda: self._update_status("Rejected"))
        received_btn = QPushButton("Mark Received")
        received_btn.setObjectName("SecondaryButton")
        received_btn.clicked.connect(lambda: self._update_status("Received"))
        row.addWidget(received_btn)
        row.addWidget(approve_btn)
        row.addWidget(reject_btn)
        row.addStretch()
        self.layout().insertLayout(1, row)

    def refresh(self):
        self._all_rows = []
        with get_session() as session:
            for d in session.query(DocumentRecord).order_by(DocumentRecord.id.desc()).all():
                self._all_rows.append([
                    d.id, d.document_type, d.title, d.department or "-",
                    d.submitted_by or "-", format_date(d.received_date), d.status,
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
        with get_session() as session:
            teachers = [t.name for t in session.query(Teacher).order_by(Teacher.name).all()]

        fields = [
            FieldSpec("document_type", "Document Type", kind="combo", options=DOCUMENT_TYPES, required=True),
            FieldSpec("title", "Title", required=True),
            FieldSpec("department", "Department"),
            FieldSpec("submitted_by", "Submitted By", kind="combo", options=["-"] + teachers),
            FieldSpec("status", "Status", kind="combo", options=STATUSES),
            FieldSpec("remarks", "Remarks", kind="textarea"),
        ]
        dialog = FormDialog("Add Document Record", fields, parent=self)
        if dialog.exec():
            self._save_document(dialog.values)

    def _save_document(self, values):
        with get_session() as session:
            teacher = None
            if values.get("submitted_by") and values["submitted_by"] != "-":
                teacher = session.query(Teacher).filter(Teacher.name == values["submitted_by"]).first()
            record = DocumentRecord(
                document_type=values["document_type"],
                title=values["title"],
                teacher_id=teacher.id if teacher else None,
                department=values.get("department", ""),
                submitted_by=values.get("submitted_by") if values.get("submitted_by") != "-" else None,
                received_date=dt.date.today(),
                status=values.get("status", "Pending"),
                remarks=values.get("remarks", ""),
            )
            session.add(record)
        log_audit(SessionManager.current_user().id, "DOCUMENT_ADDED", entity="DocumentRecord")
        self.refresh()

    def _update_status(self, new_status: str):
        row_idx = self.selected_row_index()
        if row_idx is None:
            QMessageBox.information(self, "No Selection", "Please select a document record.")
            return
        doc_id = int(self.table.item(row_idx, 0).text())
        with get_session() as session:
            record = session.get(DocumentRecord, doc_id)
            if record:
                record.status = new_status
                if new_status == "Approved":
                    record.approved_by = SessionManager.current_user().full_name
        log_audit(SessionManager.current_user().id, f"DOCUMENT_{new_status.upper()}", entity="DocumentRecord", entity_id=doc_id)
        self.refresh()
