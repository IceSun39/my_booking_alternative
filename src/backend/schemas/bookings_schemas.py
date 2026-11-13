from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from src.backend.models.bookings import BookingStatus


class BookingBase(BaseModel):
    check_in: date
    check_out: date
    guests: Annotated[int, Field(gt=0)]


class BookingCreate(BookingBase):
    room_id: int


class BookingUpdate(BaseModel):
    check_in: Annotated[date | None, Field()] = None
    check_out: Annotated[date | None, Field()] = None
    guests: Annotated[int | None, Field(gt=0)] = None
    room_id: Annotated[int | None, Field(gt=0)] = None
    status: Annotated[BookingStatus | None, Field()] = None


class BookingResponse(BookingBase):
    model_config = ConfigDict(from_attributes=True)

    booking_id: int
    user_id: int
    room_id: int
    total_price: int
    status: BookingStatus
