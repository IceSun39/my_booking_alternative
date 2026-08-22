from datetime import date
from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated, Optional
from src.backend.models.bookings import BookingStatus


class BookingBase(BaseModel):
    check_in: date
    check_out: date
    guests: Annotated[int, Field(gt=0)]


class BookingCreate(BookingBase):
    room_id: int


class BookingUpdate(BaseModel):
    check_in: Annotated[Optional[date], Field()] = None
    check_out: Annotated[Optional[date], Field()] = None
    guests: Annotated[Optional[int], Field(gt=0)] = None
    room_id: Annotated[Optional[int], Field(gt=0)] = None
    status: Annotated[Optional[BookingStatus], Field()] = None


class BookingResponse(BookingBase):
    model_config = ConfigDict(from_attributes=True)

    booking_id: int
    user_id: int
    room_id: int
    total_price: int
    status: BookingStatus
