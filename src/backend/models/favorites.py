from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.database import Base

if TYPE_CHECKING:
    from .user import User
    from .property import Property

class Favorite(Base):
    __tablename__ = "favorites"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.property_id"), primary_key=True)

    user: Mapped["User"] = relationship(back_populates="favorites")
    property: Mapped["Property"] = relationship(back_populates="favorites")