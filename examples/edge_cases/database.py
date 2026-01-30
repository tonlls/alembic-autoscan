from sqlalchemy.orm import DeclarativeBase, registry

class Base(DeclarativeBase):
    pass

# A second base for testing multiple bases
class SecondBase(DeclarativeBase):
    pass

# For imperative mapping
mapper_registry = registry()
