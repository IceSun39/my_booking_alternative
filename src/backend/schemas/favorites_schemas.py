from pydantic import BaseModel, ConfigDict
from typing import Optional


class FavoriteCreate(BaseModel):
    property_id: int
    room_id: Optional[int] = None


class FavoriteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    property_id: int
