"""
Tests for the configuration system.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from alembic_autoscan.config import Config, _find_config_file, load_config, setup_logging


class TestConfig:
    """Test suite for Config class."""

    def test_config_initialization(self):
        """Test that Config initializes with correct defaults."""
        config = Config()
        assert config.base_path == "."
        assert config.include_patterns == ["**/*.py"]
        assert config.exclude_patterns == []
        assert config.log_level == "WARNING"
        assert config.cache_enabled is True
        assert config.parallel_enabled is None
        assert config.parallel_threshold == 100

    def test_config_custom_values(self):
        """Test Config with custom values."""
        config = Config(
            base_path="/tmp/test",
            include_patterns=["**/models/**"],
            exclude_patterns=["**/tests/**"],
            log_level="DEBUG",
            cache_enabled=False,
            parallel_enabled=True,
            parallel_threshold=50,
        )
        assert config.base_path == "/tmp/test"
        assert config.include_patterns == ["**/models/**"]
        assert config.exclude_patterns == ["**/tests/**"]
        assert config.log_level == "DEBUG"
        assert config.cache_enabled is False
        assert config.parallel_enabled is True
        assert config.parallel_threshold == 50

    def test_config_to_dict(self):
        """Test Config.to_dict() method."""
        config = Config(base_path="/test", log_level="INFO")
        data = config.to_dict()

        assert data["base_path"] == "/test"
        assert data["log_level"] == "INFO"
        assert "include_patterns" in data
        assert "cache_enabled" in data

    def test_config_from_dict(self):
        """Test Config.from_dict() factory method."""
        data = {
            "base_path": "/test",
            "include_patterns": ["**/*.py"],
            "log_level": "DEBUG",
            "cache_enabled": False,
        }
        config = Config.from_dict(data)

        assert config.base_path == "/test"
        assert config.include_patterns == ["**/*.py"]
        assert config.log_level == "DEBUG"
        assert config.cache_enabled is False


class TestConfigFileLoading:
    """Test configuration file loading."""

    def test_find_config_file(self):
        """Test finding config file in directory tree."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested directory structure
            nested_dir = Path(tmpdir) / "a" / "b" / "c"
            nested_dir.mkdir(parents=True)

            # Create config file in root
            config_file = Path(tmpdir) / ".alembic-autoscan.yaml"
            config_file.write_text("test: true")

            # Should find config from nested directory
            found = _find_config_file(start_path=nested_dir)
            assert found == config_file

    def test_find_config_file_not_found(self):
        """Test when config file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            found = _find_config_file(start_path=Path(tmpdir))
            assert found is None

    def test_load_config_with_programmatic_args(self):
        """Test that programmatic arguments have highest priority."""
        config = load_config(
            base_path="/test",
            log_level="DEBUG",
            cache_enabled=False,
        )

        assert config.base_path == "/test"
        assert config.log_level == "DEBUG"
        assert config.cache_enabled is False

    def test_load_config_defaults(self):
        """Test loading config with all defaults."""
        config = load_config()

        assert config.base_path == "."
        assert config.log_level == "WARNING"
        assert config.cache_enabled is True

    def test_load_yaml_config(self, tmp_path):
        """Test loading configuration from YAML file."""
        yaml_file = tmp_path / ".alembic-autoscan.yaml"
        yaml_file.write_text("base_path: /yaml/path\nlog_level: DEBUG")

        from alembic_autoscan.config import _load_yaml_config

        data = _load_yaml_config(yaml_file)

        assert data["base_path"] == "/yaml/path"
        assert data["log_level"] == "DEBUG"

    def test_load_toml_config(self, tmp_path):
        """Test loading configuration from pyproject.toml."""
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text(
            '[tool.alembic-autoscan]\nbase_path = "/toml/path"\nlog_level = "INFO"'
        )

        from alembic_autoscan.config import _load_toml_config

        data = _load_toml_config(toml_file)

        assert data["base_path"] == "/toml/path"
        assert data["log_level"] == "INFO"

    def test_load_config_with_explicit_file(self, tmp_path):
        """Test load_config with explicit config file."""
        config_file = tmp_path / "custom.yaml"
        config_file.write_text("base_path: /custom/path")

        config = load_config(config_file=str(config_file))
        assert config.base_path == "/custom/path"

    def test_find_config_file_max_depth(self, tmp_path):
        """Test max_depth limit in _find_config_file."""
        root = tmp_path
        config_file = root / ".alembic-autoscan.yaml"
        config_file.touch()

        # Create a deep directory structure
        current = root
        for i in range(15):
            current = current / str(i)
            current.mkdir()

        # With default max_depth (10), it shouldn't find it from depth 15
        found = _find_config_file(start_path=current, max_depth=10)
        assert found is None

        # With higher max_depth, it should find it
        found = _find_config_file(start_path=current, max_depth=20)
        assert found == config_file

    def test_load_yaml_no_pyyaml(self, tmp_path):
        """Test behavior when PyYAML is not installed."""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.touch()

        with patch("alembic_autoscan.config.yaml", None):
            from alembic_autoscan.config import _load_yaml_config

            data = _load_yaml_config(yaml_file)
            assert data == {}

    def test_load_toml_no_tomllib(self, tmp_path):
        """Test behavior when tomllib/tomli is not available."""
        toml_file = tmp_path / "pyproject.toml"
        toml_file.touch()

        with patch("alembic_autoscan.config.tomllib", None):
            from alembic_autoscan.config import _load_toml_config

            data = _load_toml_config(toml_file)
            assert data == {}

    def test_load_yaml_exception(self, tmp_path):
        """Test YAML load exception handling."""
        yaml_file = tmp_path / "error.yaml"
        yaml_file.write_text("!!python/object:nonexistent.Class {}")

        from alembic_autoscan.config import _load_yaml_config

        # This should be caught and return {}
        data = _load_yaml_config(yaml_file)
        assert data == {}

    def test_load_toml_exception(self, tmp_path):
        """Test TOML load exception handling."""
        toml_file = tmp_path / "error.toml"
        toml_file.write_text("invalid = [toml")

        from alembic_autoscan.config import _load_toml_config

        # This should be caught and return {}
        data = _load_toml_config(toml_file)
        assert data == {}


class TestLoggingSetup:
    """Test logging configuration."""

    def test_setup_logging_with_string(self):
        """Test setup_logging with string level."""
        import logging

        setup_logging("DEBUG")
        logger = logging.getLogger("alembic_autoscan")
        assert logger.level == logging.DEBUG

        setup_logging("INFO")
        assert logger.level == logging.INFO

    def test_setup_logging_with_int(self):
        """Test setup_logging with numeric level."""
        import logging

        setup_logging(logging.WARNING)
        logger = logging.getLogger("alembic_autoscan")
        assert logger.level == logging.WARNING


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
