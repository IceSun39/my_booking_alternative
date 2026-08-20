from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import ForeignKey, Integer, Text, CheckConstraint, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.database import Base

if TYPE_CHECKING:
    from .user import User
    from .property import Property
    from .booking import Booking


class Review(Base):
    __tablename__ = "reviews"

    review_id: Mapped[int] = mapped_column(primary_key=True)
    rating: Mapped[int] = mapped_column(Integer, CheckConstraint("rating >= 1 AND rating <= 10"))
    comment: Mapped[str | None] = mapped_column(Text)  # Може бути порожнім (NULL)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.property_id"))

    # unique=True гарантує, що до одного бронювання буде лише один відгук
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.booking_id"), unique=True)

    # Зв'язки
    user: Mapped["User"] = relationship(back_populates="reviews")
    property: Mapped["Property"] = relationship(back_populates="reviews")
    booking: Mapped["Booking"] = relationship(back_populates="review")