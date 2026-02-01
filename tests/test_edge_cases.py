"""
Tests for edge cases and enhanced detection features.
"""

import tempfile
from pathlib import Path

import pytest

from alembic_autoscan.scanner import ModelScanner


class TestSQLModelDetection:
    """Test detection of SQLModel models."""

    def test_detect_sqlmodel_with_table_true(self):
        """Test detection of SQLModel with table=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_file = Path(tmpdir) / "hero.py"
            model_file.write_text(
                """
from sqlmodel import SQLModel, Field
from typing import Optional

class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    secret_name: str
"""
            )

            scanner = ModelScanner(base_path=tmpdir)
            assert scanner._scan_file_for_models(model_file)

    def test_ignore_sqlmodel_without_table(self):
        """Test that SQLModel without table=True is ignored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_file = Path(tmpdir) / "schema.py"
            model_file.write_text(
                """
from sqlmodel import SQLModel

class HeroBase(SQLModel):
    name: str
    secret_name: str
"""
            )

            scanner = ModelScanner(base_path=tmpdir)
            # Should not detect this as a model (no table=True)
            assert not scanner._scan_file_for_models(model_file)


class TestAbstractClassDetection:
    """Test detection and filtering of abstract base classes."""

    def test_detect_abstract_class(self):
        """Test detection of abstract base classes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_file = Path(tmpdir) / "base.py"
            model_file.write_text(
                """
from sqlalchemy import Column, Integer
from database import Base

class AbstractBase(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)

class ConcreteModel(AbstractBase):
    __tablename__ = "concrete"
"""
            )

            scanner = ModelScanner(base_path=tmpdir)

            # Should detect the file has models (ConcreteModel)
            assert scanner._scan_file_for_models(model_file)

            # Should have tracked the abstract class
            assert "AbstractBase" in scanner._abstract_classes

    def test_skip_abstract_class_in_discovery(self):
        """Test that abstract classes don't get their own module entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # File with only abstract class
            abstract_file = Path(tmpdir) / "abstract_only.py"
            abstract_file.write_text(
                """
from database import Base

class AbstractModel(Base):
    __abstract__ = True
"""
            )

            # File with concrete model
            concrete_file = Path(tmpdir) / "concrete.py"
            concrete_file.write_text(
                """
from database import Base

class ConcreteModel(Base):
    __tablename__ = "concrete"
"""
            )

            scanner = ModelScanner(base_path=tmpdir)
            modules = scanner.discover()

            # Should only discover the concrete model
            assert "concrete" in modules
            assert "abstract_only" not in modules


class TestModernSQLAlchemy:
    """Test detection of modern SQLAlchemy 2.0 patterns."""

    def test_detect_mapped_annotation(self):
        """Test detection of Mapped[] annotations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_file = Path(tmpdir) / "modern.py"
            model_file.write_text(
                """
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class ModernModel(Base):
    __tablename__ = "modern"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
"""
            )

            scanner = ModelScanner(base_path=tmpdir)
            assert scanner._scan_file_for_models(model_file)

    def test_detect_mapped_column(self):
        """Test detection of mapped_column() calls."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_file = Path(tmpdir) / "model.py"
            model_file.write_text(
                """
from sqlalchemy.orm import mapped_column
from database import Base

class User(Base):
    __tablename__ = "users"
    id = mapped_column(primary_key=True)
"""
            )

            scanner = ModelScanner(base_path=tmpdir)
            assert scanner._scan_file_for_models(model_file)


class TestMixins:
    """Test handling of mixins and multiple inheritance."""

    def test_mixin_without_table(self):
        """Test that mixins without __tablename__ are not detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mixin_file = Path(tmpdir) / "mixins.py"
            mixin_file.write_text(
                """
from sqlalchemy import Column, Integer

class TimestampMixin:
    created_at = Column(Integer)
    updated_at = Column(Integer)
"""
            )

            scanner = ModelScanner(base_path=tmpdir)
            # Mixin without Base or __tablename__ should not be detected
            assert not scanner._scan_file_for_models(mixin_file)

    def test_model_with_mixin(self):
        """Test model that uses a mixin."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_file = Path(tmpdir) / "user.py"
            model_file.write_text(
                """
from sqlalchemy import Column, Integer, String
from database import Base
from mixins import TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
"""
            )

            scanner = ModelScanner(base_path=tmpdir)
            assert scanner._scan_file_for_models(model_file)


class TestCacheIntegration:
    """Test scanner with caching enabled."""

    def test_scanner_with_cache(self):
        """Test that scanner uses cache correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_file = Path(tmpdir) / "cached_model.py"
            model_file.write_text(
                """
from database import Base

class CachedModel(Base):
    __tablename__ = "cached"
"""
            )

            scanner = ModelScanner(base_path=tmpdir, cache_enabled=True)

            # First discovery should create cache
            modules1 = scanner.discover()
            assert "cached_model" in modules1
            assert (Path(tmpdir) / ".alembic-autoscan.cache").exists()

            # Second discovery should use cache
            scanner2 = ModelScanner(base_path=tmpdir, cache_enabled=True)
            modules2 = scanner2.discover()
            assert modules1 == modules2

    def test_scanner_without_cache(self):
        """Test scanner with caching disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_file = Path(tmpdir) / "model.py"
            model_file.write_text(
                """
from database import Base

class Model(Base):
    __tablename__ = "model"
"""
            )

            scanner = ModelScanner(base_path=tmpdir, cache_enabled=False)
            modules = scanner.discover()

            assert "model" in modules
            # Cache file should not be created
            assert not (Path(tmpdir) / ".alembic-autoscan.cache").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
