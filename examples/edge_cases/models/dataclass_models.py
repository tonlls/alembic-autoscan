from sqlalchemy.orm import Mapped, MappedAsDataclass, mapped_column

from ..database import Base


class UserDataclass(MappedAsDataclass, Base):
    __tablename__ = "user_dataclasses"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    name: Mapped[str] = mapped_column()
