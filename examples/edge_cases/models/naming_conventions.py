from sqlalchemy import Column, Integer, String, MetaData
from sqlalchemy.orm import DeclarativeBase

# Custom naming convention
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=naming_convention)

class BaseWithConvention(DeclarativeBase):
    metadata = metadata

class ConventionModel(BaseWithConvention):
    __tablename__ = "convention_models"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
