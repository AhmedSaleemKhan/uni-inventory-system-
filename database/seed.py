"""
database/seed.py
Populates the database with the default admin user, categories, and
realistic sample/demo data (100 items, 30 teachers, 15 suppliers,
50 issue records, 50 printing records, 20 purchases, 20 documents).
"""

from __future__ import annotations

import datetime as dt
import random

import config
from auth.authentication import hash_password
from database.database import get_session
from database.models import (
    User, Category, Supplier, Item, Teacher, IssueRecord, ReturnRecord,
    PrintingRecord, DocumentRecord, PurchaseOrder, PurchaseItem, Notification,
)
from utils.helpers import generate_barcode_number, generate_invoice_number, generate_employee_id

CATEGORY_NAMES = [
    "Pens", "Pencils", "Markers", "Whiteboard Markers", "Permanent Markers",
    "Highlighters", "Erasers", "Sharpeners", "Staplers", "Staple Pins",
    "Paper Clips", "Binder Clips", "Glue", "Tape", "Scissors", "Cutters",
    "Punch Machines", "A4 Paper", "Legal Paper", "Colored Paper", "Photo Paper",
    "Printer Ink", "Cartridges", "Course Folders", "Office Files", "Plastic Files",
    "Card Holders", "ID Holders", "Labels", "Stickers", "Name Tags", "Chalk",
    "Dusters", "Whiteboard Cleaner", "Registers", "Diaries", "Envelopes",
    "Visitor Cards", "Office Stationery",
]

DEPARTMENTS = [
    "Computer Science", "Software Engineering", "Electrical Engineering",
    "Mechanical Engineering", "Civil Engineering", "Business Administration",
    "Applied Physics", "Mathematics", "English", "Humanities",
]

DESIGNATIONS = ["Lecturer", "Assistant Professor", "Associate Professor", "Professor", "Visiting Faculty"]

BRANDS = ["Dollar", "Pentel", "Faber-Castell", "Deli", "Kangaro", "Camlin", "HP", "Canon", "Epson", "Generic"]

FIRST_NAMES = [
    "Ahmed", "Ali", "Sara", "Ayesha", "Bilal", "Hassan", "Fatima", "Usman",
    "Hira", "Zainab", "Omar", "Sana", "Kamran", "Nida", "Faisal", "Mahnoor",
    "Tariq", "Rabia", "Adeel", "Sadia", "Imran", "Amna", "Waqas", "Sidra",
    "Danish", "Maria", "Nabeel", "Iqra", "Salman", "Anosha",
]
LAST_NAMES = [
    "Khan", "Malik", "Raza", "Qureshi", "Butt", "Sheikh", "Abbasi", "Chaudhry",
    "Farooq", "Iqbal", "Javed", "Nawaz", "Rafi", "Saeed", "Tariq",
]

DOCUMENT_TYPES = [
    "Internship Files", "TA Files", "Attendance Sheets", "Official Letters",
    "Purchase Requests", "Exam Files", "Course Files", "Office Files",
    "Teacher Documents",
]


