"""
Root FastAPI entrypoint for Vercel deployment.
Exposes the Kurinji FastAPI application instance from backend.app.main.
"""
from backend.app.main import app

__all__ = ["app"]
