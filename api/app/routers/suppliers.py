from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import db_dependency
from ..models import Supplier
from ..schemas import SupplierIn, SupplierOut
from ..security import require_permission, log_audit, CurrentUser

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])


def _to_out(s: Supplier) -> SupplierOut:
    return SupplierOut(id=s.id, name=s.name, address=s.address, phone=s.phone, email=s.email,
                        gst_number=s.gst_number, notes=s.notes,
                        total_purchases=sum(po.total_amount for po in s.purchase_orders))


@router.get("", response_model=list[SupplierOut])
def list_suppliers(db: Session = Depends(db_dependency), _u: CurrentUser = Depends(require_permission("view_dashboard"))):
    return [_to_out(s) for s in db.query(Supplier).order_by(Supplier.id.desc()).all()]


@router.post("", response_model=SupplierOut)
def create_supplier(payload: SupplierIn, db: Session = Depends(db_dependency),
                     user: CurrentUser = Depends(require_permission("manage_suppliers"))):
    supplier = Supplier(**payload.model_dump())
    db.add(supplier)
    db.flush()
    log_audit(db, user.id, "SUPPLIER_SAVED", entity="Supplier", entity_id=supplier.id)
    db.refresh(supplier)
    return _to_out(supplier)


@router.put("/{supplier_id}", response_model=SupplierOut)
def update_supplier(supplier_id: int, payload: SupplierIn, db: Session = Depends(db_dependency),
                     user: CurrentUser = Depends(require_permission("manage_suppliers"))):
    supplier = db.get(Supplier, supplier_id)
    if not supplier:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Supplier not found")
    for key, value in payload.model_dump().items():
        setattr(supplier, key, value)
    db.flush()
    log_audit(db, user.id, "SUPPLIER_SAVED", entity="Supplier", entity_id=supplier_id)
    db.refresh(supplier)
    return _to_out(supplier)


@router.delete("/{supplier_id}")
def delete_supplier(supplier_id: int, db: Session = Depends(db_dependency),
                     user: CurrentUser = Depends(require_permission("manage_suppliers"))):
    supplier = db.get(Supplier, supplier_id)
    if not supplier:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Supplier not found")
    try:
        db.delete(supplier)
        db.flush()
    except IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT,
                             "This supplier cannot be deleted because they have existing items or purchase orders linked to them.")
    log_audit(db, user.id, "SUPPLIER_DELETED", entity="Supplier", entity_id=supplier_id)
    return {"ok": True}
