from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import db_dependency
from ..models import PurchaseOrder, PurchaseItem, Supplier, Item
from ..schemas import PurchaseOrderIn, PurchaseOrderOut
from ..security import require_permission, log_audit, CurrentUser
from ..helpers import generate_invoice_number

router = APIRouter(prefix="/api/purchases", tags=["purchases"])


@router.get("", response_model=list[PurchaseOrderOut])
def list_purchases(db: Session = Depends(db_dependency), _u: CurrentUser = Depends(require_permission("manage_purchases"))):
    orders = db.query(PurchaseOrder).order_by(PurchaseOrder.id.desc()).all()
    return [
        PurchaseOrderOut(id=po.id, invoice_number=po.invoice_number, supplier=po.supplier.name if po.supplier else "-",
                         order_date=po.order_date, tax_percent=po.tax_percent, total_amount=po.total_amount,
                         payment_status=po.payment_status)
        for po in orders
    ]


@router.post("", response_model=PurchaseOrderOut)
def create_purchase(payload: PurchaseOrderIn, db: Session = Depends(db_dependency),
                     user: CurrentUser = Depends(require_permission("manage_purchases"))):
    supplier = db.query(Supplier).filter(Supplier.name == payload.supplier).first()
    if not supplier:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown supplier")
    if not payload.lines:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Please add at least one line item.")

    po = PurchaseOrder(invoice_number=generate_invoice_number(), supplier_id=supplier.id,
                        order_date=dt.date.today(), tax_percent=payload.tax_percent, payment_status="Unpaid")
    db.add(po)
    db.flush()

    subtotal = 0.0
    for line in payload.lines:
        item = db.query(Item).filter(Item.name == line.item).first()
        if not item:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown item '{line.item}'")
        line_total = line.quantity * line.unit_cost
        subtotal += line_total
        db.add(PurchaseItem(purchase_order_id=po.id, item_id=item.id, quantity=line.quantity,
                             unit_cost=line.unit_cost, line_total=line_total))
        item.current_quantity += line.quantity

    po.total_amount = round(subtotal * (1 + payload.tax_percent / 100), 2)
    db.flush()
    log_audit(db, user.id, "PURCHASE_ORDER_CREATED", entity="PurchaseOrder", entity_id=po.id)
    db.refresh(po)
    return PurchaseOrderOut(id=po.id, invoice_number=po.invoice_number, supplier=supplier.name,
                             order_date=po.order_date, tax_percent=po.tax_percent, total_amount=po.total_amount,
                             payment_status=po.payment_status)


@router.post("/{po_id}/mark-paid", response_model=PurchaseOrderOut)
def mark_paid(po_id: int, db: Session = Depends(db_dependency),
              user: CurrentUser = Depends(require_permission("manage_purchases"))):
    po = db.get(PurchaseOrder, po_id)
    if not po:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Purchase order not found")
    po.payment_status = "Paid"
    db.flush()
    return PurchaseOrderOut(id=po.id, invoice_number=po.invoice_number, supplier=po.supplier.name if po.supplier else "-",
                             order_date=po.order_date, tax_percent=po.tax_percent, total_amount=po.total_amount,
                             payment_status=po.payment_status)
