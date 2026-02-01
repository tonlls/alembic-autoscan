"""
Example: Using alembic-autoscan with configuration files
"""

from alembic_autoscan import import_models, setup_logging

# Example 1: Let configuration be loaded from pyproject.toml or .alembic-autoscan.yaml
setup_logging("INFO")
count = import_models()
print(f"Imported {count} models using configuration file")

# Example 2: Override configuration file settings
count = import_models(
    log_level="DEBUG",  # Override log level
    cache_enabled=False,  # Disable cache for this run
)
print(f"Imported {count} models with overrides")

# Example 3: Dry-run mode to preview what would be imported
count = import_models(
    base_path="./app",
    dry_run=True,
)
print(f"Would import {count} models (dry-run)")

# Example 4: Programmatic configuration (highest priority)
count = import_models(
    base_path="./src",
    include_patterns=["**/models/**"],
    exclude_patterns=["**/tests/**"],
    log_level="INFO",
    cache_enabled=True,
)
print(f"Imported {count} models with programmatic config")
