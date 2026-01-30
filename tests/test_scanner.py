"""
Tests for the ModelScanner class.
"""

import os
import tempfile
from pathlib import Path
import pytest

from alembic_autoscan.scanner import ModelScanner


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
            include_patterns=["**/models/**/*.py"],
            exclude_patterns=["**/tests/**"]
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
            model_file.write_text("""
from sqlalchemy import Column, Integer, String
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
""")
            
            scanner = ModelScanner(base_path=tmpdir)
            assert scanner._scan_file_for_models(model_file)

    def test_detect_sqlalchemy_model_with_tablename(self):
        """Test detection via __tablename__ attribute."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_file = Path(tmpdir) / "post.py"
            model_file.write_text("""
class Post:
    __tablename__ = "posts"
    id = 1
""")
            
            scanner = ModelScanner(base_path=tmpdir)
            assert scanner._scan_file_for_models(model_file)

    def test_ignore_non_model_classes(self):
        """Test that non-model classes are ignored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            regular_file = Path(tmpdir) / "utils.py"
            regular_file.write_text("""
class Helper:
    def do_something(self):
        pass
""")
            
            scanner = ModelScanner(base_path=tmpdir)
            assert not scanner._scan_file_for_models(regular_file)

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
            (models_dir / "user.py").write_text("""
from database import Base
class User(Base):
    __tablename__ = "users"
""")
            
            (models_dir / "post.py").write_text("""
from database import Base
class Post(Base):
    __tablename__ = "posts"
""")
            
            # Create non-model file
            (models_dir / "utils.py").write_text("""
def helper():
    pass
""")
            
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
            (tests_dir / "test_models.py").write_text("""
class User(Base):
    __tablename__ = "users"
""")
            
            scanner = ModelScanner(base_path=tmpdir)
            discovered = scanner.discover()
            
            # Should not discover models in tests directory
            assert len(discovered) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
