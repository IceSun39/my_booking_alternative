from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from src.backend.models.amenities import AmenityType


class AmenityBase(BaseModel):
    name: Annotated[str, Field(min_length=1)]
    description: Annotated[str | None, Field(min_length=1)] = None
    type: AmenityType = AmenityType.BOTH


class AmenityCreate(AmenityBase):
    pass


class AmenityUpdate(AmenityBase):
    name: Annotated[str | None, Field(min_length=1)] = None
    description: Annotated[str | None, Field(min_length=1)] = None
    type: AmenityType | None = None


class AmenityResponse(AmenityBase):
    model_config = ConfigDict(from_attributes=True)

    amenity_id: int


class AmenityAssign(BaseModel):
    amenity_ids: list[int] = []
