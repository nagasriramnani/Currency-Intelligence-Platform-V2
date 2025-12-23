"""
Main entry point for the Currency Intelligence Platform Backend.
Re-exports the FastAPI app from api/server.py for uvicorn.

Usage:
    python -m uvicorn main:app --reload
"""

from api.server import app

__all__ = ['app']
