from sqlalchemy import Column, Integer, String
from ..database import SecondBase

class OtherBaseModel(SecondBase):
    __tablename__ = "other_base_models"
    id = Column(Integer, primary_key=True)
    description = Column(String)
