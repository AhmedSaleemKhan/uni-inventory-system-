"""
ui/dashboard.py
Main dashboard: KPI stat cards, monthly chart, low-stock and recent
activity panels.
"""

from __future__ import annotations

import datetime as dt

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
    QListWidget, QListWidgetItem, QSizePolicy
)
from PySide6.QtCore import Qt

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from database.database import get_session
from database.models import (
    Item, IssueRecord, ReturnRecord, PrintingRecord, DocumentRecord, Notification
)
from ui.components.stat_card import StatCard
import config


class DashboardPage(QWidget):
    def __init__(self, session_user, parent=None):
        super().__init__(parent)
        self.session_user = session_user
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)

        header = QLabel(f"Welcome back, {self.session_user.full_name}")
        header.setObjectName("PageTitle")
        layout.addWidget(header)

        # Stat cards grid
        self.stats_grid = QGridLayout()
        self.stats_grid.setSpacing(14)
        layout.addLayout(self.stats_grid)

        self.card_total_inventory = StatCard("Total Inventory Items", "0", config.THEME_PRIMARY)
        self.card_available_stock = StatCard("Available Stock (units)", "0", config.THEME_SUCCESS)
        self.card_low_stock = StatCard("Low Stock Items", "0", config.THEME_ACCENT)
        self.card_out_of_stock = StatCard("Out of Stock Items", "0", config.THEME_DANGER)
        self.card_today_issued = StatCard("Today's Issued Items", "0", config.THEME_PRIMARY)
        self.card_today_returned = StatCard("Today's Returned Items", "0", config.THEME_PRIMARY)
        self.card_today_printing = StatCard("Today's Printing Jobs", "0", config.THEME_PRIMARY)
        self.card_pending_docs = StatCard("Pending Documents", "0", config.THEME_ACCENT)

        cards = [
            self.card_total_inventory, self.card_available_stock,
            self.card_low_stock, self.card_out_of_stock,
            self.card_today_issued, self.card_today_returned,
            self.card_today_printing, self.card_pending_docs,
        ]
        for i, card in enumerate(cards):
            self.stats_grid.addWidget(card, i // 4, i % 4)

        # Middle row: chart + notifications
        middle_row = QHBoxLayout()
        middle_row.setSpacing(16)

        chart_card = QFrame()
        chart_card.setObjectName("Card")
        chart_layout = QVBoxLayout(chart_card)
        chart_title = QLabel("Monthly Activity Overview")
        chart_title.setStyleSheet("font-weight: 600; font-size: 14px;")
        chart_layout.addWidget(chart_title)

        self.figure = Figure(figsize=(5, 3), tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)

        notif_card = QFrame()
        notif_card.setObjectName("Card")
        notif_card.setMaximumWidth(320)
        notif_layout = QVBoxLayout(notif_card)
        notif_title = QLabel("Notifications & Alerts")
        notif_title.setStyleSheet("font-weight: 600; font-size: 14px;")
        self.notif_list = QListWidget()
        notif_layout.addWidget(notif_title)
        notif_layout.addWidget(self.notif_list)

        middle_row.addWidget(chart_card, 2)
        middle_row.addWidget(notif_card, 1)
        layout.addLayout(middle_row)

        # Recent activities
        recent_card = QFrame()
        recent_card.setObjectName("Card")
        recent_layout = QVBoxLayout(recent_card)
        recent_title = QLabel("Recent Activities")
        recent_title.setStyleSheet("font-weight: 600; font-size: 14px;")
        self.recent_list = QListWidget()
        self.recent_list.setMaximumHeight(180)
        recent_layout.addWidget(recent_title)
        recent_layout.addWidget(self.recent_list)
        layout.addWidget(recent_card)

    def refresh(self):
        today = dt.date.today()
        with get_session() as session:
            total_items = session.query(Item).count()
            available_stock = sum(i.current_quantity for i in session.query(Item).all())
            low_stock = sum(1 for i in session.query(Item).all() if i.is_low_stock and not i.is_out_of_stock)
            out_of_stock = sum(1 for i in session.query(Item).all() if i.is_out_of_stock)

            today_issued = session.query(IssueRecord).filter(IssueRecord.issue_date == today).count()
            today_returned = session.query(ReturnRecord).filter(ReturnRecord.return_date == today).count()
            today_printing = session.query(PrintingRecord).filter(PrintingRecord.print_date == today).count()
            pending_docs = session.query(DocumentRecord).filter(DocumentRecord.status == "Pending").count()

            notifications = session.query(Notification).order_by(Notification.created_at.desc()).limit(15).all()

            # Recent activities: latest issues + printing + documents combined
            recent_issues = session.query(IssueRecord).order_by(IssueRecord.id.desc()).limit(5).all()
            recent_prints = session.query(PrintingRecord).order_by(PrintingRecord.id.desc()).limit(5).all()
            recent_docs = session.query(DocumentRecord).order_by(DocumentRecord.id.desc()).limit(5).all()

            monthly_labels, monthly_issue_counts, monthly_print_counts = self._monthly_series(session)

            self.card_total_inventory.set_value(str(total_items))
            self.card_available_stock.set_value(str(available_stock))
            self.card_low_stock.set_value(str(low_stock))
            self.card_out_of_stock.set_value(str(out_of_stock))
            self.card_today_issued.set_value(str(today_issued))
            self.card_today_returned.set_value(str(today_returned))
            self.card_today_printing.set_value(str(today_printing))
            self.card_pending_docs.set_value(str(pending_docs))

            self.notif_list.clear()
            for n in notifications:
                icon = "⚠️" if n.category in ("LowStock", "OutOfStock") else "🔔"
                QListWidgetItem(f"{icon} {n.message}", self.notif_list)
            if not notifications:
                QListWidgetItem("No active notifications.", self.notif_list)

            self.recent_list.clear()
            for r in recent_issues:
                QListWidgetItem(f"📦 Issued x{r.quantity} to teacher #{r.teacher_id} on {r.issue_date}", self.recent_list)
            for p in recent_prints:
                QListWidgetItem(f"🖨️ Printing job '{p.document_name}' for {p.teacher_name}", self.recent_list)
            for d in recent_docs:
                QListWidgetItem(f"📄 Document '{d.title}' - {d.status}", self.recent_list)

        self._draw_chart(monthly_labels, monthly_issue_counts, monthly_print_counts)

    def _monthly_series(self, session):
        labels = []
        issue_counts = []
        print_counts = []
        today = dt.date.today()
        for i in range(5, -1, -1):
            month_date = (today.replace(day=1) - dt.timedelta(days=30 * i))
            month_label = month_date.strftime("%b")
            labels.append(month_label)

            month_start = month_date.replace(day=1)
            if month_date.month == 12:
                next_month = month_date.replace(year=month_date.year + 1, month=1, day=1)
            else:
                next_month = month_date.replace(month=month_date.month + 1, day=1)

            issue_count = session.query(IssueRecord).filter(
                IssueRecord.issue_date >= month_start, IssueRecord.issue_date < next_month
            ).count()
            print_count = session.query(PrintingRecord).filter(
                PrintingRecord.print_date >= month_start, PrintingRecord.print_date < next_month
            ).count()
            issue_counts.append(issue_count)
            print_counts.append(print_count)
        return labels, issue_counts, print_counts

    def _draw_chart(self, labels, issue_counts, print_counts):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        x = range(len(labels))
        width = 0.35
        ax.bar([i - width / 2 for i in x], issue_counts, width, label="Issues", color=config.THEME_PRIMARY)
        ax.bar([i + width / 2 for i in x], print_counts, width, label="Printing", color=config.THEME_ACCENT)
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels)
        ax.legend(fontsize=8)
        ax.tick_params(labelsize=8)
        self.canvas.draw()
