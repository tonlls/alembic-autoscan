from sqlalchemy import Column, Integer, String
from ..database import Base

class TimestampMixin:
    """A mixin that is NOT a model itself but defines columns."""
    created_at = Column(Integer)

class AbstractBase(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)

class ConcreteModel(AbstractBase, TimestampMixin):
    __tablename__ = "concrete_models"
    name = Column(String)
