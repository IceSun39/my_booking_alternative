from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated, List, Optional


class PropertiesBase(BaseModel):
    name: Annotated[str, Field(min_length=1)]
    address: Annotated[str, Field(min_length=1)]
    description: Annotated[str, Field(min_length=1)]


class PropertiesCreate(PropertiesBase):
    owner_id: int


class PropertiesUpdate(PropertiesBase):
    name: Annotated[Optional[str], Field(min_length=1)]
    address: Annotated[Optional[str], Field(min_length=1)]
    description: Annotated[Optional[str], Field(min_length=1)]


class PropertiesResponse(PropertiesBase):
    model_config = ConfigDict(from_attributes=True)

    owner_id: int
    property_id: int
