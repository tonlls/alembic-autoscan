# Alembic Autoscan

🚀 **Automatically discover and import SQLAlchemy models for Alembic migrations**

Stop manually maintaining model imports in your Alembic `env.py` file! This library automatically scans your codebase for SQLAlchemy models and imports them for you.

## Features

- 🔍 **Automatic Discovery**: Scans your project for SQLAlchemy model classes
- 🛡️ **Safe AST Parsing**: Uses Abstract Syntax Tree parsing - no code execution required
- ⚙️ **Configurable**: Include/exclude patterns for fine-grained control
- 🎯 **Zero Configuration**: Works out of the box with sensible defaults
- 🔌 **Easy Integration**: Drop-in replacement for manual imports in `env.py`

## Installation

```bash
pip install alembic-autoscan
```

## CLI Usage

You can test model discovery from the command line:

```bash
# Scan the current directory
alembic-autoscan discover

# Scan a specific directory
alembic-autoscan discover ./app

# Scan with include/exclude patterns
alembic-autoscan discover ./app --include "**/models/**" --exclude "**/tests/**"
```

## Quick Start

### Basic Usage

In your Alembic `env.py` file, replace manual model imports with:

```python
from alembic_autoscan import import_models

# Automatically discover and import all models
import_models()

# Now your target_metadata will include all discovered models
from your_app.database import Base
target_metadata = Base.metadata
```

### Advanced Usage

```python
from alembic_autoscan import import_models

# Customize the discovery process
import_models(
    base_path="./src",                    # Start scanning from this directory
    include_patterns=["**/models/**"],    # Only scan these paths
    exclude_patterns=["**/tests/**"],     # Skip these paths
)
```

### Manual Scanner Usage

For more control, use the `ModelScanner` directly:

```python
from alembic_autoscan import ModelScanner

scanner = ModelScanner(
    base_path="./app",
    include_patterns=["**/models/**"],
    exclude_patterns=["**/tests/**", "**/migrations/**"]
)

# Get list of discovered model modules
models = scanner.discover()
print(f"Found {len(models)} model modules")

# Import them
scanner.import_models()
```

## How It Works

1. **Scans** your Python files using AST (Abstract Syntax Tree) parsing
2. **Identifies** classes that inherit from SQLAlchemy's `DeclarativeBase` or use `declarative_base()`
3. **Imports** the discovered model modules automatically
4. **Registers** them with SQLAlchemy's metadata for Alembic to use

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_path` | `str` | `"."` | Root directory to start scanning |
| `include_patterns` | `List[str]` | `["**/*.py"]` | Glob patterns for files to include |
| `exclude_patterns` | `List[str]` | `["**/venv/**", "**/env/**", ...]` | Glob patterns for files to exclude |

## Common Patterns

### Django-style Models Directory

```python
import_models(
    base_path="./myapp",
    include_patterns=["**/models.py", "**/models/**/*.py"]
)
```

### Multiple App Structure

```python
import_models(
    base_path="./apps",
    include_patterns=["**/models/**"],
    exclude_patterns=["**/tests/**", "**/migrations/**"]
)
```

### Monorepo with Multiple Services

```python
import_models(
    base_path="./services/user-service",
    include_patterns=["**/models/**"]
)
```

## Requirements

- Python 3.8+
- SQLAlchemy 1.4+
- Alembic 1.7+

## Development

```bash
# Clone the repository
git clone https://github.com/tonlls/alembic-autoscan.git
cd alembic-autoscan

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format and lint code
ruff check --fix .
ruff format .
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Troubleshooting

### Models not being discovered?

1. Ensure your models inherit from SQLAlchemy's `DeclarativeBase` or use `declarative_base()`
2. Check that your model files match the `include_patterns`
3. Verify files aren't being excluded by `exclude_patterns`
4. Enable debug logging to see what's being scanned

### Import errors?

Make sure your project is properly installed or the Python path is configured correctly so that model modules can be imported.

## Acknowledgments

Inspired by the common frustration of maintaining manual imports in Alembic migrations. Built with ❤️ for the Python community.
