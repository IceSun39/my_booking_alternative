from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated, List, Optional

class ReviewBase(BaseModel):
    comment: Annotated[Optional[str], Field(default=None)] = None
    rating: Annotated[int, Fielld(ge=1, le=10)]

class ReviewCreate(ReviewBase):
    booking_id: int

class ReviewUpdate(ReviewBase):
    rating: Annotated[Optional[int], Field(ge=1, le=10, default=None)]
    comment: Annotated[Optional[str], Field(default=None)] = None

class ReviewResponse(ReviewBase):
    model_config = ConfigDict(from_attributes=True)

    review_id: int
    user_id: int
    property_id: int
    booking_id: int
    created_at: datetime
