# Quick Start Guide

Get started with `alembic-autoscan` in 2 minutes!

## Installation

```bash
pip install alembic-autoscan
```

## Usage

### Step 1: Modify your Alembic env.py

Open your `alembic/env.py` file and add these lines **before** setting `target_metadata`:

```python
from alembic_autoscan import import_models

# Automatically discover and import all models
import_models()
```

### Complete Example

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Add this import
from alembic_autoscan import import_models

# Import your Base
from myapp.database import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ✨ Magic happens here - automatically imports all models
import_models()

# Set target metadata
target_metadata = Base.metadata

# ... rest of your env.py file
```

### Step 2: That's it!

Now when you run Alembic commands, all your models will be automatically discovered:

```bash
# Create a migration
alembic revision --autogenerate -m "Add new models"

# Apply migrations
alembic upgrade head
```

## Advanced Configuration

### Customize Scanning

```python
import_models(
    base_path="./src",                    # Where to start scanning
    include_patterns=["**/models/**"],    # Only scan these paths
    exclude_patterns=["**/tests/**"],     # Skip these paths
    verbose=True                          # Print discovered models
)
```

### Use Project Root Detection

```python
from alembic_autoscan import import_models_from_project_root

# Automatically finds your project root and scans from there
import_models_from_project_root(verbose=True)
```

## What Gets Discovered?

The library automatically finds classes that:
- Inherit from `DeclarativeBase` or `Base`
- Use `declarative_base()`
- Have a `__tablename__` attribute
- Contain SQLAlchemy `Column` definitions

## Troubleshooting

**Models not being discovered?**
- Enable verbose mode: `import_models(verbose=True)`
- Check your include/exclude patterns
- Ensure models inherit from SQLAlchemy base classes

**Import errors?**
- Make sure your project is in Python's path
- Check that all dependencies are installed

## Next Steps

- Check out the [full documentation](README.md)
- See the [example project](examples/sample_project/)
- Read about [configuration options](README.md#configuration-options)

Happy migrating! 🚀
