"""
Utility functions for alembic-autoscan.
"""

from pathlib import Path
from typing import List


def parse_gitignore(gitignore_path: Path) -> List[str]:
    """
    Parse a .gitignore file and return a list of glob patterns.

    Args:
        gitignore_path: Path to the .gitignore file

    Returns:
        List of glob patterns
    """
    patterns: List[str] = []

    if not gitignore_path.exists():
        return patterns

    try:
        with open(gitignore_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Standardize patterns to resemble glob patterns used in scanner
                # This is a best-effort conversion

                # Handle negation
                pattern = line
                if pattern.startswith("!"):
                    # We don't support negation in exclude patterns currently
                    continue

                # Handle directory markers
                if pattern.endswith("/"):
                    pattern = pattern + "**"

                # Handle root-anchored patterns
                if pattern.startswith("/"):
                    # /dist -> dist/**
                    pattern = pattern[1:]
                else:
                    # node_modules -> **/node_modules/** if it's a directory or simple match
                    if "/" not in pattern:
                        # Simple name like 'venv' or '*.pyc'
                        if "*" in pattern:
                            pattern = "**/" + pattern
                        else:
                            # Could be file or directory, add both
                            patterns.append(f"**/{pattern}/**")
                            pattern = f"**/{pattern}"
                    else:
                        # my/path -> **/my/path
                        if not pattern.startswith("**/") and not pattern.startswith("*"):
                            pattern = f"**/{pattern}"

                patterns.append(pattern)

    except OSError:
        pass

    return patterns
