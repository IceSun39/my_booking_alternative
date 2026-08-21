from pwdlib.hashers import bcrypt
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from sqlalchemy.orm import selectinload

from src.backend.models.users import User
from src.backend.schemas.users_schemas import UserCreate, UserInDB, UserUpdate, UserFullResponse, UserResponse
from src.core.security import get_password_hash


class UserService:
    async def _get_user_in_db(self, session: AsyncSession, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def get_user(self, session: AsyncSession, user_id: int) -> UserResponse:
        user = await self._get_user_in_db(session=session, user_id=user_id)
        return UserResponse.model_validate(user)

    async def create_user(selfself, session: AsyncSession, user_create: UserCreate) -> UserResponse:
        existing_user = await self._get_user_in_db(session=session, user_id=user_create.user_id)
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")

        hashed_password = get_password_hash(user_create.password)

        user_data = user_create.model_dump(exclude={"password"})

        new_user = User(
            **user_data,
            password=hashed_password,
        )

        session.add(new_user)
        await session.commit()
        await session.refresh()
        return UserResponse.model_validate(new_user)

    async def update_user(self, session: AsyncSession, user_update: UserUpdate) -> UserResponse:
        user = await self._get_user_in_db(session=session, user_id=user_update.user_id)

        update_data = user_update.model_dump(exclude_unset=True)

        if "password" in update_data:
            raw_password = update_data.pop("password")
            hashed_password = get_password_hash(raw_password)

        for key, value in update_data.items():
            setattr(user, key, value)

        await session.commit()
        await session.refresh()
        return UserResponse.model_validate(user)

    async def delete_user(self, session: AsyncSession, user_id: int) -> None:
        existing_user = await self._get_user_in_db(session=session, user_id=user_id)

        await session.delete(existing_user)
        await session.commit()

        return None

    async def get_user_by_email(self, session: AsyncSession, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)

        return result.scalar_one_or_none()