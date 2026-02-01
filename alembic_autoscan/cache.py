"""
Cache management for alembic-autoscan.

Caches scan results based on file modification times to speed up
subsequent scans, especially in large codebases.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ScanCache:
    """Cache for model discovery results."""

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        enabled: bool = True,
    ):
        """
        Initialize scan cache.

        Args:
            cache_dir: Directory to store cache file (defaults to current directory)
            enabled: Whether caching is enabled
        """
        self.enabled = enabled
        self.cache_dir = cache_dir or Path.cwd()
        self.cache_file = self.cache_dir / ".alembic-autoscan.cache"
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _generate_cache_key(
        self,
        base_path: str,
        include_patterns: List[str],
        exclude_patterns: List[str],
    ) -> str:
        """Generate a unique cache key based on scan configuration."""
        key_data = (
            f"{base_path}:{','.join(sorted(include_patterns))}:{','.join(sorted(exclude_patterns))}"
        )
        return hashlib.sha256(key_data.encode()).hexdigest()

    def load(
        self,
        base_path: str,
        include_patterns: List[str],
        exclude_patterns: List[str],
    ) -> Optional[Dict[str, Tuple[float, bool, Optional[str]]]]:
        """
        Load cache for the given configuration.

        Args:
            base_path: Base path that was scanned
            include_patterns: Include patterns used
            exclude_patterns: Exclude patterns used

        Returns:
            Dictionary mapping file paths to (mtime, is_model, module_path)
            or None if cache doesn't exist or is invalid
        """
        if not self.enabled:
            return None

        if not self.cache_file.exists():
            logger.debug("No cache file found")
            return None

        try:
            with open(self.cache_file, encoding="utf-8") as f:
                all_caches = json.load(f)

            cache_key = self._generate_cache_key(base_path, include_patterns, exclude_patterns)

            if cache_key not in all_caches:
                logger.debug(f"No cache entry for key: {cache_key}")
                return None

            cache_data = all_caches[cache_key]
            logger.info(f"Loaded cache with {len(cache_data)} entries")

            # Convert to the expected format
            result: Dict[str, Tuple[float, bool, Optional[str]]] = {}
            for file_path, entry in cache_data.items():
                result[file_path] = (
                    entry["mtime"],
                    entry["is_model"],
                    entry.get("module_path"),
                )

            return result

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to load cache: {e}")
            return None

    def save(
        self,
        base_path: str,
        include_patterns: List[str],
        exclude_patterns: List[str],
        file_data: Dict[str, Tuple[float, bool, Optional[str]]],
    ) -> None:
        """
        Save cache for the given configuration.

        Args:
            base_path: Base path that was scanned
            include_patterns: Include patterns used
            exclude_patterns: Exclude patterns used
            file_data: Dictionary mapping file paths to (mtime, is_model, module_path)
        """
        if not self.enabled:
            return

        try:
            # Load existing cache file if it exists
            if self.cache_file.exists():
                with open(self.cache_file, encoding="utf-8") as f:
                    all_caches = json.load(f)
            else:
                all_caches = {}

            # Update cache for this configuration
            cache_key = self._generate_cache_key(base_path, include_patterns, exclude_patterns)

            # Convert to JSON-serializable format
            cache_entry = {}
            for file_path, (mtime, is_model, module_path) in file_data.items():
                cache_entry[file_path] = {
                    "mtime": mtime,
                    "is_model": is_model,
                    "module_path": module_path,
                }

            all_caches[cache_key] = cache_entry

            # Write back to file
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(all_caches, f, indent=2)

            logger.info(f"Saved cache with {len(cache_entry)} entries")

        except OSError as e:
            logger.warning(f"Failed to save cache: {e}")

    def invalidate(self) -> None:
        """Delete the cache file."""
        if self.cache_file.exists():
            try:
                self.cache_file.unlink()
                logger.info("Cache invalidated")
            except OSError as e:
                logger.warning(f"Failed to delete cache file: {e}")

    def is_file_modified(
        self,
        file_path: Path,
        cached_mtime: float,
    ) -> bool:
        """
        Check if a file has been modified since it was cached.

        Args:
            file_path: Path to the file
            cached_mtime: Cached modification time

        Returns:
            True if the file has been modified or doesn't exist
        """
        try:
            current_mtime = file_path.stat().st_mtime
            return current_mtime != cached_mtime
        except (OSError, FileNotFoundError):
            # File doesn't exist or can't be accessed
            return True
