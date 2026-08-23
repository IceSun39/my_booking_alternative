from typing import List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.database import Base
from src.backend.models.associations import property_amenities

if TYPE_CHECKING:
    from .users import User
    from .rooms import Room
    from .favorites import Favorite
    from .reviews import Review
    from .amenities import Amenity


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
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    reviews_count: Mapped[int] = mapped_column(Integer, default=0)

    owner: Mapped["User"] = relationship(back_populates="properties")
    rooms: Mapped[List["Room"]] = relationship(back_populates="property")
    favorites: Mapped[List["Favorite"]] = relationship(back_populates="property")
    reviews: Mapped[List["Review"]] = relationship(back_populates="property")
    amenities: Mapped[List["Amenity"]] = relationship("Amenity",secondary=property_amenities,back_populates="properties")
