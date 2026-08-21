from sqlalchemy import Integer, String, Table, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.backend.database.database import Base
from src.backend.models.associations.room_amenities import room_amenities

class Amenity(Base):
    __tablename__ = "amenities"

    amenity_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String,nullable=True)

    rooms = relationship("Room", secondary=room_amenities, back_populates="amenities")