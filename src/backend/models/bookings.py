from typing import TYPE_CHECKING
from datetime import date
from sqlalchemy import ForeignKey, Integer, Float, Date, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from src.backend.database import Base

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

    total_price: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(Enum(BookingStatus))

    user: Mapped["User"] = relationship(back_populates="bookings")
    room: Mapped["Room"] = relationship(back_populates="bookings")

    review: Mapped["Review"] = relationship(back_populates="booking")
