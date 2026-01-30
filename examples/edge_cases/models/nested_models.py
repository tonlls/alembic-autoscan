from sqlalchemy import Column, Integer, String
from ..database import Base

class Outer:
    class InnerModel(Base):
        __tablename__ = "inner_models"
        id = Column(Integer, primary_key=True)
        data = Column(String)
