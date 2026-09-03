from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import db_dependency
from ..models import Item, Category
from ..schemas import ItemIn, ItemOut, CategoryOut
from ..security import require_permission, log_audit, CurrentUser
from ..helpers import generate_barcode

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


def _to_out(item: Item) -> ItemOut:
    return ItemOut(
        id=item.id, barcode=item.barcode, category=item.category.name if item.category else "-",
        name=item.name, description=item.description, brand=item.brand, unit=item.unit,
        current_quantity=item.current_quantity, minimum_quantity=item.minimum_quantity,
        maximum_quantity=item.maximum_quantity, status=item.status, notes=item.notes,
        is_low_stock=item.is_low_stock, is_out_of_stock=item.is_out_of_stock,
    )


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(db_dependency), _u: CurrentUser = Depends(require_permission("view_inventory"))):
    return db.query(Category).order_by(Category.name).all()


@router.get("", response_model=list[ItemOut])
def list_items(db: Session = Depends(db_dependency), _u: CurrentUser = Depends(require_permission("view_inventory"))):
    items = db.query(Item).order_by(Item.id.desc()).all()
    return [_to_out(i) for i in items]


@router.post("", response_model=ItemOut)
def create_item(payload: ItemIn, db: Session = Depends(db_dependency),
                 user: CurrentUser = Depends(require_permission("manage_inventory"))):
    category = db.query(Category).filter(Category.name == payload.category).first()
    if not category:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown category")

    item = Item(barcode=generate_barcode(), category_id=category.id, name=payload.name,
                description=payload.description, brand=payload.brand, unit=payload.unit,
                current_quantity=payload.current_quantity, minimum_quantity=payload.minimum_quantity,
                maximum_quantity=payload.maximum_quantity, status=payload.status, notes=payload.notes)
    db.add(item)
    db.flush()
    log_audit(db, user.id, "ITEM_SAVED", entity="Item", entity_id=item.id)
    db.refresh(item)
    return _to_out(item)


@router.put("/{item_id}", response_model=ItemOut)
def update_item(item_id: int, payload: ItemIn, db: Session = Depends(db_dependency),
                 user: CurrentUser = Depends(require_permission("manage_inventory"))):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
    category = db.query(Category).filter(Category.name == payload.category).first()

    item.category_id = category.id if category else item.category_id
    item.name = payload.name
    item.description = payload.description
    item.brand = payload.brand
    item.unit = payload.unit
    item.current_quantity = payload.current_quantity
    item.minimum_quantity = payload.minimum_quantity
    item.maximum_quantity = payload.maximum_quantity
    item.status = payload.status
    item.notes = payload.notes
    db.flush()
    log_audit(db, user.id, "ITEM_SAVED", entity="Item", entity_id=item_id)
    db.refresh(item)
    return _to_out(item)


@router.delete("/{item_id}")
def delete_item(item_id: int, db: Session = Depends(db_dependency),
                 user: CurrentUser = Depends(require_permission("manage_inventory"))):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
    try:
        db.delete(item)
        db.flush()
    except IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT,
                             "This item cannot be deleted because it is referenced by existing issue records.")
    log_audit(db, user.id, "ITEM_DELETED", entity="Item", entity_id=item_id)
    return {"ok": True}
