"""
ui/reports.py
Central reporting hub: generates Inventory, Teacher, Printing, Issue,
Return, Purchase, Supplier, Low Stock, and Pending reports, exportable
to PDF, Excel, and CSV.
"""

from __future__ import annotations

import csv
import datetime as dt

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox,
    QAbstractItemView
)
import openpyxl

from database.database import get_session
from database.models import (
    Item, Teacher, PrintingRecord, IssueRecord, ReturnRecord,
    PurchaseOrder, Supplier, DocumentRecord
)
from utils.helpers import format_currency, format_date
from utils.pdf_reports import generate_tabular_report
import config

REPORT_TYPES = [
    "Inventory Report", "Low Stock Report", "Teacher Report",
    "Printing Report", "Issue Report", "Return Report",
    "Purchase Report", "Supplier Report", "Pending Documents Report",
]


def _build_report_data(report_type: str) -> tuple[list[str], list[list]]:
    with get_session() as session:
        if report_type == "Inventory Report":
            headers = ["ID", "Barcode", "Category", "Name", "Qty", "Min Qty", "Unit", "Status"]
            rows = [[i.id, i.barcode, i.category.name if i.category else "-", i.name,
                     i.current_quantity, i.minimum_quantity, i.unit, i.status]
                    for i in session.query(Item).all()]

        elif report_type == "Low Stock Report":
            headers = ["ID", "Name", "Category", "Current Qty", "Minimum Qty", "Storage Location"]
            rows = [[i.id, i.name, i.category.name if i.category else "-",
                     i.current_quantity, i.minimum_quantity, i.storage_location or "-"]
                    for i in session.query(Item).all() if i.is_low_stock]

        elif report_type == "Teacher Report":
            headers = ["ID", "Employee ID", "Name", "Department", "Designation", "Status"]
            rows = [[t.id, t.employee_id, t.name, t.department, t.designation, t.status]
                    for t in session.query(Teacher).all()]

        elif report_type == "Printing Report":
            headers = ["ID", "Teacher", "Document", "Mode", "Pages", "Copies", "Cost", "Date"]
            rows = [[p.id, p.teacher_name, p.document_name, p.color_mode, p.pages,
                     p.copies, format_currency(p.cost), format_date(p.print_date)]
                    for p in session.query(PrintingRecord).all()]

        elif report_type == "Issue Report":
            headers = ["ID", "Teacher", "Item", "Qty", "Issue Date", "Status"]
            rows = [[r.id, r.teacher.name if r.teacher else "-", r.item.name if r.item else "-",
                     r.quantity, format_date(r.issue_date), r.status]
                    for r in session.query(IssueRecord).all()]

        elif report_type == "Return Report":
            headers = ["Issue ID", "Returned Qty", "Return Date", "Condition", "Late?"]
            rows = [[rr.issue_id, rr.returned_quantity, format_date(rr.return_date),
                     rr.condition, "Yes" if rr.is_late else "No"]
                    for rr in session.query(ReturnRecord).all()]

        elif report_type == "Purchase Report":
            headers = ["ID", "Invoice #", "Supplier", "Order Date", "Total", "Payment Status"]
            rows = [[po.id, po.invoice_number, po.supplier.name if po.supplier else "-",
                     format_date(po.order_date), format_currency(po.total_amount), po.payment_status]
                    for po in session.query(PurchaseOrder).all()]

        elif report_type == "Supplier Report":
            headers = ["ID", "Name", "Phone", "Email", "GST Number"]
            rows = [[s.id, s.name, s.phone or "-", s.email or "-", s.gst_number or "-"]
                    for s in session.query(Supplier).all()]

        elif report_type == "Pending Documents Report":
            headers = ["ID", "Type", "Title", "Department", "Received Date"]
            rows = [[d.id, d.document_type, d.title, d.department or "-", format_date(d.received_date)]
                    for d in session.query(DocumentRecord).filter(DocumentRecord.status == "Pending").all()]

        else:
            headers, rows = [], []

    return headers, rows


class ReportsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._on_generate()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("Reports Center")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        controls = QHBoxLayout()
        self.report_combo = QComboBox()
        self.report_combo.addItems(REPORT_TYPES)
        self.report_combo.currentTextChanged.connect(self._on_generate)

        generate_btn = QPushButton("Generate")
        generate_btn.clicked.connect(self._on_generate)

        export_pdf_btn = QPushButton("Export PDF")
        export_pdf_btn.setObjectName("SecondaryButton")
        export_pdf_btn.clicked.connect(lambda: self._export("pdf"))

        export_excel_btn = QPushButton("Export Excel")
        export_excel_btn.setObjectName("SecondaryButton")
        export_excel_btn.clicked.connect(lambda: self._export("xlsx"))

        export_csv_btn = QPushButton("Export CSV")
        export_csv_btn.setObjectName("SecondaryButton")
        export_csv_btn.clicked.connect(lambda: self._export("csv"))

        controls.addWidget(QLabel("Report Type:"))
        controls.addWidget(self.report_combo)
        controls.addWidget(generate_btn)
        controls.addStretch()
        controls.addWidget(export_pdf_btn)
        controls.addWidget(export_excel_btn)
        controls.addWidget(export_csv_btn)
        layout.addLayout(controls)

        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self.row_count_label = QLabel("0 records")
        layout.addWidget(self.row_count_label)

    def _on_generate(self, *_args):
        report_type = self.report_combo.currentText()
        headers, rows = _build_report_data(report_type)
        self._current_headers = headers
        self._current_rows = rows
        self._current_report_type = report_type

        self.table.setSortingEnabled(False)
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(rows))
        for r, row_data in enumerate(rows):
            for c, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                self.table.setItem(r, c, item)
        self.table.setSortingEnabled(True)
        self.row_count_label.setText(f"{len(rows)} records")

    def _export(self, fmt: str):
        if not self._current_rows:
            QMessageBox.information(self, "No Data", "There is no data to export for this report.")
            return

        safe_name = self._current_report_type.lower().replace(" ", "_")
        default_path = str(config.EXPORTS_DIR / f"{safe_name}.{fmt}")
        filter_map = {"pdf": "PDF Files (*.pdf)", "xlsx": "Excel Files (*.xlsx)", "csv": "CSV Files (*.csv)"}
        path, _ = QFileDialog.getSaveFileName(self, f"Export {fmt.upper()}", default_path, filter_map[fmt])
        if not path:
            return

        if fmt == "pdf":
            generate_tabular_report(self._current_report_type, self._current_headers, self._current_rows, path)
        elif fmt == "xlsx":
            self._export_excel(path)
        elif fmt == "csv":
            self._export_csv(path)

        QMessageBox.information(self, "Export Complete", f"Report exported to:\n{path}")

    def _export_excel(self, path: str):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = self._current_report_type[:31]
        ws.append(self._current_headers)
        for row in self._current_rows:
            ws.append(list(row))
        for col_cells in ws.columns:
            max_len = max(len(str(c.value)) for c in col_cells if c.value is not None) if col_cells else 10
            ws.column_dimensions[col_cells[0].column_letter].width = min(max(max_len + 2, 10), 40)
        wb.save(path)

    def _export_csv(self, path: str):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self._current_headers)
            writer.writerows(self._current_rows)
