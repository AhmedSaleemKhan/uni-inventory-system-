"""
app/main.py
FastAPI application factory: CORS, startup DB init + seed, router wiring.
This is the `app` object Vercel's Python runtime looks for.
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .database import init_db
from .seed import seed_all
from .routers import (
    auth, dashboard, inventory, teachers, issues, printing,
    documents, suppliers, purchases, reports, users,
)

app = FastAPI(title=config.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    # Auth is a Bearer token in the Authorization header, not cookies, so
    # credentialed CORS isn't needed - and the CORS spec forbids combining
    # allow_credentials with a wildcard origin anyway.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _bootstrap() -> None:
    init_db()
    seed_all()


@app.get("/api/health")
def health():
    # commit/database_configured exist to answer "is this actually the
    # deployment I think it is" from one URL, without needing to trust a
    # dashboard label - VERCEL_GIT_COMMIT_SHA is set automatically by
    # Vercel at build and runtime, no configuration needed.
    return {
        "status": "ok",
        "app": config.APP_NAME,
        "commit": os.getenv("VERCEL_GIT_COMMIT_SHA", "not running on Vercel"),
        "database_configured": bool(os.getenv("DATABASE_URL")),
    }


app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(inventory.router)
app.include_router(teachers.router)
app.include_router(issues.router)
app.include_router(printing.router)
app.include_router(documents.router)
app.include_router(suppliers.router)
app.include_router(purchases.router)
app.include_router(reports.router)
app.include_router(users.router)
