"""
app/database.py
SQLAlchemy engine/session setup. Works against SQLite or Postgres based
on config.DATABASE_URL alone - no other code changes needed either way.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from . import config
from .models import Base

_is_sqlite = config.DATABASE_URL.startswith("sqlite")

_connect_args = {"check_same_thread": False} if _is_sqlite else {}
engine: Engine = create_engine(config.DATABASE_URL, connect_args=_connect_args, future=True, pool_pre_ping=not _is_sqlite)

if _is_sqlite:
    @event.listens_for(Engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def _migrate_diary_no() -> None:
    """create_all() only creates whole tables that don't exist yet - it never
    alters an existing one. An `items` table created before the barcode ->
    diary_no rename is missing the new NOT NULL column entirely, which
    crashes every query touching Item. Add and backfill it once, here."""
    inspector = inspect(engine)
    if "items" not in inspector.get_table_names():
        return
    existing_columns = {c["name"] for c in inspector.get_columns("items")}
    if "diary_no" in existing_columns:
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE items ADD COLUMN diary_no VARCHAR(64)"))
        pad = "substr('0000' || id, -5, 5)" if _is_sqlite else "lpad(id::text, 5, '0')"
        conn.execute(text(f"UPDATE items SET diary_no = 'DN-' || {pad} WHERE diary_no IS NULL"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_items_diary_no ON items (diary_no)"))
        if not _is_sqlite:
            conn.execute(text("ALTER TABLE items ALTER COLUMN diary_no SET NOT NULL"))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _migrate_diary_no()


@contextmanager
def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def db_dependency() -> Generator[Session, None, None]:
    """FastAPI dependency: one session per request, committed on success."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