def _random_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def seed_all() -> None:
    """Idempotent seeding: only runs if the users table is empty."""
    with get_session() as session:
        if session.query(User).count() > 0:
            return  # already seeded

        # --- Default admin user -------------------------------------------------
        admin = User(
            username=config.DEFAULT_ADMIN_USERNAME,
            password_hash=hash_password(config.DEFAULT_ADMIN_PASSWORD),
            full_name="System Administrator",
            role=config.ROLE_SUPER_ADMIN,
            email="admin@uaims.local",
            must_change_password=True,
        )
        session.add(admin)

        # A few extra role-based demo users
        demo_users = [
            ("storekeeper", config.ROLE_STORE_KEEPER, "Store Keeper"),
            ("officestaff", config.ROLE_OFFICE_STAFF, "Office Staff Member"),
            ("printstaff", config.ROLE_PRINTING_STAFF, "Printing Staff Member"),
            ("deptstaff", config.ROLE_DEPARTMENT_STAFF, "Department Staff Member"),
        ]
        for username, role, full_name in demo_users:
            session.add(User(
                username=username,
                password_hash=hash_password("password123"),
                full_name=full_name,
                role=role,
            ))

        # --- Categories ----------------------------------------------------------
        categories = [Category(name=name) for name in CATEGORY_NAMES]
        session.add_all(categories)
        session.flush()

        # --- Suppliers (15) --------------------------------------------------------
        suppliers = []
        for i in range(1, 16):
            suppliers.append(Supplier(
                name=f"{random.choice(['Al-Haramain', 'National', 'City', 'Metro', 'Sindh', 'Punjab', 'Universal', 'Prime'])} Stationery Suppliers {i}",
                address=f"Shop #{random.randint(1,200)}, Main Bazaar, Karachi",
                phone=f"03{random.randint(00,99):02d}{random.randint(1000000,9999999)}",
                email=f"supplier{i}@example.com",
                gst_number=f"GST-{random.randint(100000,999999)}",
                notes="Reliable supplier for office and printing stationery.",
            ))
        session.add_all(suppliers)
        session.flush()

        # --- Items (100) ------------------------------------------------------------
        items = []
        for i in range(1, 101):
            category = random.choice(categories)
            supplier = random.choice(suppliers)
            qty = random.randint(0, 500)
            min_q = random.randint(10, 50)
            items.append(Item(
                barcode=generate_barcode_number(),
                category_id=category.id,
                name=f"{category.name} - Type {chr(65 + (i % 5))}",
                description=f"Standard office supply item under {category.name} category.",
                brand=random.choice(BRANDS),
                supplier_id=supplier.id,
                purchase_date=dt.date.today() - dt.timedelta(days=random.randint(1, 400)),
                purchase_cost=round(random.uniform(5, 500), 2),
                selling_cost=round(random.uniform(6, 600), 2),
                unit=random.choice(["pcs", "box", "ream", "pack", "dozen"]),
                current_quantity=qty,
                minimum_quantity=min_q,
                maximum_quantity=min_q * random.randint(10, 30),
                storage_location=f"Rack-{random.randint(1,20)}/Shelf-{random.randint(1,5)}",
                status="Active",
                notes="",
            ))
        session.add_all(items)
        session.flush()

        # --- Teachers (30) -----------------------------------------------------------
        teachers = []
        for i in range(1, 31):
            dept = random.choice(DEPARTMENTS)
            teachers.append(Teacher(
                employee_id=generate_employee_id("FAC"),
                name=_random_name(),
                department=dept,
                designation=random.choice(DESIGNATIONS),
                phone=f"03{random.randint(0,99):02d}{random.randint(1000000,9999999)}",
                email=f"faculty{i}@pafiast.edu.pk",
                office_number=f"F-{random.randint(100,399)}",
                assigned_courses=f"{dept} Course {random.randint(101,499)}",
                status="Active",
            ))
        session.add_all(teachers)
        session.flush()

        # --- Issue records (50) + some Return records -------------------------------
        issue_records = []
        for i in range(1, 51):
            teacher = random.choice(teachers)
            item = random.choice(items)
            issue_date = dt.date.today() - dt.timedelta(days=random.randint(0, 60))
            return_required = random.choice([True, False])
            record = IssueRecord(
                teacher_id=teacher.id,
                item_id=item.id,
                quantity=random.randint(1, 10),
                issue_date=issue_date,
                issue_time=f"{random.randint(9,17):02d}:{random.randint(0,59):02d}",
                issued_by="System Administrator",
                department=teacher.department,
                remarks="",
                return_required=return_required,
                expected_return_date=issue_date + dt.timedelta(days=7) if return_required else None,
                status="Issued",
            )
            issue_records.append(record)
        session.add_all(issue_records)
        session.flush()

        # Mark ~half of the "return_required" issues as returned
        for record in issue_records:
            if record.return_required and random.random() < 0.5:
                return_date = record.issue_date + dt.timedelta(days=random.randint(3, 12))
                is_late = record.expected_return_date is not None and return_date > record.expected_return_date
                session.add(ReturnRecord(
                    issue_id=record.id,
                    returned_quantity=record.quantity,
                    return_date=return_date,
                    condition=random.choice(["Good", "Damaged", "Partially Used"]),
                    received_by="Store Keeper",
                    is_late=is_late,
                ))
                record.status = "Returned"
            elif record.return_required and record.expected_return_date and record.expected_return_date < dt.date.today():
                record.status = "Overdue"

        # --- Printing records (50) --------------------------------------------------
        printing_records = []
        for i in range(1, 51):
            teacher = random.choice(teachers)
            color_mode = random.choice(["Black & White", "Color"])
            side_mode = random.choice(["Single Side", "Double Side"])
            pages = random.randint(1, 50)
            copies = random.randint(1, 20)
            per_page_cost = 5 if color_mode == "Black & White" else 15
            cost = pages * copies * per_page_cost
            printing_records.append(PrintingRecord(
                teacher_id=teacher.id,
                teacher_name=teacher.name,
                department=teacher.department,
                course=f"{teacher.department} {random.randint(101,499)}",
                document_name=f"{random.choice(['Quiz', 'Assignment', 'Handout', 'Lecture Notes', 'Exam Paper'])} {i}",
                color_mode=color_mode,
                side_mode=side_mode,
                pages=pages,
                copies=copies,
                cost=cost,
                printed_by="Printing Staff Member",
                print_date=dt.date.today() - dt.timedelta(days=random.randint(0, 45)),
                status="Completed",
            ))
        session.add_all(printing_records)

        # --- Document records (20) ---------------------------------------------------
        documents = []
        for i in range(1, 21):
            teacher = random.choice(teachers)
            status = random.choice(["Pending", "Received", "Approved", "Rejected"])
            documents.append(DocumentRecord(
                document_type=random.choice(DOCUMENT_TYPES),
                title=f"{random.choice(DOCUMENT_TYPES)} - {teacher.department} - #{i}",
                teacher_id=teacher.id,
                department=teacher.department,
                submitted_by=teacher.name,
                received_date=dt.date.today() - dt.timedelta(days=random.randint(0, 90)),
                status=status,
                approved_by="System Administrator" if status == "Approved" else None,
                remarks="",
            ))
        session.add_all(documents)

        # --- Purchase orders (20) with purchase items --------------------------------
        for i in range(1, 21):
            supplier = random.choice(suppliers)
            po = PurchaseOrder(
                invoice_number=generate_invoice_number(),
                supplier_id=supplier.id,
                order_date=dt.date.today() - dt.timedelta(days=random.randint(0, 120)),
                tax_percent=random.choice([0, 5, 10, 17]),
                payment_status=random.choice(["Paid", "Unpaid", "Partial"]),
                notes="",
            )
            session.add(po)
            session.flush()

            total = 0.0
            for _ in range(random.randint(1, 4)):
                item = random.choice(items)
                qty = random.randint(5, 100)
                unit_cost = item.purchase_cost
                line_total = round(qty * unit_cost, 2)
                total += line_total
                session.add(PurchaseItem(
                    purchase_order_id=po.id,
                    item_id=item.id,
                    quantity=qty,
                    unit_cost=unit_cost,
                    line_total=line_total,
                ))
            po.total_amount = round(total * (1 + po.tax_percent / 100), 2)

        # --- Notifications for low/out of stock items --------------------------------
        for item in items:
            if item.is_out_of_stock:
                session.add(Notification(category="OutOfStock", message=f"{item.name} is out of stock."))
            elif item.is_low_stock:
                session.add(Notification(category="LowStock", message=f"{item.name} is low on stock ({item.current_quantity} left)."))
