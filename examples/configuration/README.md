# Example Configuration Files for Alembic Autoscan

This directory contains example configuration files demonstrating different configuration options.

## Using pyproject.toml

Add this section to your `pyproject.toml`:

```toml
[tool.alembic-autoscan]
base_path = "./src"
include_patterns = ["**/models/**/*.py"]
exclude_patterns = ["**/tests/**", "**/test_*.py"]
log_level = "INFO"
cache_enabled = true
```

## Using .alembic-autoscan.yaml

Create a `.alembic-autoscan.yaml` file in your project root:

```yaml
base_path: ./app
include_patterns:
  - "**/models/**/*.py"
  - "**/models.py"
exclude_patterns:
  - "**/tests/**"
  - "**/migrations/**"
log_level: INFO
cache_enabled: true
```

## Configuration Priority

Configuration is loaded with the following priority (highest to lowest):

1. **Programmatic arguments** - Parameters passed directly to `import_models()`
2. **pyproject.toml** - `[tool.alembic-autoscan]` section
3. **YAML file** - `.alembic-autoscan.yaml` in project root
4. **Defaults** - Built-in sensible defaults

## Available Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `base_path` | string | `"."` | Root directory to start scanning |
| `include_patterns` | list[string] | `["**/*.py"]` | Glob patterns to include |
| `exclude_patterns` | list[string] | See defaults | Glob patterns to exclude |
| `log_level` | string | `"WARNING"` | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `cache_enabled` | boolean | `true` | Enable/disable caching |
| `parallel_enabled` | boolean | `null` | Enable parallel scanning (auto-detect if null) |
| `parallel_threshold` | integer | `100` | Minimum files for parallel mode |
