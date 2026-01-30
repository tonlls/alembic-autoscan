from sqlalchemy import Column, Integer, String, ForeignKey
from ..database import Base

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    type = Column(String(50))

    __mapper_args__ = {
        "polymorphic_identity": "employee",
        "polymorphic_on": type,
    }

class Engineer(Employee):
    __tablename__ = "engineers"
    id = Column(Integer, ForeignKey("employees.id"), primary_key=True)
    engineer_info = Column(String(50))

    __mapper_args__ = {
        "polymorphic_identity": "engineer",
    }
