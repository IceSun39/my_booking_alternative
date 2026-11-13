from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, ConfigDict, Field

from src.backend.models.users import Role

if TYPE_CHECKING:
    from src.backend.schemas.bookings_schemas import BookingResponse
    from src.backend.schemas.favorites_schemas import FavoriteResponse
    from src.backend.schemas.properties_schemas import PropertiesResponse
    from src.backend.schemas.reviews_schemas import ReviewResponse


class UserBase(BaseModel):
    email: Annotated[str, Field(min_length=1)]
    username: Annotated[str, Field(min_length=1)]
    phone_number: Annotated[str, Field(min_length=1)]


class UserCreate(UserBase):
    password: Annotated[str, Field(min_length=1)]
    role: Annotated[Role, Field(default=Role.USER)]


class UserRegister(UserBase):
    password: Annotated[str, Field(min_length=1)]


class UserUpdate(BaseModel):
    email: Annotated[str | None, Field(min_length=1)] = None
    username: Annotated[str | None, Field(min_length=1)] = None
    phone_number: Annotated[str | None, Field(min_length=1)] = None
    password: Annotated[str | None, Field(min_length=1)] = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    role: Role


class UserInDB(UserBase):
    password: Annotated[str, Field(min_length=1)]


class UserFullResponse(UserResponse):
    properties: list[PropertiesResponse] = []
    bookings: list[BookingResponse] = []
    favorites: list[FavoriteResponse] = []
    reviews: list[ReviewResponse] = []
