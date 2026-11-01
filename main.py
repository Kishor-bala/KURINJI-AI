"""
Root FastAPI entrypoint for Vercel deployment.
Exposes the Kurinji FastAPI application instance from backend.app.main.
"""
import sys
from pathlib import Path

# Ensure root and backend are on sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.main import app

# Export all standard ASGI handler names at top level for serverless discovery
handler = app
application = app

__all__ = ["app", "handler", "application"]
