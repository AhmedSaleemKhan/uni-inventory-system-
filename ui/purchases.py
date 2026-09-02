"""
ui/purchases.py
Purchase order management: create POs against suppliers, add line
items, compute totals with tax, and update stock on receipt.
"""

from __future__ import annotations

import datetime as dt

from PySide6.QtWidgets import (
    QMessageBox, QPushButton, QHBoxLayout, QDialog, QVBoxLayout, QFormLayout,
    QComboBox, QSpinBox, QDoubleSpinBox, QLabel, QListWidget, QListWidgetItem
)

from database.database import get_session
from database.models import PurchaseOrder, PurchaseItem, Supplier, Item
from ui.widgets.table_page import TablePage
from utils.helpers import generate_invoice_number, format_currency, format_date
from auth.authentication import SessionManager, log_audit
from auth.permissions import has_permission

COLUMNS = ["ID", "Invoice #", "Supplier", "Order Date", "Tax %", "Total Amount", "Payment Status"]


class PurchaseOrderDialog(QDialog):
    """Compact dialog to create a purchase order with multiple line items."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Purchase Order")
        self.setMinimumWidth(480)
        self.line_items: list[tuple[int, str, int, float]] = []  # item_id, name, qty, unit_cost

        with get_session() as session:
            self.suppliers = {s.name: s.id for s in session.query(Supplier).order_by(Supplier.name).all()}
            self.items = {i.name: (i.id, i.purchase_cost) for i in session.query(Item).order_by(Item.name).all()}

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.supplier_combo = QComboBox()
        self.supplier_combo.addItems(list(self.suppliers.keys()))
        form.addRow("Supplier:", self.supplier_combo)

        self.tax_spin = QDoubleSpinBox()
        self.tax_spin.setRange(0, 100)
        self.tax_spin.setValue(0)
        form.addRow("Tax %:", self.tax_spin)

        layout.addLayout(form)

        item_row = QHBoxLayout()
        self.item_combo = QComboBox()
        self.item_combo.addItems(list(self.items.keys()))
        self.item_combo.currentTextChanged.connect(self._on_item_selected)
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 100000)
        self.unit_cost_spin = QDoubleSpinBox()
        self.unit_cost_spin.setRange(0, 1_000_000)
        add_line_btn = QPushButton("Add Line")
        add_line_btn.clicked.connect(self._add_line)
        item_row.addWidget(self.item_combo)
        item_row.addWidget(self.qty_spin)
        item_row.addWidget(self.unit_cost_spin)
        item_row.addWidget(add_line_btn)
        layout.addLayout(item_row)
        self._on_item_selected(self.item_combo.currentText())

        self.lines_list = QListWidget()
        layout.addWidget(self.lines_list)

        self.total_label = QLabel("Total: Rs. 0.00")
        layout.addWidget(self.total_label)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("SecondaryButton")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Create Purchase Order")
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _on_item_selected(self, name: str):
        if name in self.items:
            _, cost = self.items[name]
            self.unit_cost_spin.setValue(cost)

    def _add_line(self):
        name = self.item_combo.currentText()
        if not name:
            return
        item_id, _ = self.items[name]
        qty = self.qty_spin.value()
        unit_cost = self.unit_cost_spin.value()
        self.line_items.append((item_id, name, qty, unit_cost))
        line_total = qty * unit_cost
        QListWidgetItem(f"{name} x{qty} @ {format_currency(unit_cost)} = {format_currency(line_total)}", self.lines_list)
        self._update_total()

    def _update_total(self):
        subtotal = sum(qty * cost for _, _, qty, cost in self.line_items)
        tax = subtotal * (self.tax_spin.value() / 100)
        self.total_label.setText(f"Total: {format_currency(subtotal + tax)}")

    def _on_save(self):
        if not self.line_items:
            QMessageBox.warning(self, "No Items", "Please add at least one line item.")
            return
        self.accept()


class PurchasesPage(TablePage):
    def __init__(self, parent=None):
        self.can_manage = has_permission(SessionManager.current_user().role, "manage_purchases")
        super().__init__("Purchase Orders", COLUMNS, add_label="+ New Purchase Order",
                          show_add_button=self.can_manage, parent=parent)
        self._add_action_buttons()
        self.refresh()

    def _add_action_buttons(self):
        if not self.can_manage:
            return
        row = QHBoxLayout()
        mark_paid_btn = QPushButton("Mark Paid")
        mark_paid_btn.setObjectName("SuccessButton")
        mark_paid_btn.clicked.connect(lambda: self._update_payment_status("Paid"))
        row.addWidget(mark_paid_btn)
        row.addStretch()
        self.layout().insertLayout(1, row)

    def refresh(self):
        self._all_rows = []
        with get_session() as session:
            for po in session.query(PurchaseOrder).order_by(PurchaseOrder.id.desc()).all():
                self._all_rows.append([
                    po.id, po.invoice_number, po.supplier.name if po.supplier else "-",
                    format_date(po.order_date), po.tax_percent,
                    format_currency(po.total_amount), po.payment_status,
                ])
        self.set_rows(self._all_rows)

    def on_search(self, *_args):
        query = self.search_input.text().lower().strip()
        filtered = [row for row in self._all_rows if (not query) or any(query in str(c).lower() for c in row)]
        self.set_rows(filtered)

    def on_add_clicked(self):
        dialog = PurchaseOrderDialog(parent=self)
        if dialog.exec():
            self._save_purchase_order(dialog)

    def _save_purchase_order(self, dialog: PurchaseOrderDialog):
        with get_session() as session:
            supplier_id = dialog.suppliers[dialog.supplier_combo.currentText()]
            tax_percent = dialog.tax_spin.value()

            po = PurchaseOrder(
                invoice_number=generate_invoice_number(),
                supplier_id=supplier_id,
                order_date=dt.date.today(),
                tax_percent=tax_percent,
                payment_status="Unpaid",
            )
            session.add(po)
            session.flush()

            subtotal = 0.0
            for item_id, _name, qty, unit_cost in dialog.line_items:
                line_total = qty * unit_cost
                subtotal += line_total
                session.add(PurchaseItem(
                    purchase_order_id=po.id, item_id=item_id,
                    quantity=qty, unit_cost=unit_cost, line_total=line_total,
                ))
                item = session.get(Item, item_id)
                if item:
                    item.current_quantity += qty  # stock update on receipt

            po.total_amount = round(subtotal * (1 + tax_percent / 100), 2)

        log_audit(SessionManager.current_user().id, "PURCHASE_ORDER_CREATED", entity="PurchaseOrder")
        self.refresh()
        QMessageBox.information(self, "Success", "Purchase order created and stock updated.")

    def _update_payment_status(self, status: str):
        row_idx = self.selected_row_index()
        if row_idx is None:
            QMessageBox.information(self, "No Selection", "Please select a purchase order.")
            return
        po_id = int(self.table.item(row_idx, 0).text())
        with get_session() as session:
            po = session.get(PurchaseOrder, po_id)
            if po:
                po.payment_status = status
        self.refresh()
