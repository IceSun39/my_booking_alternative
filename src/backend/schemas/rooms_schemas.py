from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from src.backend.models.rooms import RoomType
from src.backend.schemas.amenities_schemas import AmenityResponse


class RoomBase(BaseModel):
    name: Annotated[str, Field(min_length=1)]
    price: Annotated[float, Field(gt=0)]
    capacity: Annotated[int, Field(gt=0)]
    room_type: Annotated[RoomType, Field(default=RoomType.PRIVATE)]


class RoomCreate(RoomBase):
    property_id: int
    amenities: list[AmenityResponse] = Field(default_factory=list)


class RoomUpdate(BaseModel):
    room_id: int
    name: Annotated[str | None, Field(min_length=1)] = None
    price: Annotated[float | None, Field(gt=0)] = None
    capacity: Annotated[int | None, Field(gt=0)] = None
    amenities: Annotated[AmenityResponse | None, Field()] = None


class RoomResponse(RoomBase):
    model_config = ConfigDict(from_attributes=True)

    room_id: int
    property_id: int
    amenities: list[AmenityResponse] = Field(default_factory=list)
