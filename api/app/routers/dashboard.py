from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import db_dependency
from ..models import Item, IssueRecord, ReturnRecord, PrintingRecord, DocumentRecord, Notification
from ..schemas import DashboardOut
from ..security import require_permission

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
def get_dashboard(db: Session = Depends(db_dependency), _user=Depends(require_permission("view_dashboard"))):
    today = dt.date.today()
    items = db.query(Item).all()

    total_items = len(items)
    available_stock = sum(i.current_quantity for i in items)
    low_stock = sum(1 for i in items if i.is_low_stock and not i.is_out_of_stock)
    out_of_stock = sum(1 for i in items if i.is_out_of_stock)

    today_issued = db.query(IssueRecord).filter(IssueRecord.issue_date == today).count()
    today_returned = db.query(ReturnRecord).filter(ReturnRecord.return_date == today).count()
    today_printing = db.query(PrintingRecord).filter(PrintingRecord.print_date == today).count()
    pending_docs = db.query(DocumentRecord).filter(DocumentRecord.status == "Pending").count()

    notifications = db.query(Notification).order_by(Notification.created_at.desc()).limit(15).all()
    recent_issues = db.query(IssueRecord).order_by(IssueRecord.id.desc()).limit(5).all()
    recent_prints = db.query(PrintingRecord).order_by(PrintingRecord.id.desc()).limit(5).all()
    recent_docs = db.query(DocumentRecord).order_by(DocumentRecord.id.desc()).limit(5).all()

    recent_activity = (
        [f"Issued x{r.quantity} to teacher #{r.teacher_id} on {r.issue_date}" for r in recent_issues]
        + [f"Printing job '{p.document_name}' for {p.teacher_name}" for p in recent_prints]
        + [f"Document '{d.title}' - {d.status}" for d in recent_docs]
    )

    labels, issue_counts, print_counts = [], [], []
    for i in range(5, -1, -1):
        month_date = today.replace(day=1) - dt.timedelta(days=30 * i)
        labels.append(month_date.strftime("%b"))
        month_start = month_date.replace(day=1)
        next_month = (month_date.replace(year=month_date.year + 1, month=1, day=1) if month_date.month == 12
                      else month_date.replace(month=month_date.month + 1, day=1))
        issue_counts.append(db.query(IssueRecord).filter(
            IssueRecord.issue_date >= month_start, IssueRecord.issue_date < next_month).count())
        print_counts.append(db.query(PrintingRecord).filter(
            PrintingRecord.print_date >= month_start, PrintingRecord.print_date < next_month).count())

    return DashboardOut(
        total_items=total_items, available_stock=available_stock, low_stock=low_stock,
        out_of_stock=out_of_stock, today_issued=today_issued, today_returned=today_returned,
        today_printing=today_printing, pending_docs=pending_docs,
        notifications=[n.message for n in notifications] or ["No active notifications."],
        recent_activity=recent_activity,
        monthly_labels=labels, monthly_issue_counts=issue_counts, monthly_print_counts=print_counts,
    )
