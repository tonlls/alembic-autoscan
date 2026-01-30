# Example Project

This example demonstrates how to use `alembic-autoscan` with a simple SQLAlchemy project.

## Project Structure

```
sample_project/
├── database.py          # Database configuration and Base
├── models/
│   ├── __init__.py     # No manual imports needed!
│   ├── user.py         # User model
│   └── post.py         # Post model
├── alembic/
│   ├── env.py          # Uses alembic-autoscan
│   └── versions/       # Migration files
└── alembic.ini         # Alembic configuration
```

## Setup

1. Install dependencies:
```bash
pip install sqlalchemy alembic
pip install -e ../../  # Install alembic-autoscan from parent directory
```

2. Initialize the database:
```bash
python -c "from database import init_db; init_db()"
```

3. Create your first migration:
```bash
alembic revision --autogenerate -m "Initial migration"
```

Notice in the output that `alembic-autoscan` automatically discovered the User and Post models!

4. Apply the migration:
```bash
alembic upgrade head
```

## Key Points

### Traditional Approach (Without alembic-autoscan)

In `models/__init__.py`, you would need:
```python
from .user import User
from .post import Post
```

And in `alembic/env.py`, you would need:
```python
from models import User, Post  # Manual imports
from database import Base
target_metadata = Base.metadata
```

### With alembic-autoscan

In `models/__init__.py`:
```python
# Nothing needed! Or just documentation
```

In `alembic/env.py`:
```python
from alembic_autoscan import import_models
from database import Base

import_models(verbose=True)  # Automatically discovers and imports all models
target_metadata = Base.metadata
```

That's it! No more manual imports to maintain.

## Adding New Models

1. Create a new model file in `models/` (e.g., `models/comment.py`)
2. Run `alembic revision --autogenerate -m "Add comment model"`
3. The new model is automatically discovered - no code changes needed!
