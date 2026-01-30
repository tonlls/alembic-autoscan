from sqlalchemy import Column, Integer
from ..database import Base

class InitModel(Base):
    __tablename__ = "init_models"
    id = Column(Integer, primary_key=True)
