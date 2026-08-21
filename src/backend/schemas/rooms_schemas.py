from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated, Optional


class RoomBase(BaseModel):
    name: Annotated[str, Field(min_length=1)]
    price: Annotated[float, Field(gt=0)]
    capacity: Annotated[int, Field(gt=0)]


class RoomCreate(RoomBase):
    property_id: int


class RoomUpdate(BaseModel):
    room_id: int
    name: Annotated[Optional[str], Field(min_length=1)] = None
    price: Annotated[Optional[float], Field(gt=0)] = None
    capacity: Annotated[Optional[int], Field(gt=0)] = None


class RoomResponse(RoomBase):
    model_config = ConfigDict(from_attributes=True)

    room_id: int
    property_id: int
