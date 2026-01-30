import enum
from sqlalchemy import Column, Integer, Enum, String
from ..database import Base

class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class TypedModel(Base):
    __tablename__ = "typed_models"
    
    id = Column(Integer, primary_key=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER)
    custom_data = Column(String)
