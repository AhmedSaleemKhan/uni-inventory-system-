"""
ui/suppliers.py
Supplier management: contact info, GST, and linked purchase history.
"""

from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QPushButton, QHBoxLayout
from sqlalchemy.exc import IntegrityError

from database.database import get_session
from database.models import Supplier, PurchaseOrder
from ui.widgets.table_page import TablePage
from ui.widgets.form_dialog import FormDialog, FieldSpec
from utils.helpers import format_currency
from auth.authentication import SessionManager, log_audit
from auth.permissions import has_permission

COLUMNS = ["ID", "Name", "Phone", "Email", "GST Number", "Address", "Total Purchases"]


class SuppliersPage(TablePage):
    def __init__(self, parent=None):
        self.can_manage = has_permission(SessionManager.current_user().role, "manage_suppliers")
        super().__init__("Supplier Management", COLUMNS, add_label="+ Add Supplier",
                          show_add_button=self.can_manage, parent=parent)
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
            for s in session.query(Supplier).order_by(Supplier.id.desc()).all():
                total_purchases = sum(po.total_amount for po in s.purchase_orders)
                self._all_rows.append([
                    s.id, s.name, s.phone or "-", s.email or "-",
                    s.gst_number or "-", s.address or "-", format_currency(total_purchases),
                ])
        self.set_rows(self._all_rows)

    def on_search(self, *_args):
        query = self.search_input.text().lower().strip()
        filtered = [row for row in self._all_rows if (not query) or any(query in str(c).lower() for c in row)]
        self.set_rows(filtered)

    def _field_specs(self):
        return [
            FieldSpec("name", "Supplier Name", required=True),
            FieldSpec("address", "Address", kind="textarea"),
            FieldSpec("phone", "Phone"),
            FieldSpec("email", "Email"),
            FieldSpec("gst_number", "GST Number"),
            FieldSpec("notes", "Notes", kind="textarea"),
        ]

    def on_add_clicked(self):
        dialog = FormDialog("Add Supplier", self._field_specs(), parent=self)
        if dialog.exec():
            self._save_supplier(dialog.values)

    def _save_supplier(self, values, supplier_id=None):
        with get_session() as session:
            if supplier_id:
                supplier = session.get(Supplier, supplier_id)
            else:
                supplier = Supplier()
                session.add(supplier)
            supplier.name = values["name"]
            supplier.address = values.get("address", "")
            supplier.phone = values.get("phone", "")
            supplier.email = values.get("email", "")
            supplier.gst_number = values.get("gst_number", "")
            supplier.notes = values.get("notes", "")
        log_audit(SessionManager.current_user().id, "SUPPLIER_SAVED", entity="Supplier", entity_id=supplier_id)
        self.refresh()

    def _edit_selected(self):
        row_idx = self.selected_row_index()
        if row_idx is None:
            QMessageBox.information(self, "No Selection", "Please select a supplier to edit.")
            return
        supplier_id = int(self.table.item(row_idx, 0).text())
        with get_session() as session:
            supplier = session.get(Supplier, supplier_id)
            if not supplier:
                return
            initial = {
                "name": supplier.name, "address": supplier.address,
                "phone": supplier.phone, "email": supplier.email,
                "gst_number": supplier.gst_number, "notes": supplier.notes,
            }
        dialog = FormDialog("Edit Supplier", self._field_specs(), initial=initial, parent=self)
        if dialog.exec():
            self._save_supplier(dialog.values, supplier_id=supplier_id)

    def _delete_selected(self):
        row_idx = self.selected_row_index()
        if row_idx is None:
            QMessageBox.information(self, "No Selection", "Please select a supplier to delete.")
            return
        supplier_id = int(self.table.item(row_idx, 0).text())
        confirm = QMessageBox.question(self, "Confirm Delete", "Delete this supplier permanently?")
        if confirm != QMessageBox.Yes:
            return
        try:
            with get_session() as session:
                supplier = session.get(Supplier, supplier_id)
                if supplier:
                    session.delete(supplier)
        except IntegrityError:
            QMessageBox.warning(
                self, "Cannot Delete",
                "This supplier cannot be deleted because they have existing items "
                "or purchase orders linked to them."
            )
            return
        log_audit(SessionManager.current_user().id, "SUPPLIER_DELETED", entity="Supplier", entity_id=supplier_id)
        self.refresh()
