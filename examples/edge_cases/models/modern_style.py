from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base

class ModernModel(Base):
    __tablename__ = "modern_models"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
