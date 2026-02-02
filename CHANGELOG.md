# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.1] - 2026-02-02

### Fixed
- Fixed `TypeError` when performing relative imports for modules inside excluded directories (like `.venv`).
- Improved robustness of pattern matching for directory exclusions.
- Resolved line length linting errors in `scanner.py`.

## [1.2.0] - 2026-02-02

### Added
- **Parallel Scanning**: Multi-process scanning for improved performance on large codebases.
- **Standard Ignore Support**: Automatically reads and respects `.gitignore` patterns.
- **Strict Mode**: Validation feature to ensure discovered modules can be successfully imported.
- **Security**: Added `SECURITY.md` for vulnerability reporting policy.

### Fixed
- Resolved Mypy type annotation errors in `config.py` and `utils.py`.

## [1.0.0] - 2026-02-01

### Added
- **Configuration System**: Support for `pyproject.toml` and `.alembic-autoscan.yaml` for managing scan settings.
- **Caching Mechanism**: Persistent scan results to speed up model discovery in large projects.
- **SQLModel Support**: Detection of SQLModel models (with `table=True`).
- **Abstract Class Detection**: Correctly identifies and skips classes with `__abstract__ = True`.
- **Improved Model Detection**:
    - Support for Imperative Mapping (`map_imperatively`).
    - Detection of `Mapped` type annotations and `mapped_column`.
    - Better handling of `as_declarative` and `declarative_base` decorators.
- **Enhanced CLI**: Command-line tool with discovery options and include/exclude filtering.
- **Logging**: Multi-level logging (DEBUG, INFO, WARNING, ERROR) for better transparency.
- **Developer Experience**:
    - Automatic project root detection.
    - Zero-configuration defaults.
    - Comprehensive test suite with coverage reporting.
- **Security & Quality**:
    - Integration of Bandit for security scanning.
    - Pre-commit hooks for Ruff (linting), Mypy (type checking), and Bandit (security).
    - GitHub Actions workflows for automated testing, security audits, and PyPI deployment.

### Fixed
- Improved robustness of glob pattern matching for complex directory structures.
- Fixed relative path resolution issues in different OS environments.
- Resolved various type hinting and linting errors.

## [0.1.0] - 2026-01-28

### Added
- Initial release of alembic-autoscan
- AST-based model discovery for SQLAlchemy models
- Automatic import functionality for Alembic migrations
- Support for pattern-based include/exclude filtering
- Integration helpers for easy Alembic env.py setup
- Project root detection utility
- Comprehensive test suite
- Example project demonstrating usage
- Full documentation and README

### Features
- Discovers models inheriting from `DeclarativeBase`
- Detects models using `declarative_base()`
- Identifies models with `__tablename__` attribute
- Configurable scanning patterns
- Verbose mode for debugging
- Zero-configuration default setup

[1.2.1]: https://github.com/tonlls/alembic-autoscan/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/tonlls/alembic-autoscan/compare/v1.0.0...v1.2.0
[1.0.0]: https://github.com/tonlls/alembic-autoscan/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/tonlls/alembic-autoscan/releases/tag/v0.1.0
