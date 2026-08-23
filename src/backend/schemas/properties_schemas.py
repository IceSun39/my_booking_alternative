from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated, Optional


class PropertiesBase(BaseModel):
    name: Annotated[str, Field(min_length=1)]
    country: Annotated[str, Field(min_length=1)]
    city: Annotated[str, Field(min_length=1)]
    street: Annotated[str, Field(min_length=1)]
    house_number: Annotated[str, Field(min_length=1)]
    description: Annotated[str, Field(min_length=1)]

class PropertiesCreate(PropertiesBase):
    owner_id: int

class PropertiesUpdate(BaseModel):
    name: Annotated[Optional[str], Field(min_length=1)] = None
    country: Annotated[Optional[str], Field(min_length=1)] = None
    city: Annotated[Optional[str], Field(min_length=1)] = None
    street: Annotated[Optional[str], Field(min_length=1)] = None
    house_number: Annotated[Optional[str], Field(min_length=1)] = None
    description: Annotated[Optional[str], Field(min_length=1)] = None

class PropertiesResponse(PropertiesBase):
    model_config = ConfigDict(from_attributes=True)
    owner_id: int
    property_id: int
    rating: float
    reviews_count: int
