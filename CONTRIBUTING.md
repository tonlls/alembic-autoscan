# Contributing to Alembic Autoscan

Thank you for your interest in contributing! Here are some guidelines to help you get started.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/tonlls/alembic-autoscan.git
cd alembic-autoscan
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e ".[dev]"
```

4. Install pre-commit hooks:
```bash
pre-commit install
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=alembic_autoscan --cov-report=html

# Run specific test file
pytest tests/test_scanner.py -v
```

We use `ruff` for code formatting and linting:

```bash
# Format and lint
ruff check --fix .
ruff format .
```

## Type Checking

We use `mypy` for type checking:

```bash
mypy alembic_autoscan
```

## Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure they pass
5. Format and lint code with ruff
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Reporting Issues

When reporting issues, please include:
- Python version
- SQLAlchemy version
- Alembic version
- A minimal reproducible example
- Expected vs actual behavior

## Feature Requests

We welcome feature requests! Please open an issue describing:
- The use case
- Why it would be useful
- Potential implementation approach (optional)

Thank you for contributing! 🎉
