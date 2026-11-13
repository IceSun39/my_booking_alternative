from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class ReviewBase(BaseModel):
    comment: Annotated[str | None, Field(default=None)] = None
    rating: Annotated[int, Field(ge=1, le=10)]


class ReviewCreate(ReviewBase):
    booking_id: int


class ReviewUpdate(BaseModel):
    rating: Annotated[int | None, Field(ge=1, le=10)] = None
    comment: Annotated[str | None, Field()] = None


class ReviewResponse(ReviewBase):
    model_config = ConfigDict(from_attributes=True)

    review_id: int
    user_id: int
    property_id: int
    booking_id: int
    created_at: datetime
