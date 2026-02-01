"""
Tests for the caching system.
"""

import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from alembic_autoscan.cache import ScanCache


class TestScanCache:
    """Test suite for ScanCache."""

    def test_cache_initialization(self):
        """Test cache initializes correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ScanCache(cache_dir=Path(tmpdir), enabled=True)
            assert cache.enabled is True
            assert cache.cache_file == Path(tmpdir) / ".alembic-autoscan.cache"

    def test_cache_disabled(self):
        """Test cache operations when disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ScanCache(cache_dir=Path(tmpdir), enabled=False)

            # Should return None when loading
            result = cache.load("/test", ["**/*.py"], [])
            assert result is None

            # Should not save when disabled
            cache.save("/test", ["**/*.py"], [], {})
            assert not cache.cache_file.exists()

    def test_cache_save_and_load(self):
        """Test saving and loading cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ScanCache(cache_dir=Path(tmpdir))

            file_data = {
                "/path/to/file.py": (1234567890.0, True, "models.file"),
                "/path/to/other.py": (1234567891.0, False, None),
            }

            # Save cache
            cache.save("/test", ["**/*.py"], ["**/tests/**"], file_data)
            assert cache.cache_file.exists()

            # Load cache
            loaded = cache.load("/test", ["**/*.py"], ["**/tests/**"])
            assert loaded is not None
            assert len(loaded) == 2
            assert loaded["/path/to/file.py"] == (1234567890.0, True, "models.file")
            assert loaded["/path/to/other.py"] == (1234567891.0, False, None)

    def test_cache_key_generation(self):
        """Test that different configurations generate different cache keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ScanCache(cache_dir=Path(tmpdir))

            # Save with first configuration
            cache.save("/test1", ["**/*.py"], [], {"file1.py": (1.0, True, "mod1")})

            # Save with different configuration
            cache.save("/test2", ["**/*.py"], [], {"file2.py": (2.0, True, "mod2")})

            # Both should be retrievable
            data1 = cache.load("/test1", ["**/*.py"], [])
            data2 = cache.load("/test2", ["**/*.py"], [])

            assert data1 is not None
            assert data2 is not None
            assert "file1.py" in data1
            assert "file2.py" in data2

    def test_cache_invalidation(self):
        """Test cache invalidation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ScanCache(cache_dir=Path(tmpdir))

            # Save cache
            cache.save("/test", ["**/*.py"], [], {"file.py": (1.0, True, "mod")})
            assert cache.cache_file.exists()

            # Invalidate
            cache.invalidate()
            assert not cache.cache_file.exists()

    def test_is_file_modified(self):
        """Test file modification detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ScanCache(cache_dir=Path(tmpdir))

            # Create a test file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("# test")

            # Get initial mtime
            mtime = test_file.stat().st_mtime

            # Should not be modified
            assert not cache.is_file_modified(test_file, mtime)

            # Modify file (wait a bit to ensure mtime changes)
            time.sleep(0.01)
            test_file.write_text("# modified")

            # Should be detected as modified
            assert cache.is_file_modified(test_file, mtime)

    def test_is_file_modified_missing_file(self):
        """Test modification check for non-existent file."""
        cache = ScanCache()

        # Non-existent file should be considered modified
        assert cache.is_file_modified(Path("/nonexistent/file.py"), 12345.0)

    def test_cache_with_none_module_path(self):
        """Test caching files that are not models."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ScanCache(cache_dir=Path(tmpdir))

            file_data = {
                "/path/to/model.py": (1.0, True, "models.model"),
                "/path/to/util.py": (2.0, False, None),  # Not a model
            }

            cache.save("/test", ["**/*.py"], [], file_data)
            loaded = cache.load("/test", ["**/*.py"], [])

            assert loaded is not None
            assert loaded["/path/to/util.py"] == (2.0, False, None)

    def test_load_corrupted_cache(self, tmp_path):
        """Test loading a corrupted cache file."""
        cache = ScanCache(cache_dir=tmp_path)
        cache.cache_file.write_text("not json")

        # Should return None and not raise exception
        result = cache.load(".", ["*"], [])
        assert result is None

    def test_save_io_error(self, tmp_path):
        """Test saving cache with IO error."""
        cache = ScanCache(cache_dir=tmp_path)

        # Mock open to raise IOError
        with patch("builtins.open", side_effect=OSError("disk full")):
            # Should not raise exception
            cache.save(".", ["*"], [], {"f": (1.0, True, "m")})

    def test_invalidate_os_error(self, tmp_path):
        """Test invalidating cache with OS error."""
        cache = ScanCache(cache_dir=tmp_path)
        cache.cache_file.touch()

        # Mock unlink to raise OSError
        with patch.object(Path, "unlink", side_effect=OSError("permission denied")):
            # Should not raise exception
            cache.invalidate()

    def test_load_no_cache_file(self, tmp_path):
        """Test loading when cache file does not exist."""
        cache = ScanCache(cache_dir=tmp_path)
        # Ensure file doesn't exist
        if cache.cache_file.exists():
            cache.cache_file.unlink()

        result = cache.load(".", ["*"], [])
        assert result is None

    def test_load_missing_key(self, tmp_path):
        """Test loading when cache file exists but key is missing."""
        cache = ScanCache(cache_dir=tmp_path)
        # Create cache with some data
        cache.save("other_path", ["*"], [], {"f": (1.0, True, "m")})

        # Try to load with different path (different key)
        result = cache.load("new_path", ["*"], [])
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
