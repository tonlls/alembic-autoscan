"""
Alembic Autoscan - Automatically discover and import SQLAlchemy models for Alembic migrations.
"""

from .integration import import_models
from .scanner import ModelScanner

__version__ = "1.0.0"
__all__ = ["ModelScanner", "import_models"]
