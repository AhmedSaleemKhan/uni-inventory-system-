"""
ui/teachers.py
Teacher management: list, search, add, edit, delete faculty records.
"""

from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QPushButton, QHBoxLayout
from sqlalchemy.exc import IntegrityError

from database.database import get_session
from database.models import Teacher
from ui.widgets.table_page import TablePage
from ui.widgets.form_dialog import FormDialog, FieldSpec
from utils.helpers import generate_employee_id
from auth.authentication import SessionManager, log_audit
from auth.permissions import has_permission

COLUMNS = ["ID", "Employee ID", "Name", "Department", "Designation", "Phone", "Email", "Office", "Status"]

DEPARTMENTS = [
    "Computer Science", "Software Engineering", "Electrical Engineering",
    "Mechanical Engineering", "Civil Engineering", "Business Administration",
    "Applied Physics", "Mathematics", "English", "Humanities",
]
DESIGNATIONS = ["Lecturer", "Assistant Professor", "Associate Professor", "Professor", "Visiting Faculty"]


class TeachersPage(TablePage):
    def __init__(self, parent=None):
        self.can_manage = has_permission(SessionManager.current_user().role, "manage_teachers")
        super().__init__(
            "Teacher Management", COLUMNS, add_label="+ Add Teacher",
            show_add_button=self.can_manage,
            extra_filter_options=DEPARTMENTS, parent=parent,
        )
        self._add_action_buttons()
        self.refresh()

    def _add_action_buttons(self):
        if not self.can_manage:
            return
        row = QHBoxLayout()
        edit_btn = QPushButton("Edit Selected")
        edit_btn.setObjectName("SecondaryButton")
        edit_btn.clicked.connect(self._edit_selected)
        delete_btn = QPushButton("Delete Selected")
        delete_btn.setObjectName("DangerButton")
        delete_btn.clicked.connect(self._delete_selected)
        row.addWidget(edit_btn)
        row.addWidget(delete_btn)
        row.addStretch()
        self.layout().insertLayout(1, row)

    def refresh(self):
        self._all_rows = []
        with get_session() as session:
            for t in session.query(Teacher).order_by(Teacher.id.desc()).all():
                self._all_rows.append([
                    t.id, t.employee_id, t.name, t.department, t.designation,
                    t.phone or "-", t.email or "-", t.office_number or "-", t.status,
                ])
        self.set_rows(self._all_rows)

    def on_search(self, *_args):
        query = self.search_input.text().lower().strip()
        dept_filter = self.filter_combo.currentText() if self.filter_combo else "All"
        filtered = [
            row for row in self._all_rows
            if ((not query) or any(query in str(c).lower() for c in row))
            and (dept_filter == "All" or row[3] == dept_filter)
        ]
        self.set_rows(filtered)

    def _field_specs(self):
        return [
            FieldSpec("name", "Full Name", required=True),
            FieldSpec("department", "Department", kind="combo", options=DEPARTMENTS, required=True),
            FieldSpec("designation", "Designation", kind="combo", options=DESIGNATIONS),
            FieldSpec("phone", "Phone"),
            FieldSpec("email", "Email"),
            FieldSpec("office_number", "Office Number"),
            FieldSpec("assigned_courses", "Assigned Courses (comma separated)", kind="textarea"),
            FieldSpec("status", "Status", kind="combo", options=["Active", "On Leave", "Retired"]),
        ]

    def on_add_clicked(self):
        dialog = FormDialog("Add Teacher", self._field_specs(), parent=self)
        if dialog.exec():
            self._save_teacher(dialog.values)

    def _save_teacher(self, values, teacher_id=None):
        with get_session() as session:
            if teacher_id:
                teacher = session.get(Teacher, teacher_id)
            else:
                teacher = Teacher(employee_id=generate_employee_id("FAC"))
                session.add(teacher)
            teacher.name = values["name"]
            teacher.department = values["department"]
            teacher.designation = values.get("designation", "Lecturer")
            teacher.phone = values.get("phone", "")
            teacher.email = values.get("email", "")
            teacher.office_number = values.get("office_number", "")
            teacher.assigned_courses = values.get("assigned_courses", "")
            teacher.status = values.get("status", "Active")
        log_audit(SessionManager.current_user().id, "TEACHER_SAVED", entity="Teacher", entity_id=teacher_id)
        self.refresh()

    def _edit_selected(self):
        row_idx = self.selected_row_index()
        if row_idx is None:
            QMessageBox.information(self, "No Selection", "Please select a teacher to edit.")
            return
        teacher_id = int(self.table.item(row_idx, 0).text())
        with get_session() as session:
            teacher = session.get(Teacher, teacher_id)
            if not teacher:
                return
            initial = {
                "name": teacher.name, "department": teacher.department,
                "designation": teacher.designation, "phone": teacher.phone,
                "email": teacher.email, "office_number": teacher.office_number,
                "assigned_courses": teacher.assigned_courses, "status": teacher.status,
            }
        dialog = FormDialog("Edit Teacher", self._field_specs(), initial=initial, parent=self)
        if dialog.exec():
            self._save_teacher(dialog.values, teacher_id=teacher_id)

    def _delete_selected(self):
        row_idx = self.selected_row_index()
        if row_idx is None:
            QMessageBox.information(self, "No Selection", "Please select a teacher to delete.")
            return
        teacher_id = int(self.table.item(row_idx, 0).text())
        confirm = QMessageBox.question(self, "Confirm Delete", "Delete this teacher record permanently?")
        if confirm != QMessageBox.Yes:
            return
        try:
            with get_session() as session:
                teacher = session.get(Teacher, teacher_id)
                if teacher:
                    session.delete(teacher)
        except IntegrityError:
            QMessageBox.warning(
                self, "Cannot Delete",
                "This teacher cannot be deleted because they have existing issue, "
                "printing, or document records."
            )
            return
        log_audit(SessionManager.current_user().id, "TEACHER_DELETED", entity="Teacher", entity_id=teacher_id)
        self.refresh()
