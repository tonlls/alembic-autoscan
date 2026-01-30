from sqlalchemy.orm import as_declarative, declared_attr
from sqlalchemy import Column, Integer

@as_declarative()
class DecoratorBase:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
    
    id = Column(Integer, primary_key=True)

class DecoratorModel(DecoratorBase):
    pass
