from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated, Optional, List
from src.backend.schemas.amenities_schemas import AmenityResponse


class RoomBase(BaseModel):
    name: Annotated[str, Field(min_length=1)]
    price: Annotated[float, Field(gt=0)]
    capacity: Annotated[int, Field(gt=0)]
    is_contains_several_groups: bool = Field(default=False)


class RoomCreate(RoomBase):
    property_id: int
    amenities: List[AmenityResponse] = Field(default_factory=list)


class RoomUpdate(BaseModel):
    room_id: int
    name: Annotated[Optional[str], Field(min_length=1)] = None
    price: Annotated[Optional[float], Field(gt=0)] = None
    capacity: Annotated[Optional[int], Field(gt=0)] = None
    amenities: Annotated[Optional[AmenityResponse], Field()] = None


class RoomResponse(RoomBase):
    model_config = ConfigDict(from_attributes=True)

    room_id: int
    property_id: int
    amenities: List[AmenityResponse] = Field(default_factory=list)
