from decimal import Decimal
import enum

from typing import List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Integer, Boolean, Numeric, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.database import Base
from src.backend.models.associations.room_amenities import room_amenities

if TYPE_CHECKING:
    from .properties import Property
    from .bookings import Booking
    from .favorites import Favorite
    from .amenities import Amenity


class RoomType(enum.Enum):
    PRIVATE = "private"
    SHARED = 'shared'

class Room(Base):
    __tablename__ = "rooms"

    room_id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.property_id"))

    name: Mapped[str] = mapped_column(String)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    capacity: Mapped[int] = mapped_column(Integer)
    is_shared: Mapped[RoomType] = mapped_column(Enum(RoomType, default=RoomType.PRIVATE))

    property: Mapped["Property"] = relationship(back_populates="rooms")
    bookings: Mapped[List["Booking"]] = relationship(back_populates="room")
    favorites: Mapped[List["Favorite"]] = relationship(back_populates="room")
    amenities: Mapped[List["Amenity"]] = relationship(secondary=room_amenities, back_populates="rooms")
