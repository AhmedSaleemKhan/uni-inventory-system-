"""
app/schemas.py
Pydantic request/response models. One pragmatic schema per entity rather
than separate Create/Update/Out variants everywhere - fields that are
server-assigned (id, computed flags, timestamps) simply aren't accepted
on the *In schemas.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class LoginIn(BaseModel):
    username: str
    password: str


class ChangePasswordIn(BaseModel):
    new_password: str


class MeOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    must_change_password: bool


class LoginOut(BaseModel):
    token: str
    user: MeOut


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
class UserIn(BaseModel):
    username: str
    full_name: str
    role: str
    email: Optional[str] = ""
    phone: Optional[str] = ""
    password: Optional[str] = "password123"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    full_name: str
    role: str
    email: Optional[str] = None
    is_active: bool
    last_login: Optional[dt.datetime] = None


# ---------------------------------------------------------------------------
# Categories / Suppliers
# ---------------------------------------------------------------------------
class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class SupplierIn(BaseModel):
    name: str
    address: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    gst_number: Optional[str] = ""
    notes: Optional[str] = ""


class SupplierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    gst_number: Optional[str] = None
    notes: Optional[str] = None
    total_purchases: float = 0.0


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------
class ItemIn(BaseModel):
    category: str
    name: str
    description: Optional[str] = ""
    brand: Optional[str] = ""
    supplier: Optional[str] = None
    purchase_date: Optional[dt.date] = None
    purchase_cost: float = 0.0
    selling_cost: float = 0.0
    unit: str = "pcs"
    current_quantity: int = 0
    minimum_quantity: int = 10
    maximum_quantity: int = 1000
    storage_location: Optional[str] = ""
    status: str = "Active"
    notes: Optional[str] = ""


class ItemOut(BaseModel):
    id: int
    barcode: str
    category: str
    name: str
    description: Optional[str] = None
    brand: Optional[str] = None
    supplier: Optional[str] = None
    purchase_date: Optional[dt.date] = None
    purchase_cost: float
    selling_cost: float
    unit: str
    current_quantity: int
    minimum_quantity: int
    maximum_quantity: int
    storage_location: Optional[str] = None
    status: str
    notes: Optional[str] = None
    is_low_stock: bool
    is_out_of_stock: bool


# ---------------------------------------------------------------------------
# Teachers
# ---------------------------------------------------------------------------
class TeacherIn(BaseModel):
    name: str
    department: str
    designation: str = "Lecturer"
    phone: Optional[str] = ""
    email: Optional[str] = ""
    office_number: Optional[str] = ""
    assigned_courses: Optional[str] = ""
    status: str = "Active"


class TeacherOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: str
    name: str
    department: str
    designation: str
    phone: Optional[str] = None
    email: Optional[str] = None
    office_number: Optional[str] = None
    assigned_courses: Optional[str] = None
    status: str


# ---------------------------------------------------------------------------
# Issue / Return
# ---------------------------------------------------------------------------
class IssueIn(BaseModel):
    teacher: str
    item: str
    quantity: int = 1
    department: Optional[str] = None
    remarks: Optional[str] = ""
    return_required: bool = False
    expected_return_date: Optional[dt.date] = None


class IssueOut(BaseModel):
    id: int
    teacher: str
    item: str
    quantity: int
    issue_date: dt.date
    department: Optional[str] = None
    return_required: bool
    expected_return_date: Optional[dt.date] = None
    status: str


class ReturnIn(BaseModel):
    returned_quantity: int
    condition: str = "Good"
    remarks: Optional[str] = ""


class ReturnOut(BaseModel):
    issue_id: int
    teacher: str
    item: str
    quantity: int
    issue_date: dt.date
    expected_return_date: Optional[dt.date] = None
    status: str


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------
class PrintingIn(BaseModel):
    teacher: Optional[str] = None
    department: Optional[str] = ""
    course: Optional[str] = ""
    document_name: str
    color_mode: str = "Black & White"
    side_mode: str = "Single Side"
    pages: int = 1
    copies: int = 1


class PrintingOut(BaseModel):
    id: int
    teacher_name: str
    department: Optional[str] = None
    course: Optional[str] = None
    document_name: str
    color_mode: str
    side_mode: str
    pages: int
    copies: int
    cost: float
    print_date: dt.date
    status: str


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------
class DocumentIn(BaseModel):
    document_type: str
    title: str
    department: Optional[str] = ""
    submitted_by: Optional[str] = None
    status: str = "Pending"
    remarks: Optional[str] = ""


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    document_type: str
    title: str
    department: Optional[str] = None
    submitted_by: Optional[str] = None
    received_date: dt.date
    status: str
    approved_by: Optional[str] = None


# ---------------------------------------------------------------------------
# Purchases
# ---------------------------------------------------------------------------
class PurchaseLineIn(BaseModel):
    item: str
    quantity: int
    unit_cost: float


class PurchaseOrderIn(BaseModel):
    supplier: str
    tax_percent: float = 0.0
    lines: List[PurchaseLineIn]


class PurchaseOrderOut(BaseModel):
    id: int
    invoice_number: str
    supplier: str
    order_date: dt.date
    tax_percent: float
    total_amount: float
    payment_status: str


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
class DashboardOut(BaseModel):
    total_items: int
    available_stock: int
    low_stock: int
    out_of_stock: int
    today_issued: int
    today_returned: int
    today_printing: int
    pending_docs: int
    notifications: List[str]
    recent_activity: List[str]
    monthly_labels: List[str]
    monthly_issue_counts: List[int]
    monthly_print_counts: List[int]
