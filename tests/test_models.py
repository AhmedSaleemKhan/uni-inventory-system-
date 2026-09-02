"""
tests/test_models.py
Basic unit tests covering database models, authentication hashing,
and the permission matrix. Run with:

    python -m pytest tests/ -v

Uses a temporary in-memory SQLite database so it never touches the
real inventory.db file.
"""

import os
import sys
import datetime as dt

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.models import Base, User, Category, Item, Teacher, Supplier
from auth.authentication import hash_password, verify_password
from auth.roles import get_role_permissions, PERMISSIONS
from auth.permissions import has_permission
import config


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()


def test_password_hash_roundtrip():
    hashed = hash_password("MySecret123")
    assert verify_password("MySecret123", hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_create_user(session):
    user = User(username="testuser", password_hash=hash_password("pass1234"),
                full_name="Test User", role=config.ROLE_OFFICE_STAFF)
    session.add(user)
    session.commit()
    fetched = session.query(User).filter_by(username="testuser").first()
    assert fetched is not None
    assert fetched.role == config.ROLE_OFFICE_STAFF


def test_item_low_stock_property(session):
    category = Category(name="Pens")
    session.add(category)
    session.commit()

    item = Item(
        barcode="ITM000001", category_id=category.id, name="Blue Pen",
        current_quantity=5, minimum_quantity=10,
    )
    session.add(item)
    session.commit()

    assert item.is_low_stock is True
    assert item.is_out_of_stock is False

    item.current_quantity = 0
    session.commit()
    assert item.is_out_of_stock is True


def test_teacher_creation(session):
    teacher = Teacher(employee_id="FAC-1001", name="Dr. Ahmed Khan", department="Computer Science")
    session.add(teacher)
    session.commit()
    assert session.query(Teacher).count() == 1


def test_supplier_creation(session):
    supplier = Supplier(name="City Stationery")
    session.add(supplier)
    session.commit()
    assert session.query(Supplier).count() == 1


def test_role_permissions_super_admin_has_all():
    perms = get_role_permissions(config.ROLE_SUPER_ADMIN)
    assert "manage_backup" in perms
    assert "manage_users" in perms


def test_role_permissions_department_staff_limited():
    perms = get_role_permissions(config.ROLE_DEPARTMENT_STAFF)
    assert "manage_backup" not in perms
    assert "manage_users" not in perms


def test_has_permission_helper():
    assert has_permission(config.ROLE_STORE_KEEPER, "manage_inventory") is True
    assert has_permission(config.ROLE_PRINTING_STAFF, "manage_inventory") is False


def test_all_permission_roles_are_valid():
    for permission, roles in PERMISSIONS.items():
        for role in roles:
            assert role in config.ALL_ROLES
