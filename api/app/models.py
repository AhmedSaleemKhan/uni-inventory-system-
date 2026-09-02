"""
app/models.py
SQLAlchemy ORM models - same schema as the desktop app's database/models.py,
portable as-is across SQLite and Postgres.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional, List

from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, Date, Text, ForeignKey, Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def now() -> dt.datetime:
    return dt.datetime.now()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="Office Staff")
    email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=now)
    last_login: Mapped[Optional[dt.datetime]] = mapped_column(DateTime, nullable=True)

    login_logs: Mapped[List["LoginHistory"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class LoginHistory(Base):
    __tablename__ = "login_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    login_time: Mapped[dt.datetime] = mapped_column(DateTime, default=now)
    logout_time: Mapped[Optional[dt.datetime]] = mapped_column(DateTime, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship(back_populates="login_logs")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    entity: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[dt.datetime] = mapped_column(DateTime, default=now)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    items: Mapped[List["Item"]] = relationship(back_populates="category")


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    gst_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=now)

    items: Mapped[List["Item"]] = relationship(back_populates="supplier")
    purchase_orders: Mapped[List["PurchaseOrder"]] = relationship(back_populates="supplier")


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    barcode: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    supplier_id: Mapped[Optional[int]] = mapped_column(ForeignKey("suppliers.id"), nullable=True)
    purchase_date: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    purchase_cost: Mapped[float] = mapped_column(Float, default=0.0)
    selling_cost: Mapped[float] = mapped_column(Float, default=0.0)
    unit: Mapped[str] = mapped_column(String(30), default="pcs")
    current_quantity: Mapped[int] = mapped_column(Integer, default=0)
    minimum_quantity: Mapped[int] = mapped_column(Integer, default=5)
    maximum_quantity: Mapped[int] = mapped_column(Integer, default=1000)
    storage_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="Active")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=now, onupdate=now)

    category: Mapped["Category"] = relationship(back_populates="items")
    supplier: Mapped[Optional["Supplier"]] = relationship(back_populates="items")
    issue_records: Mapped[List["IssueRecord"]] = relationship(back_populates="item")
    purchase_items: Mapped[List["PurchaseItem"]] = relationship(back_populates="item")

    @property
    def is_low_stock(self) -> bool:
        return self.current_quantity <= self.minimum_quantity

    @property
    def is_out_of_stock(self) -> bool:
        return self.current_quantity <= 0


Index("ix_items_category_status", Item.category_id, Item.status)


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    designation: Mapped[str] = mapped_column(String(100), default="Lecturer")
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    office_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    assigned_courses: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="Active")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=now)

    issue_records: Mapped[List["IssueRecord"]] = relationship(back_populates="teacher")
    printing_records: Mapped[List["PrintingRecord"]] = relationship(back_populates="teacher")
    documents: Mapped[List["DocumentRecord"]] = relationship(back_populates="teacher")


class IssueRecord(Base):
    __tablename__ = "issue_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    issue_date: Mapped[dt.date] = mapped_column(Date, default=dt.date.today)
    issue_time: Mapped[str] = mapped_column(String(20), default="")
    issued_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    return_required: Mapped[bool] = mapped_column(Boolean, default=False)
    expected_return_date: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="Issued")

    teacher: Mapped["Teacher"] = relationship(back_populates="issue_records")
    item: Mapped["Item"] = relationship(back_populates="issue_records")
    return_record: Mapped[Optional["ReturnRecord"]] = relationship(back_populates="issue_record", uselist=False)


class ReturnRecord(Base):
    __tablename__ = "return_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issue_records.id"), unique=True, nullable=False)
    returned_quantity: Mapped[int] = mapped_column(Integer, default=0)
    return_date: Mapped[dt.date] = mapped_column(Date, default=dt.date.today)
    condition: Mapped[str] = mapped_column(String(50), default="Good")
    received_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_late: Mapped[bool] = mapped_column(Boolean, default=False)

    issue_record: Mapped["IssueRecord"] = relationship(back_populates="return_record")


class PrintingRecord(Base):
    __tablename__ = "printing_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    teacher_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teachers.id"), nullable=True)
    teacher_name: Mapped[str] = mapped_column(String(150), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    course: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    document_name: Mapped[str] = mapped_column(String(200), nullable=False)
    color_mode: Mapped[str] = mapped_column(String(20), default="Black & White")
    side_mode: Mapped[str] = mapped_column(String(20), default="Single Side")
    pages: Mapped[int] = mapped_column(Integer, default=1)
    copies: Mapped[int] = mapped_column(Integer, default=1)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    printed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    print_date: Mapped[dt.date] = mapped_column(Date, default=dt.date.today)
    status: Mapped[str] = mapped_column(String(30), default="Completed")

    teacher: Mapped[Optional["Teacher"]] = relationship(back_populates="printing_records")


class DocumentRecord(Base):
    __tablename__ = "document_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    teacher_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teachers.id"), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    submitted_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    received_date: Mapped[dt.date] = mapped_column(Date, default=dt.date.today)
    status: Mapped[str] = mapped_column(String(30), default="Pending")
    approved_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    teacher: Mapped[Optional["Teacher"]] = relationship(back_populates="documents")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_number: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    order_date: Mapped[dt.date] = mapped_column(Date, default=dt.date.today)
    tax_percent: Mapped[float] = mapped_column(Float, default=0.0)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    payment_status: Mapped[str] = mapped_column(String(30), default="Unpaid")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    supplier: Mapped["Supplier"] = relationship(back_populates="purchase_orders")
    purchase_items: Mapped[List["PurchaseItem"]] = relationship(back_populates="purchase_order", cascade="all, delete-orphan")


class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_cost: Mapped[float] = mapped_column(Float, default=0.0)
    line_total: Mapped[float] = mapped_column(Float, default=0.0)

    purchase_order: Mapped["PurchaseOrder"] = relationship(back_populates="purchase_items")
    item: Mapped["Item"] = relationship(back_populates="purchase_items")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=now)
