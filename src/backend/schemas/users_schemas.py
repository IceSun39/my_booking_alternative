from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated, List, Optional
from src.backend.models.users import Role


class UserBase(BaseModel):
    email: Annotated[str, Field(min_length=1)]
    username: Annotated[str, Field(min_length=1)]
    phone_number: Annotated[str, Field(min_length=1)]


class UserCreate(UserBase):
    password: Annotated[str, Field(min_length=1)]


class UserUpdate(UserBase):
    email: Annotated[Optional[str], Field(min_length=1)] = None
    username: Annotated[Optional[str], Field(min_length=1)] = None
    phone_number: Annotated[Optional[str], Field(min_length=1)] = None
    password: Annotated[Optional[str], Field(min_length=1)] = None


class UserResponse(UserBase):
    user_id: int
    role: Role


class UserInDB(UserBase):
    password: Annotated[str, Field(min_length=1)]


class UserFullResponse(UserResponse):
    properties: List["PropertyResponse"] = []
    bookings: List["BookingResponse"] = []
    favorites: List["FavoriteResponse"] = []
    reviews: List["ReviewResponse"] = []
