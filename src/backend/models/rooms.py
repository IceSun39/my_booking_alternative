import enum
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.database import Base
from src.backend.models.associations.room_amenities import room_amenities

if TYPE_CHECKING:
    from .amenities import Amenity
    from .bookings import Booking
    from .favorites import Favorite
    from .properties import Property


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
    room_type: Mapped[RoomType] = mapped_column(
        Enum(RoomType),
        nullable=False,
        default=RoomType.PRIVATE,
    )

    property: Mapped[Property] = relationship(back_populates="rooms")
    bookings: Mapped[list[Booking]] = relationship(back_populates="room")
    favorites: Mapped[list[Favorite]] = relationship(back_populates="room")
    amenities: Mapped[list[Amenity]] = relationship(secondary=room_amenities, back_populates="rooms")
