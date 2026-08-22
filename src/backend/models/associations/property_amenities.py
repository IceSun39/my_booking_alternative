from sqlalchemy import Column, Integer, Table, ForeignKey
from src.backend.database.database import Base

property_amenities = Table(
    "property_amenities",
    Base.metadata,
    Column("property_id", Integer, ForeignKey("properties.property_id", ondelete="CASCADE"), primary_key=True),
    Column("amenity_id", Integer, ForeignKey("amenities.amenity_id", ondelete="CASCADE"), primary_key=True),
)