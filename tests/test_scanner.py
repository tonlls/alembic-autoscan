import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from alembic_autoscan.scanner import ModelScanner, scan_file_worker


class TestModelScanner:
    """Test suite for ModelScanner."""

    def test_scanner_initialization(self):
        """Test that scanner initializes with correct defaults."""
        scanner = ModelScanner()
        assert scanner.base_path == Path.cwd()
        assert scanner.include_patterns == ["**/*.py"]
        assert len(scanner.exclude_patterns) > 0

    def test_scanner_with_custom_path(self):
        """Test scanner with custom base path."""
        scanner = ModelScanner(base_path="/tmp")
        assert scanner.base_path == Path("/tmp").resolve()

    def test_pattern_matching(self):
        """Test pattern matching logic."""
        scanner = ModelScanner()

        # Test include pattern
        test_file = Path("app/models/user.py")
        assert scanner._matches_pattern(test_file, ["**/*.py"])

        # Test exclude pattern
        assert scanner._matches_pattern(Path("venv/lib/test.py"), ["**/venv/**"])

    def test_should_scan_file(self):
        """Test file scanning decision logic."""
        scanner = ModelScanner(
            include_patterns=["**/models/**/*.py"], exclude_patterns=["**/tests/**"]
        )

        # Should scan
        assert scanner._should_scan_file(Path("app/models/user.py"))

        # Should not scan (excluded)
        assert not scanner._should_scan_file(Path("app/tests/test_user.py"))

        # Should not scan (not included)
        assert not scanner._should_scan_file(Path("app/views/home.py"))

    def test_detect_sqlalchemy_model_with_base(self):
        """Test detection of SQLAlchemy models inheriting from Base."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test model file
            model_file = Path(tmpdir) / "user.py"
            model_file.write_text(
                """
from sqlalchemy import Column, Integer, String
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
"""
            )

            _, is_model, _ = scan_file_worker(model_file)
            assert is_model

    def test_detect_sqlalchemy_model_with_tablename(self):
        """Test detection via __tablename__ attribute."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_file = Path(tmpdir) / "post.py"
            model_file.write_text(
                """
class Post:
    __tablename__ = "posts"
    id = 1
"""
            )

            _, is_model, _ = scan_file_worker(model_file)
            assert is_model

    def test_ignore_non_model_classes(self):
        """Test that non-model classes are ignored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            regular_file = Path(tmpdir) / "utils.py"
            regular_file.write_text(
                """
class Helper:
    def do_something(self):
        pass
"""
            )

            _, is_model, _ = scan_file_worker(regular_file)
            assert not is_model

    def test_module_path_conversion(self):
        """Test conversion of file paths to module paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = ModelScanner(base_path=tmpdir)

            # Test regular file
            file_path = Path(tmpdir) / "app" / "models" / "user.py"
            module_path = scanner._get_module_path(file_path)
            assert module_path == "app.models.user"

            # Test __init__.py
            init_path = Path(tmpdir) / "app" / "models" / "__init__.py"
            module_path = scanner._get_module_path(init_path)
            assert module_path == "app.models"

    def test_discover_models_in_directory(self):
        """Test full discovery process."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create directory structure
            models_dir = Path(tmpdir) / "app" / "models"
            models_dir.mkdir(parents=True)

            # Create model files
            (models_dir / "user.py").write_text(
                """
from database import Base
class User(Base):
    __tablename__ = "users"
"""
            )

            (models_dir / "post.py").write_text(
                """
from database import Base
class Post(Base):
    __tablename__ = "posts"
"""
            )

            # Create non-model file
            (models_dir / "utils.py").write_text(
                """
def helper():
    pass
"""
            )

            scanner = ModelScanner(base_path=tmpdir)
            discovered = scanner.discover()

            assert "app.models.user" in discovered
            assert "app.models.post" in discovered
            assert "app.models.utils" not in discovered

    def test_exclude_patterns_work(self):
        """Test that exclude patterns properly filter files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test directory
            tests_dir = Path(tmpdir) / "tests"
            tests_dir.mkdir()

            # Create a model-like file in tests
            (tests_dir / "test_models.py").write_text(
                """
class User(Base):
    __tablename__ = "users"
"""
            )

            scanner = ModelScanner(base_path=tmpdir)
            discovered = scanner.discover()

            # Should not discover models in tests directory
            assert len(discovered) == 0

    def test_detect_sqlmodel(self):
        """Test detection of SQLModel models."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_file = Path(tmpdir) / "hero.py"
            model_file.write_text(
                """
from sqlmodel import SQLModel, Field

