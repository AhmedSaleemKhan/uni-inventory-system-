"""app/helpers.py - shared ID generators used by both seed data and live create endpoints."""

from __future__ import annotations

import random


def generate_barcode() -> str:
    return "ITM" + "".join(random.choices("0123456789", k=9))


def generate_employee_id() -> str:
    return f"FAC-{random.randint(1000, 9999)}"
