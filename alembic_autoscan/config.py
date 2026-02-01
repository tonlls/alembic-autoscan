"""
Configuration management for alembic-autoscan.

Supports loading configuration from multiple sources with priority:
1. Programmatic arguments (highest priority)
2. pyproject.toml [tool.alembic-autoscan]
3. .alembic-autoscan.yaml
4. Defaults (lowest priority)
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    import tomllib  # type: ignore # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # type: ignore # Fallback for Python 3.8-3.10
    except ImportError:
        tomllib = None  # type: ignore

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


class Config:
    """Configuration container for alembic-autoscan."""

    def __init__(
        self,
        base_path: Optional[str] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        log_level: str = "WARNING",
        cache_enabled: bool = True,
        parallel_enabled: Optional[bool] = None,
        parallel_threshold: int = 100,
    ):
        """
        Initialize configuration.

        Args:
            base_path: Root directory to scan
            include_patterns: Glob patterns for files to include
            exclude_patterns: Glob patterns for files to exclude
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            cache_enabled: Whether to use caching
            parallel_enabled: Whether to use parallel scanning (None = auto-detect)
            parallel_threshold: Minimum number of files to enable parallel scanning
        """
        self.base_path = base_path or "."
        self.include_patterns = include_patterns or ["**/*.py"]
        self.exclude_patterns = exclude_patterns or []
        self.log_level = log_level.upper()
        self.cache_enabled = cache_enabled
        self.parallel_enabled = parallel_enabled
        self.parallel_threshold = parallel_threshold

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "base_path": self.base_path,
            "include_patterns": self.include_patterns,
            "exclude_patterns": self.exclude_patterns,
            "log_level": self.log_level,
            "cache_enabled": self.cache_enabled,
            "parallel_enabled": self.parallel_enabled,
            "parallel_threshold": self.parallel_threshold,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create configuration from dictionary."""
        return cls(
            base_path=data.get("base_path"),
            include_patterns=data.get("include_patterns"),
            exclude_patterns=data.get("exclude_patterns"),
            log_level=data.get("log_level", "WARNING"),
            cache_enabled=data.get("cache_enabled", True),
            parallel_enabled=data.get("parallel_enabled"),
            parallel_threshold=data.get("parallel_threshold", 100),
        )


def _find_config_file(
    start_path: Optional[Path] = None,
    filename: str = ".alembic-autoscan.yaml",
    max_depth: int = 10,
) -> Optional[Path]:
    """
    Find configuration file by walking up the directory tree.

    Args:
        start_path: Directory to start searching from
        filename: Configuration filename to look for
        max_depth: Maximum number of parent directories to check

    Returns:
        Path to config file if found, None otherwise
    """
    current = start_path or Path.cwd()

    for i, parent in enumerate([current] + list(current.parents)):
        if i >= max_depth:
            break

        config_path = parent / filename
        if config_path.exists():
            logger.debug(f"Found config file: {config_path}")
            return config_path

    return None


def _load_yaml_config(config_path: Path) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if yaml is None:
        logger.warning(
            f"PyYAML not installed, cannot load {config_path}. " "Install with: pip install pyyaml"
        )
        return {}

    try:
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            logger.debug(f"Loaded YAML config from {config_path}")
            return data or {}
    except Exception as e:
        logger.warning(f"Failed to load YAML config from {config_path}: {e}")
        return {}


def _load_toml_config(config_path: Path) -> Dict[str, Any]:
    """Load configuration from pyproject.toml [tool.alembic-autoscan] section."""
    if tomllib is None:
        logger.warning(
            "tomli/tomllib not available, cannot load pyproject.toml configuration. "
            "For Python 3.8-3.10, install with: pip install tomli"
        )
        return {}

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
            tool_dict = data.get("tool", {})
            if isinstance(tool_dict, dict):
                tool_config = tool_dict.get("alembic-autoscan", {})
                if isinstance(tool_config, dict):
                    if tool_config:
                        logger.debug(f"Loaded TOML config from {config_path}")
                    return tool_config
            return {}
    except Exception as e:
        logger.warning(f"Failed to load TOML config from {config_path}: {e}")
        return {}


def load_config(
    base_path: Optional[str] = None,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    log_level: Optional[str] = None,
    cache_enabled: Optional[bool] = None,
    parallel_enabled: Optional[bool] = None,
    parallel_threshold: Optional[int] = None,
    config_file: Optional[str] = None,
) -> Config:
    """
    Load configuration from multiple sources with priority.

    Priority order (highest to lowest):
    1. Programmatic arguments (passed to this function)
    2. pyproject.toml [tool.alembic-autoscan]
    3. .alembic-autoscan.yaml
    4. Defaults

    Args:
        base_path: Root directory to scan
        include_patterns: Glob patterns for files to include
        exclude_patterns: Glob patterns for files to exclude
        log_level: Logging level
        cache_enabled: Whether to use caching
        parallel_enabled: Whether to use parallel scanning
        parallel_threshold: Minimum files for parallel scanning
        config_file: Explicit path to config file (YAML or TOML)

    Returns:
        Config object with merged configuration
    """
    # Start with defaults
    config_data: Dict[str, Any] = {}

    # Try to find and load YAML config
    if config_file:
        config_path = Path(config_file)
        if config_path.exists():
            config_data.update(_load_yaml_config(config_path))
    else:
        yaml_path = _find_config_file(filename=".alembic-autoscan.yaml")
        if yaml_path:
            config_data.update(_load_yaml_config(yaml_path))

    # Try to find and load TOML config (higher priority than YAML)
    toml_path = _find_config_file(filename="pyproject.toml")
    if toml_path:
        toml_data = _load_toml_config(toml_path)
        if toml_data:
            config_data.update(toml_data)

    # Override with programmatic arguments (highest priority)
    if base_path is not None:
        config_data["base_path"] = base_path
    if include_patterns is not None:
        config_data["include_patterns"] = include_patterns
    if exclude_patterns is not None:
        config_data["exclude_patterns"] = exclude_patterns
    if log_level is not None:
        config_data["log_level"] = log_level
    if cache_enabled is not None:
        config_data["cache_enabled"] = cache_enabled
    if parallel_enabled is not None:
        config_data["parallel_enabled"] = parallel_enabled
    if parallel_threshold is not None:
        config_data["parallel_threshold"] = parallel_threshold

    return Config.from_dict(config_data)


def setup_logging(log_level: Union[str, int] = "WARNING") -> None:
    """
    Configure logging for alembic-autoscan.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR) or numeric level
    """
    if isinstance(log_level, str):
        numeric_level = getattr(logging, log_level.upper(), logging.WARNING)
    else:
        numeric_level = log_level

    # Configure root logger for alembic_autoscan
    logger = logging.getLogger("alembic_autoscan")
    logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create console handler with formatting
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(numeric_level)

    formatter = logging.Formatter("[%(name)s] %(levelname)s: %(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False
