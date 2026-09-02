"""
Vercel Python entrypoint - re-exports the FastAPI `app` instance.

Vercel's runtime loads this file directly via importlib (not by running
`python index.py` or `uvicorn index:app` from inside api/), so it does
NOT automatically put this file's own directory on sys.path the way
local dev does. Without the line below, "from app.main import app"
fails with "ModuleNotFoundError: No module named 'app'" because the
sibling app/ package can't be found. Adding this directory to sys.path
explicitly makes it resolve the same way in both places.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app  # noqa: E402,F401
