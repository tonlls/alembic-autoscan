"""
Database configuration for the complex example project.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Create the declarative base
Base = declarative_base()

# Database URL (SQLite for this example)
DATABASE_URL = "sqlite:///./complex_example.db"

# Create engine
engine = create_engine(DATABASE_URL, echo=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=engine)
