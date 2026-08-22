from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from typing import Optional, List

from src.backend.models.favorites import Favorite
from src.backend.schemas.favorites_schemas import FavoriteCreate


class FavoriteService:
    async def _get_favorite_in_db(self, session: AsyncSession, user_id: int, property_id: int) -> Optional[Favorite]:
        stmt = select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.property_id == property_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_users_favorites(self, session: AsyncSession, user_id: int) -> List[Favorite]:
        stmt = select(Favorite).where(Favorite.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def create_favorite(self, session: AsyncSession, user_id: int, favorite_create: FavoriteCreate) -> Favorite:
        existing_favorite = await self._get_favorite_in_db(session, user_id, favorite_create.property_id)

        if existing_favorite:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already in favorites")

        new_favorite = Favorite(
            user_id=user_id,
            property_id=favorite_create.property_id,
            room_id=favorite_create.room_id
        )
        session.add(new_favorite)
        await session.commit()
        await session.refresh(new_favorite)
        return new_favorite

    async def delete_favorite(self, session: AsyncSession, user_id: int, property_id: int) -> None:
        favorite = await self._get_favorite_in_db(session, user_id, property_id)
        if not favorite:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Favorite not found")

        await session.delete(favorite)
        await session.commit()