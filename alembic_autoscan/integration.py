"""
Integration helpers for using alembic-autoscan with Alembic env.py.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional

from .scanner import ModelScanner


def import_models(
    base_path: Optional[str] = None,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    verbose: bool = False,
) -> int:
    """
    Discover and import all SQLAlchemy models in the codebase.

    This is the main convenience function to use in Alembic's env.py file.

    Args:
        base_path: Root directory to scan. Defaults to current working directory.
        include_patterns: Glob patterns for files to include (default: ["**/*.py"])
        exclude_patterns: Glob patterns for files to exclude
        verbose: If True, print information about discovered models

    Returns:
        Number of successfully imported model modules

    Example:
        In your Alembic env.py:

        ```python
        from alembic_autoscan import import_models

        # Import all models
        import_models()

        # Or with custom configuration
        import_models(
            base_path="./app",
            include_patterns=["**/models/**"],
            exclude_patterns=["**/tests/**"]
        )

        # Then use your Base metadata as usual
        from myapp.database import Base
        target_metadata = Base.metadata
        ```
    """
    # Default to current working directory if not specified
    if base_path is None:
        base_path = os.getcwd()

    # Create scanner
    scanner = ModelScanner(
        base_path=base_path,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
    )

    # Discover models
    modules = scanner.discover()

    if verbose:
        print(f"[alembic-autoscan] Discovered {len(modules)} model modules:")
        for module in modules:
            print(f"  - {module}")

    # Import models
    imported_count = scanner.import_models(modules)

    if verbose:
        print(f"[alembic-autoscan] Successfully imported {imported_count} modules")

    return imported_count


def get_project_root(marker_files: Optional[List[str]] = None) -> Path:
    """
    Find the project root directory by looking for marker files.

    Args:
        marker_files: List of files that indicate project root
                     (default: ["pyproject.toml", "setup.py", ".git"])

    Returns:
        Path to project root

    Example:
        ```python
        from alembic_autoscan import import_models, get_project_root

        project_root = get_project_root()
        import_models(base_path=str(project_root))
        ```
    """
    if marker_files is None:
        marker_files = ["pyproject.toml", "setup.py", "setup.cfg", ".git"]

    current = Path.cwd()

    # Walk up the directory tree
    for parent in [current] + list(current.parents):
        for marker in marker_files:
            if (parent / marker).exists():
                return parent

    # If no marker found, return current directory
    return current


def import_models_from_project_root(
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    verbose: bool = False,
) -> int:
    """
    Convenience function that automatically finds project root and imports models.

    This is useful when your Alembic migrations are in a subdirectory and you want
    to scan from the project root.

    Args:
        include_patterns: Glob patterns for files to include
        exclude_patterns: Glob patterns for files to exclude
        verbose: If True, print information about discovered models

    Returns:
        Number of successfully imported model modules

    Example:
        ```python
        from alembic_autoscan import import_models_from_project_root

        # Automatically find project root and import all models
        import_models_from_project_root(verbose=True)
        ```
    """
    project_root = get_project_root()

    if verbose:
        print(f"[alembic-autoscan] Project root: {project_root}")

    return import_models(
        base_path=str(project_root),
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
        verbose=verbose,
    )
