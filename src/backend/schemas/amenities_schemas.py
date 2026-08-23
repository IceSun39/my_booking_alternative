from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated, Optional, List

from src.backend.models.amenities import AmenityType

class AmenityBase(BaseModel):
    name: Annotated[str, Field(min_length=1)]
    description: Annotated[Optional[str], Field(min_length=1)] = None
    type: AmenityType = AmenityType.BOTH

class AmenityCreate(AmenityBase):
    pass


class AmenityUpdate(AmenityBase):
    name: Annotated[Optional[str], Field(min_length=1)] = None
    description: Annotated[Optional[str], Field(min_length=1)] = None
    type: Optional[AmenityType] = None

class AmenityResponse(AmenityBase):
    model_config = ConfigDict(from_attributes=True)

    amenity_id: int

class AmenityAssign(BaseModel):
    amenity_ids: List[int] = []
