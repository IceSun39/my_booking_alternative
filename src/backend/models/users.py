import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.database import Base

if TYPE_CHECKING:
    from .bookings import Booking
    from .favorites import Favorite
    from .properties import Property
    from .reviews import Review


class Role(enum.Enum):
    ADMIN = 1
    USER = 2
    OWNER = 3


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    password: Mapped[str] = mapped_column(String)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    phone_number: Mapped[str] = mapped_column(String, nullable=True)
    role: Mapped[Role] = mapped_column(Enum(Role))

    properties: Mapped[list[Property]] = relationship(back_populates="owner")
    bookings: Mapped[list[Booking]] = relationship(back_populates="user")
    favorites: Mapped[list[Favorite]] = relationship(back_populates="user")
    reviews: Mapped[list[Review]] = relationship(back_populates="user")

    @property
    def is_admin(self) -> bool:
        return self.role == Role.ADMIN
