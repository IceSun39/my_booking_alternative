from pydantic import BaseModel, Field
from typing import Annotated, List, Optional
from datetime import date
import enum


class SortBy(enum.Enum):
    PRICE_DESC = "price_desc"
    PRICE_ASC = "price_asc"
    REVIEW_DESC = "review_desc"
    REVIEW_ASC = "review_asc"


class SearchFilter(BaseModel):
    check_in: Annotated[date, Field(..., description="Date of check_in")]
    check_out: Annotated[date, Field(..., description="Check out date")]
    city: Annotated[str, Field(..., description="City")]
    guest: Annotated[str, Field(..., description="Number of guests")]

    min_price: Optional[Annotated[float, Field(..., description="Minimum price")]]
    max_price: Optional[Annotated[float, Field(..., description="Maximum price")]]
    amenities: Optional[Annotated[List[int], Field(..., description="Amenities")]]
    sort_by: Optional[Annotated[SortBy, Field(..., description="Sort by")]]
