from pydantic import BaseModel, ConfigDict


class FavoriteCreate(BaseModel):
    property_id: int
    room_id: int


class FavoriteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    property_id: int
    room_id: int
