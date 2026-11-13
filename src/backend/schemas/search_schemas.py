import enum
from datetime import date
from typing import Annotated

from pydantic import BaseModel, Field


class SortBy(enum.Enum):
    PRICE_DESC = "price_desc"
    PRICE_ASC = "price_asc"
    REVIEW_DESC = "review_desc"
    REVIEW_ASC = "review_asc"


class SearchFilter(BaseModel):
    check_in: Annotated[date, Field(..., description="Date of check_in")]
    check_out: Annotated[date, Field(..., description="Check out date")]
    city: Annotated[str, Field(..., description="City")]
    guest: Annotated[int, Field(..., gt=0, description="Number of guests")]

    min_price: Annotated[float | None, Field(default=None)] = None
    max_price: Annotated[float | None, Field(default=None)] = None
    amenities: Annotated[list[int] | None, Field(default=None)] = None
    sort_by: Annotated[SortBy | None, Field(default=None)] = None