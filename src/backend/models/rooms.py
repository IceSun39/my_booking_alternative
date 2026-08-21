from typing import List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Float, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.database import Base

if TYPE_CHECKING:
    from .properties import Property
    from .bookings import Booking
    from .favorites import Favorite


class Room(Base):
    __tablename__ = "rooms"

    room_id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.property_id"))

    name: Mapped[str] = mapped_column(String)
    price: Mapped[float] = mapped_column(Float)
    capacity: Mapped[int] = mapped_column(Integer)
    is_contains_several_groups: Mapped[bool] = mapped_column(Boolean)

    property: Mapped["Property"] = relationship(back_populates="rooms")
    bookings: Mapped[List["Booking"]] = relationship(back_populates="room")
    favorites: Mapped[List["Favorite"]] = relationship(back_populates="room")
