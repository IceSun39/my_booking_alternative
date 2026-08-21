from typing import List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.database import Base

if TYPE_CHECKING:
    from .users import User
    from .rooms import Room
    from .favorites import Favorite
    from .reviews import Review


class Property(Base):
    __tablename__ = "properties"

    property_id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    name: Mapped[str] = mapped_column(String)
    address: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)

    owner: Mapped["User"] = relationship(back_populates="properties")
    rooms: Mapped[List["Room"]] = relationship(back_populates="property")
    favorites: Mapped[List["Favorite"]] = relationship(back_populates="property")
    reviews: Mapped[List["Review"]] = relationship(back_populates="property")
