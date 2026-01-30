"""
Alembic Autoscan - Automatically discover and import SQLAlchemy models for Alembic migrations.
"""

from .scanner import ModelScanner
from .integration import import_models

__version__ = "0.1.0"
__all__ = ["ModelScanner", "import_models"]
