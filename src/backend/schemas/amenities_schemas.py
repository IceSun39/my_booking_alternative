from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated, Optional


class AmenityBase(BaseModel):
    name: Annotated[str, Field(min_length=1)]
    description: Annotated[Optional[str], Field(min_length=1)] = None


class AmenityCreate(AmenityBase):
    pass


class AmenityUpdate(AmenityBase):
    name: Annotated[Optional[str], Field(min_length=1)] = None
    description: Annotated[Optional[str], Field(min_length=1)] = None


class AmenityResponse(AmenityBase):
    model_config = ConfigDict(from_attributes=True)

    amenity_id: int
