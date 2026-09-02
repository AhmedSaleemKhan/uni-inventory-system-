"""
utils/helpers.py
Shared helper utilities: ID/barcode generation, QR codes, date formatting,
currency formatting, and small validation helpers.
"""

from __future__ import annotations

import datetime as dt
import io
import os
import random
import string
import uuid

import qrcode
import barcode
from barcode.writer import ImageWriter

import config


# ---------------------------------------------------------------------------
# ID / Code generation
# ---------------------------------------------------------------------------
def generate_barcode_number(prefix: str = "ITM") -> str:
    """Generate a unique-looking numeric barcode string (EAN-13 friendly)."""
    digits = "".join(random.choices(string.digits, k=9))
    return f"{prefix}{digits}"


def generate_invoice_number() -> str:
    today = dt.date.today().strftime("%Y%m%d")
    suffix = uuid.uuid4().hex[:6].upper()
    return f"INV-{today}-{suffix}"


def generate_employee_id(prefix: str = "EMP") -> str:
    return f"{prefix}-{random.randint(1000, 9999)}"


def generate_teacher_id() -> str:
    return f"T-{uuid.uuid4().hex[:8].upper()}"


# ---------------------------------------------------------------------------
# Barcode / QR generation (saved to assets/images, returns file path)
# ---------------------------------------------------------------------------
def generate_qr_code_image(data: str, filename: str) -> str:
    """Create a QR code PNG for the given data and return its file path."""
    img = qrcode.make(data)
    path = os.path.join(config.IMAGES_DIR, filename)
    img.save(path)
    return path


def generate_barcode_image(code_value: str, filename_no_ext: str) -> str:
    """Create a Code128 barcode PNG and return the file path (with extension)."""
    try:
        code128 = barcode.get_barcode_class("code128")
        writer = ImageWriter()
        full_path_no_ext = os.path.join(config.IMAGES_DIR, filename_no_ext)
        instance = code128(code_value, writer=writer)
        saved_path = instance.save(full_path_no_ext)
        return saved_path
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------
def format_currency(amount: float) -> str:
    return f"Rs. {amount:,.2f}"


def format_date(value: dt.date | dt.datetime | None) -> str:
    if value is None:
        return "-"
    return value.strftime("%d-%b-%Y")


def format_datetime(value: dt.datetime | None) -> str:
    if value is None:
        return "-"
    return value.strftime("%d-%b-%Y %I:%M %p")


def current_time_str() -> str:
    return dt.datetime.now().strftime("%I:%M %p")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def is_valid_email(value: str) -> bool:
    if not value:
        return True  # optional field
    return "@" in value and "." in value.split("@")[-1]


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))
