"""
database/database.py
SQLAlchemy engine, session factory, and database initialization helpers.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

import config
from database.models import Base

logger = logging.getLogger("uaims.database")

engine: Engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
    future=True,
)


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign key constraint enforcement for SQLite connections."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    """Create all tables if they do not already exist."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created at %s", config.DATABASE_PATH)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context-managed session with automatic commit/rollback."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def database_is_fresh() -> bool:
    """Return True if the database file did not previously exist."""
    return not config.DATABASE_PATH.exists() or config.DATABASE_PATH.stat().st_size == 0
