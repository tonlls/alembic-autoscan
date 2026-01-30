from sqlalchemy import Table, Column, Integer, String
from ..database import mapper_registry

class UserImperative:
    pass

user_table = Table(
    "user_imperative",
    mapper_registry.metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(50)),
)

mapper_registry.map_imperatively(UserImperative, user_table)
