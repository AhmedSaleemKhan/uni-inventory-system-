"""Vercel Python entrypoint - re-exports the FastAPI `app` instance."""

from app.main import app  # noqa: F401
