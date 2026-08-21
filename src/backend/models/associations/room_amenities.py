from sqlalchemy import Column, Integer, Table, ForeignKey
from src.backend.database.database import Base

room_amenities = Table(
    "room_amenities",
    Base.metadata,
    Column("room_id", Integer, ForeignKey("rooms.room_id", ondelete="CASCADE"), primary_key=True),
    Column("amenity_id", Integer, ForeignKey("amenities.amenity_id", ondelete="CASCADE"), primary_key=True),
)