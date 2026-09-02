"""
ui/inventory.py
Inventory management: list, search/filter, add, edit, delete, and
barcode/QR generation for stock items.
"""

from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QPushButton, QHBoxLayout, QWidget
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from database.database import get_session
from database.models import Item, Category, Supplier
from ui.widgets.table_page import TablePage
from ui.widgets.form_dialog import FormDialog, FieldSpec
from utils.helpers import generate_barcode_number, generate_qr_code_image, format_currency
from auth.authentication import SessionManager, log_audit
from auth.permissions import has_permission

COLUMNS = [
    "ID", "Barcode", "Category", "Name", "Brand", "Supplier", "Unit",
    "Qty", "Min Qty", "Purchase Cost", "Selling Cost", "Location", "Status"
]


class InventoryPage(TablePage):
    def __init__(self, parent=None):
        with get_session() as session:
            category_names = [c.name for c in session.query(Category).order_by(Category.name).all()]
        super().__init__(
            "Inventory Management", COLUMNS,
            add_label="+ Add Item",
            show_add_button=has_permission(SessionManager.current_user().role, "manage_inventory"),
            extra_filter_options=category_names,
            parent=parent,
        )
        self.can_manage = has_permission(SessionManager.current_user().role, "manage_inventory")
        self._add_action_buttons()
        self.refresh()

    def _add_action_buttons(self):
        if not self.can_manage:
            return
        action_row = QHBoxLayout()
        edit_btn = QPushButton("Edit Selected")
        edit_btn.setObjectName("SecondaryButton")
        edit_btn.clicked.connect(self._edit_selected)
        delete_btn = QPushButton("Delete Selected")
        delete_btn.setObjectName("DangerButton")
        delete_btn.clicked.connect(self._delete_selected)
        action_row.addWidget(edit_btn)
        action_row.addWidget(delete_btn)
        action_row.addStretch()
        self.layout().insertLayout(1, action_row)

    def refresh(self):
        self._all_rows = []
        with get_session() as session:
            items = session.query(Item).order_by(Item.id.desc()).all()
            for item in items:
                self._all_rows.append([
                    item.id, item.barcode,
                    item.category.name if item.category else "-",
                    item.name, item.brand or "-",
                    item.supplier.name if item.supplier else "-",
                    item.unit, item.current_quantity, item.minimum_quantity,
                    format_currency(item.purchase_cost), format_currency(item.selling_cost),
                    item.storage_location or "-", item.status,
                ])
        self.set_rows(self._all_rows)

    def on_search(self, *_args):
        query = self.search_input.text().lower().strip()
        category_filter = self.filter_combo.currentText() if self.filter_combo else "All"
        filtered = []
        for row in self._all_rows:
            matches_query = (not query) or any(query in str(cell).lower() for cell in row)
            matches_category = (category_filter == "All") or (row[2] == category_filter)
            if matches_query and matches_category:
                filtered.append(row)
        self.set_rows(filtered)

    def on_add_clicked(self):
        with get_session() as session:
            categories = [c.name for c in session.query(Category).order_by(Category.name).all()]
            suppliers = [s.name for s in session.query(Supplier).order_by(Supplier.name).all()]

        fields = [
            FieldSpec("category", "Category", kind="combo", options=categories, required=True),
            FieldSpec("name", "Item Name", required=True),
            FieldSpec("description", "Description", kind="textarea"),
            FieldSpec("brand", "Brand"),
            FieldSpec("supplier", "Supplier", kind="combo", options=["-"] + suppliers),
            FieldSpec("purchase_date", "Purchase Date", kind="date"),
            FieldSpec("purchase_cost", "Purchase Cost", kind="float", maximum=1_000_000),
            FieldSpec("selling_cost", "Selling Cost", kind="float", maximum=1_000_000),
            FieldSpec("unit", "Unit", kind="combo", options=["pcs", "box", "ream", "pack", "dozen"]),
            FieldSpec("current_quantity", "Current Quantity", kind="int", maximum=100000),
            FieldSpec("minimum_quantity", "Minimum Quantity", kind="int", maximum=100000, default=10),
            FieldSpec("maximum_quantity", "Maximum Quantity", kind="int", maximum=1000000, default=1000),
            FieldSpec("storage_location", "Storage Location"),
            FieldSpec("status", "Status", kind="combo", options=["Active", "Discontinued", "Damaged"]),
            FieldSpec("notes", "Notes", kind="textarea"),
        ]
        dialog = FormDialog("Add Inventory Item", fields, parent=self)
        if dialog.exec():
            self._save_item(dialog.values)

    def _save_item(self, values, item_id=None):
        with get_session() as session:
            category = session.query(Category).filter(Category.name == values["category"]).first()
            supplier = None
            if values.get("supplier") and values["supplier"] != "-":
                supplier = session.query(Supplier).filter(Supplier.name == values["supplier"]).first()

            if item_id:
                item = session.get(Item, item_id)
            else:
                item = Item(barcode=generate_barcode_number())
                session.add(item)

            item.category_id = category.id if category else None
            item.name = values["name"]
            item.description = values.get("description", "")
            item.brand = values.get("brand", "")
            item.supplier_id = supplier.id if supplier else None
            item.purchase_date = values.get("purchase_date")
            item.purchase_cost = values.get("purchase_cost", 0)
            item.selling_cost = values.get("selling_cost", 0)
            item.unit = values.get("unit", "pcs")
            item.current_quantity = values.get("current_quantity", 0)
            item.minimum_quantity = values.get("minimum_quantity", 10)
            item.maximum_quantity = values.get("maximum_quantity", 1000)
            item.storage_location = values.get("storage_location", "")
            item.status = values.get("status", "Active")
            item.notes = values.get("notes", "")
            session.flush()

            try:
                item.qr_code_path = generate_qr_code_image(item.barcode, f"item_{item.id}_qr.png")
            except Exception:
                pass

        log_audit(SessionManager.current_user().id, "ITEM_SAVED", entity="Item", entity_id=item_id)
        self.refresh()

    def _edit_selected(self):
        row_idx = self.selected_row_index()
        if row_idx is None:
            QMessageBox.information(self, "No Selection", "Please select an item to edit.")
            return
        item_id = int(self.table.item(row_idx, 0).text())

        with get_session() as session:
            item = session.get(Item, item_id)
            if not item:
                return
            categories = [c.name for c in session.query(Category).order_by(Category.name).all()]
            suppliers = [s.name for s in session.query(Supplier).order_by(Supplier.name).all()]
            initial = {
                "category": item.category.name if item.category else "",
                "name": item.name,
                "description": item.description,
                "brand": item.brand,
                "supplier": item.supplier.name if item.supplier else "-",
                "purchase_date": item.purchase_date,
                "purchase_cost": item.purchase_cost,
                "selling_cost": item.selling_cost,
                "unit": item.unit,
                "current_quantity": item.current_quantity,
                "minimum_quantity": item.minimum_quantity,
                "maximum_quantity": item.maximum_quantity,
                "storage_location": item.storage_location,
                "status": item.status,
                "notes": item.notes,
            }

        fields = [
            FieldSpec("category", "Category", kind="combo", options=categories, required=True),
            FieldSpec("name", "Item Name", required=True),
            FieldSpec("description", "Description", kind="textarea"),
            FieldSpec("brand", "Brand"),
            FieldSpec("supplier", "Supplier", kind="combo", options=["-"] + suppliers),
            FieldSpec("purchase_date", "Purchase Date", kind="date"),
            FieldSpec("purchase_cost", "Purchase Cost", kind="float", maximum=1_000_000),
            FieldSpec("selling_cost", "Selling Cost", kind="float", maximum=1_000_000),
            FieldSpec("unit", "Unit", kind="combo", options=["pcs", "box", "ream", "pack", "dozen"]),
            FieldSpec("current_quantity", "Current Quantity", kind="int", maximum=100000),
            FieldSpec("minimum_quantity", "Minimum Quantity", kind="int", maximum=100000),
            FieldSpec("maximum_quantity", "Maximum Quantity", kind="int", maximum=1000000),
            FieldSpec("storage_location", "Storage Location"),
            FieldSpec("status", "Status", kind="combo", options=["Active", "Discontinued", "Damaged"]),
            FieldSpec("notes", "Notes", kind="textarea"),
        ]
        dialog = FormDialog("Edit Inventory Item", fields, initial=initial, parent=self)
        if dialog.exec():
            self._save_item(dialog.values, item_id=item_id)

    def _delete_selected(self):
        row_idx = self.selected_row_index()
        if row_idx is None:
            QMessageBox.information(self, "No Selection", "Please select an item to delete.")
            return
        item_id = int(self.table.item(row_idx, 0).text())
        confirm = QMessageBox.question(self, "Confirm Delete", "Delete this inventory item permanently?")
        if confirm != QMessageBox.Yes:
            return
        try:
            with get_session() as session:
                item = session.get(Item, item_id)
                if item:
                    session.delete(item)
        except IntegrityError:
            QMessageBox.warning(
                self, "Cannot Delete",
                "This item cannot be deleted because it is referenced by existing "
                "issue or purchase records."
            )
            return
        log_audit(SessionManager.current_user().id, "ITEM_DELETED", entity="Item", entity_id=item_id)
        self.refresh()
