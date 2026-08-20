from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated, List, Optional


class RoomBase(BaseModel):
    name: Annotated(str, Field(min_length=1))
    price: Annotated(float, Field(default=0.0))
    capacity: Annotated(int, Field(default=1))


class RoomCreate(RoomBase):
    pass


class RoomUpdate(RoomBase):
    name: Annotated(Optional[str], Field(min_length=1)) = None
    price: Annotated(Optional[float], Field()) = 0.0
    capacity: Annotated(Optional[int], Field()) = 1
    property: Annotated(Optional["PropertyUpdate"], Field())
    bookings: Annotated(List["BookingUpdate"], Field())


class RoomResponse(RoomBase):
    room_id: int
    property_id: int


class RoomInDB(RoomBase):
    pass

