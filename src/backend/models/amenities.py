from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.backend.database.database import Base
from src.backend.models.associations import property_amenities, room_amenities
import enum

class AmenityType(enum.Enum):
    PROPERTY = "property"
    ROOM = "room"
    BOTH = "both"

class Amenity(Base):
    __tablename__ = "amenities"

    amenity_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    type: Mapped[AmenityType] = mapped_column(Enum(AmenityType), nullable=False)

    rooms = relationship("Room", secondary=room_amenities, back_populates="amenities")
    properties = relationship("Property", secondary=property_amenities, back_populates="amenities")
