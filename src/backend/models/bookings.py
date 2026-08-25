from decimal import Decimal
from typing import TYPE_CHECKING
from datetime import date
from sqlalchemy import ForeignKey, Integer, Date, Enum, Numeric, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ExcludeConstraint
import enum

from src.backend.database import Base
from src.backend.models.rooms import RoomType

if TYPE_CHECKING:
    from .users import User
    from .rooms import Room
    from .reviews import Review


class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Booking(Base):
    __tablename__ = "bookings"

    booking_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.room_id"))

    check_in: Mapped[date] = mapped_column(Date)
    check_out: Mapped[date] = mapped_column(Date)
    guests: Mapped[int] = mapped_column(Integer)

    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus), default=BookingStatus.PENDING)
    room_type: Mapped[RoomType] = mapped_column(
        Enum(RoomType),
        nullable=False,
        default=RoomType.PRIVATE,
    )

    __table_args__ = (
        ExcludeConstraint(
            (
                text(
                    """
                    CASE
                        WHEN room_type = 'PRIVATE'
                             AND status IN ('PENDING', 'CONFIRMED')
                        THEN room_id
                        ELSE NULL
                    END
                    """
                ),
                "=",
            ),
            (
                text("daterange(check_in, check_out)"),
                "&&",
            ),
            name="exclude_overlapping_private_bookings",
        ),
    )

    user: Mapped["User"] = relationship(back_populates="bookings")
    room: Mapped["Room"] = relationship(back_populates="bookings")

    review: Mapped["Review"] = relationship(back_populates="booking")
