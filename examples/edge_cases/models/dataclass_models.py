from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, MappedAsDataclass
from ..database import Base

class UserDataclass(MappedAsDataclass, Base):
    __tablename__ = "user_dataclasses"
    
    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    name: Mapped[str] = mapped_column()
