from unittest.mock import MagicMock, patch

from alembic_autoscan.config import _load_toml_config, _load_yaml_config, load_config


def test_load_config_all_args():
    # Covers arguments passed to load_config
    config = load_config(
        base_path="/tmp",
        include_patterns=["*.py"],
        exclude_patterns=["test"],
        log_level="DEBUG",
        cache_enabled=False,
        parallel_enabled=True,
        parallel_threshold=500,
        strict_mode=True,
    )
    assert config.base_path == "/tmp"
    assert config.include_patterns == ["*.py"]
    assert config.exclude_patterns == ["test"]
    assert config.log_level == "DEBUG"
    assert config.cache_enabled is False
    assert config.parallel_enabled is True
    assert config.parallel_threshold == 500
    assert config.strict_mode is True


def test_load_toml_config_structure(tmp_path):
    # Case 1: [tool] but no [tool.alembic-autoscan]
    p = tmp_path / "pyproject.toml"
    p.write_text('[tool]\nother = "stuff"')
    assert _load_toml_config(p) == {}

    # Case 2: [tool.alembic-autoscan] is not a dict
    with patch("alembic_autoscan.config.tomllib.load", return_value={"tool": "not_a_dict"}):
        assert _load_toml_config(p) == {}

    with patch(
        "alembic_autoscan.config.tomllib.load",
        return_value={"tool": {"alembic-autoscan": "not_a_dict"}},
    ):
        assert _load_toml_config(p) == {}


def test_load_yaml_config_exception(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text("invalid: yaml")
    with patch("alembic_autoscan.config.yaml.safe_load", side_effect=ValueError("Boom")):
        assert _load_yaml_config(p) == {}


def test_load_yaml_config_not_installed():
    with patch("alembic_autoscan.config.yaml", None):
        assert _load_yaml_config(MagicMock()) == {}


def test_load_toml_config_not_installed():
    with patch("alembic_autoscan.config.tomllib", None):
        assert _load_toml_config(MagicMock()) == {}
