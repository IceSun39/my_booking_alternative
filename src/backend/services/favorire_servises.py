from backend.models import Review
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from sqlalchemy.orm import selectinload

from src.backend.models.favorites import Favorite
from src.backend.schemas.favorites_schemas import FavoriteCreate, FavoriteResponse

class FavoriteService:
    async def _get_favorite_in_db(self, session: AsyncSession, property_id: int, user_id, room_id:int) -> Optional[Favorite]:
        stmt = select(Favorite).where(Favorite.user_id == user_id and Favorite.property_id == property_id and Favorite.room_id == room_id)
        result = await session.execute(stmt)
        favorite = result.scalar_one_or_none()
        return favorite

    async def get_users_favorites(self,session: AsyncSession, user_id: int) -> Optional[List[Favorite]]:
        stmt = selevt(Favorite).where(Favorite.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def create_favorite(self,session: AsyncSession, user_id: int, favorite_create: FavoriteCreate) -> dict:
        favorite = self._get_favorite_in_db(session, user_id, favorite_create.property_id, favorite_create.room_id)
        if favorite:
            return {"Message": "Favorite already exists", "status": 200}

        favorite = Favorite(user_id=user_id, property_id=favorite_create.property_id)
        session.add(favorite)
        await session.commit()
        await session.refresh(favorite)
        return {"Message": "Favorite created", "status": 200}

    async def delete_favorite(self,session: AsyncSession, user_id: int, favorite_id: int) -> dict:
        favorite = await self._get_favorite_in_db(session, user_id, favorite_id)
        if favorite is None:
            return {"Message": "Favorite does not exist", "status": 200}

        await session.delete(favorite)
        await session.commit()
        return {"Message": "Favorite deleted", "status": 200}

