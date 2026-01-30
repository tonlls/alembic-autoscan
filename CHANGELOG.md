# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.1.0]: https://github.com/tonlls/alembic-autoscan/releases/tag/v0.1.0
