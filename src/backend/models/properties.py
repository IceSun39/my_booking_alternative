from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.database import Base
from src.backend.models.associations import property_amenities

if TYPE_CHECKING:
    from .amenities import Amenity
    from .favorites import Favorite
    from .reviews import Review
    from .rooms import Room
    from .users import User


class Property(Base):
    __tablename__ = "properties"

    property_id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    name: Mapped[str] = mapped_column(String)
    country: Mapped[str] = mapped_column(String)
    city: Mapped[str] = mapped_column(String)
    street: Mapped[str] = mapped_column(String)
    house_number: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String, nullable=True)
    rating: Mapped[float] = mapped_column(
        Float,
        CheckConstraint(
            "rating >= 0 AND rating <= 10", name="check_rating_range_properties"
        ),
        default=0.0,
    )
    reviews_count: Mapped[int] = mapped_column(Integer, default=0)

    owner: Mapped[User] = relationship(back_populates="properties")
    rooms: Mapped[list[Room]] = relationship(back_populates="property")
    favorites: Mapped[list[Favorite]] = relationship(back_populates="property")
    reviews: Mapped[list[Review]] = relationship(back_populates="property")
    amenities: Mapped[list[Amenity]] = relationship(
        "Amenity", secondary=property_amenities, back_populates="properties"
    )