class Hero(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
"""
            )

            _, is_model, _ = scan_file_worker(model_file)
            assert is_model

    def test_detect_sqlmodel_functional(self):
        """Test detection of SQLModel models with functional syntax."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_file = Path(tmpdir) / "hero.py"
            model_file.write_text(
                """
from sqlmodel import SQLModel

class Hero(SQLModel(table=True)):
    pass
"""
            )

            _, is_model, _ = scan_file_worker(model_file)
            assert is_model

    def test_detect_as_declarative_decorator(self):
        """Test detection via decorators."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_file = Path(tmpdir) / "models.py"
            model_file.write_text(
                """
from sqlalchemy.ext.declarative import as_declarative

@as_declarative()
class Base:
    __tablename__ = "base"
"""
            )

            _, is_model, _ = scan_file_worker(model_file)
            assert is_model

    def test_detect_mapped_subscript(self):
        """Test detection of Mapped[Type] annotations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_file = Path(tmpdir) / "models.py"
            model_file.write_text(
                """
from sqlalchemy.orm import Mapped, DeclarativeBase

class User(DeclarativeBase):
    __tablename__ = "users"
    id: Mapped[int]
"""
            )

            _, is_model, _ = scan_file_worker(model_file)
            assert is_model

    def test_detect_imperative_mapping(self):
        """Test detection of imperative mapping."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_file = Path(tmpdir) / "models.py"
            model_file.write_text(
                """
from sqlalchemy.orm import registry
reg = registry()
reg.map_imperatively(User, table)
"""
            )

            _, is_model, _ = scan_file_worker(model_file)
            assert is_model

    def test_discover_with_cache(self):
        """Test discovery with cache enabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            models_dir = Path(tmpdir)
            model_file = models_dir / "user.py"
            model_file.write_text("class User:\n    __tablename__ = 'users'")

            scanner = ModelScanner(base_path=tmpdir, cache_enabled=True)
            discovered = scanner.discover()

            assert "user" in discovered
            cache_file = Path(tmpdir) / ".alembic-autoscan.cache"
            assert cache_file.exists()

            # Verify cache content
            with cache_file.open() as f:
                data = json.load(f)
                # Should find an entry where user keys exist
                # Format: {"hash": {"filepath": {...}}}
                assert len(data) > 0
                first_key = list(data.keys())[0]
                assert str(model_file.resolve()) in data[first_key]
                assert data[first_key][str(model_file.resolve())]["is_model"] is True

    def test_import_models(self):
        """Test importing discovered models."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_file = Path(tmpdir) / "mymodel.py"
            model_file.write_text("class User:\n    __tablename__ = 'users'")

            scanner = ModelScanner(base_path=tmpdir)
            scanner.discover()

            # Mock importlib.import_module
            with patch("importlib.import_module") as mock_import:
                count = scanner.import_models()
                assert count == 1
                mock_import.assert_called_with("mymodel")

    def test_import_models_error(self, capsys):
        """Test importing models with errors."""
        scanner = ModelScanner()

        def side_effect(name, package=None):
            if name == "nonexistent":
                raise ImportError("test")
            return MagicMock()

        with patch("alembic_autoscan.scanner.importlib.import_module", side_effect=side_effect):
            count = scanner.import_models(["nonexistent"])
            assert count == 0

            captured = capsys.readouterr()
            assert "Warning: Could not import nonexistent: test" in captured.err

    def test_matches_pattern_relative_error(self):
        """Test _matches_pattern when relative_to fails."""
        scanner = ModelScanner(base_path="/tmp")
        # Trying to make /etc relative to /tmp should raise ValueError
        path = Path("/etc/passwd")
        # Should fall back to original path and still work if pattern matches
        assert scanner._matches_pattern(path, ["/etc/*"])

    def test_detect_attribute_base(self):
        """Test detection of class User(db.Model)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_file = Path(tmpdir) / "models.py"
            model_file.write_text(
                """
import flask_sqlalchemy
db = flask_sqlalchemy.SQLAlchemy()
class User(db.Model):
    __tablename__ = "users"
"""
            )
            _, is_model, _ = scan_file_worker(model_file)
            assert is_model

    def test_detect_functional_base(self):
        """Test detection of class User(declarative_base())."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_file = Path(tmpdir) / "models.py"
            model_file.write_text(
                """
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
class User(Base):
    __tablename__ = "users"
"""
            )
            _, is_model, _ = scan_file_worker(model_file)
            assert is_model

    def test_ignore_abstract_class(self):
        """Test that abstract classes are ignored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_file = Path(tmpdir) / "models.py"
            model_file.write_text(
                """
class Base:
    __abstract__ = True
    __tablename__ = "base"
"""
            )
            _, is_model, abstracts = scan_file_worker(model_file)
            assert not is_model
            assert "Base" in abstracts


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
